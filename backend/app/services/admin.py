"""Admin views: reports, roles, access log and funnel metrics (US-010, US-022)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.api.errors import not_found
from app.api.schemas.admin import (
    AccessLogEntry,
    AdminUser,
    AiHealth,
    FunnelUnit,
    Metrics,
    Report,
)
from app.db.models import (
    Attendance,
    ConnectionRequestRow,
    ConnectionRow,
    DiscoveryConsent,
    Event,
    FollowUpReportRow,
    ModelTrace,
    Profile,
    Registration,
    ReportRow,
    StaffAccessLog,
    User,
)
from app.domain.vocab import Role
from app.services import people, policy
from app.settings import get_settings


def roles_of(db: Session, user: User) -> list[Role]:
    roles = [Role.participant]
    if user.is_organiser:
        roles.append(Role.organiser)
    if policy.facilitated_circle_ids(db, user.id):
        roles.append(Role.facilitator)
    if user.is_admin:
        roles.append(Role.admin)
    return roles


def list_reports(db: Session) -> list[Report]:
    rows = db.scalars(select(ReportRow).order_by(ReportRow.created_at.desc())).all()
    names = people.refs(db, {r.reporter_id for r in rows} | {r.subject_id for r in rows})
    return [
        Report(
            id=r.id,
            reporter=names[r.reporter_id],
            subject=names[r.subject_id],
            reason=r.reason,
            created_at=r.created_at,
        )
        for r in rows
    ]


def _admin_user(db: Session, user: User, profile: Profile) -> AdminUser:
    return AdminUser(
        id=user.id, display_name=user.display_name, stage=profile.stage, roles=roles_of(db, user)
    )


def list_users(db: Session) -> list[AdminUser]:
    rows = db.execute(
        select(User, Profile).join(Profile, Profile.user_id == User.id).order_by(User.display_name)
    ).all()
    return [_admin_user(db, u, p) for u, p in rows]


def set_organiser(db: Session, user_id: UUID, organiser: bool) -> AdminUser:
    user, profile = db.get(User, user_id), db.get(Profile, user_id)
    if user is None or profile is None:
        raise not_found()
    user.is_organiser = organiser
    db.flush()
    return _admin_user(db, user, profile)


def access_log(db: Session) -> list[AccessLogEntry]:
    rows = list(
        db.scalars(select(StaffAccessLog).order_by(StaffAccessLog.viewed_at.desc()).limit(500))
    )
    names = people.refs(db, {r.viewer_id for r in rows} | {r.subject_id for r in rows})
    return [
        AccessLogEntry(
            id=r.id,
            viewer=names[r.viewer_id],
            viewer_role=r.viewer_role,
            subject=names[r.subject_id],
            fields=r.fields,
            circle_id=r.circle_id,
            viewed_at=r.viewed_at,
        )
        for r in rows
    ]


def _count(db: Session, stmt: object) -> int:
    return int(db.scalar(stmt) or 0)  # type: ignore[call-overload]


def funnel(db: Session) -> list[FunnelUnit]:
    """Separate units, each with its own denominator; no combined rate (MD-016, MP-005).

    Counted with plain SQL, never by a model (W20).
    """
    ended = select(Event.id).where(Event.state == "approved", Event.ends_at <= policy.now())
    participants = _count(db, select(func.count()).select_from(User))
    registered = _count(db, select(func.count()).where(Registration.event_id.in_(ended)))
    opportunities = _count(
        db,
        select(func.count()).where(
            Attendance.event_id.in_(ended), Attendance.status == "confirmed"
        ),
    )
    event_opt_ins = _count(
        db,
        select(func.count())
        .select_from(DiscoveryConsent)
        .join(
            Attendance,
            (Attendance.event_id == DiscoveryConsent.event_id)
            & (Attendance.user_id == DiscoveryConsent.user_id),
        )
        .where(DiscoveryConsent.event_id.in_(ended), Attendance.status == "confirmed"),
    )
    directory = _count(db, select(func.count()).where(DiscoveryConsent.event_id.is_(None)))
    requests = _count(db, select(func.count()).select_from(ConnectionRequestRow))
    accepted = _count(db, select(func.count()).where(ConnectionRequestRow.status == "accepted"))
    connections = _count(db, select(func.count()).select_from(ConnectionRow))

    def pairs_met(number: int) -> int:
        return _count(
            db,
            select(func.count(distinct(FollowUpReportRow.connection_id))).where(
                FollowUpReportRow.number == number, FollowUpReportRow.met.is_(True)
            ),
        )

    first, second = pairs_met(1), pairs_met(2)
    return [
        FunnelUnit(
            key="opportunities",
            label="Reconnection opportunities (confirmed attendance at ended events)",
            count=opportunities,
            denominator=registered,
            denominator_label="registrations for ended events",
        ),
        FunnelUnit(
            key="event_opt_ins",
            label="Event reconnection opt-ins",
            count=event_opt_ins,
            denominator=opportunities,
            denominator_label="reconnection opportunities",
        ),
        FunnelUnit(
            key="directory_opt_ins",
            label="Directory opt-ins",
            count=directory,
            denominator=participants,
            denominator_label="people",
        ),
        FunnelUnit(
            key="requests",
            label="Connection requests sent",
            count=requests,
            denominator=participants,
            denominator_label="people",
        ),
        FunnelUnit(
            key="acceptances",
            label="Requests accepted",
            count=accepted,
            denominator=requests,
            denominator_label="requests sent",
        ),
        FunnelUnit(
            key="first_catch_ups",
            label="Pairs reporting a first catch-up",
            count=first,
            denominator=connections,
            denominator_label="connected pairs",
            self_reported=True,
        ),
        FunnelUnit(
            key="second_catch_ups",
            label="Pairs reporting a second catch-up",
            count=second,
            denominator=first,
            denominator_label="pairs reporting a first catch-up",
            self_reported=True,
        ),
    ]


def spend_usd(db: Session) -> Decimal:
    return Decimal(db.scalar(select(func.coalesce(func.sum(ModelTrace.cost_usd), 0))) or 0)


def ai_health(db: Session) -> AiHealth:
    """Built from trace metadata only; never touches profile content (SAD Production Shape)."""
    traces = db.scalars(select(ModelTrace)).all()
    attempted = [t for t in traces if t.model_calls > 0]
    total = len(traces)
    latencies = sorted(t.latency_ms for t in attempted)
    shown = sum(len(t.output_ids) for t in traces)
    dropped = sum(len(t.dropped) for t in traces)
    cap = get_settings().ai_spend_cap_usd
    spent = float(spend_usd(db))

    def rate(n: int, d: int) -> float | None:
        return round(n / d, 4) if d else None

    return AiHealth(
        spend_usd=round(spent, 4),
        spend_cap_usd=cap,
        ai_enabled=spent < cap,
        calls=sum(t.model_calls for t in traces),
        fallback_rate=rate(sum(t.outcome == "fallback" for t in traces), total),
        schema_failure_rate=rate(sum(t.schema_failures > 0 for t in attempted), len(attempted)),
        dropped_item_rate=rate(dropped, shown + dropped),
        p95_latency_ms=latencies[max(0, -(-len(latencies) * 95 // 100) - 1)] if latencies else None,
        assistant_accepted=sum(t.review_outcome == "accepted" for t in traces),
        assistant_discarded=sum(t.review_outcome == "discarded" for t in traces),
    )


def metrics(db: Session) -> Metrics:
    return Metrics(funnel=funnel(db), ai=ai_health(db), generated_at=policy.now())
