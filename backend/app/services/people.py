"""Profiles and person cards. The only place profile fields are filtered by visibility (MD-020)."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.api.errors import not_found
from app.api.schemas.common import PersonCard, PersonRef, Relationship
from app.api.schemas.profile import (
    ContactDetails,
    LabelledValue,
    MatchingFieldsView,
    OwnProfile,
    ProfileFields,
    Vocabulary,
)
from app.db.models import ConnectionRequestRow, Profile, ProfileFieldRow, StaffAccessLog, User
from app.domain import vocab
from app.domain.vocab import ProfileField, Visibility
from app.services import policy

LIST_FIELDS = {"looking_for", "interests", "challenges", "time_windows"}
DEFAULT_VISIBILITY = {f.value: Visibility.public.value for f in ProfileField} | {
    "faith_context": Visibility.matching_only.value
}


@dataclass
class ProfileData:
    user: User
    profile: Profile
    values: dict[str, Any] = field(default_factory=dict)
    visibility: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> Any:
        return self.values.get(name, [] if name in LIST_FIELDS else None)

    def visibility_of(self, name: str) -> str:
        return self.visibility.get(name, DEFAULT_VISIBILITY[name])

    def public(self, name: str) -> Any:
        """The value another participant may see: empty when the field is `matching_only`."""
        if self.visibility_of(name) != Visibility.public.value:
            return [] if name in LIST_FIELDS else None
        return self.get(name)

    def matching_only_fields(self) -> dict[str, Any]:
        return {
            n: v
            for n, v in self.values.items()
            if self.visibility_of(n) == Visibility.matching_only.value
        }


def load_profiles(db: Session, ids: Iterable[UUID]) -> dict[UUID, ProfileData]:
    wanted = list(set(ids))
    if not wanted:
        return {}
    rows = db.execute(
        select(User, Profile).join(Profile, Profile.user_id == User.id).where(User.id.in_(wanted))
    ).all()
    out = {u.id: ProfileData(u, p) for u, p in rows}
    for row in db.scalars(select(ProfileFieldRow).where(ProfileFieldRow.user_id.in_(wanted))):
        if row.user_id in out:
            out[row.user_id].values[row.field] = row.value
            out[row.user_id].visibility[row.field] = row.visibility
    return out


def load_profile(db: Session, user_id: UUID) -> ProfileData:
    found = load_profiles(db, [user_id]).get(user_id)
    if found is None:
        raise not_found()
    return found


def refs(db: Session, ids: Iterable[UUID]) -> dict[UUID, PersonRef]:
    wanted = list(set(ids))
    if not wanted:
        return {}
    rows = db.execute(select(User.id, User.display_name).where(User.id.in_(wanted))).all()
    return {i: PersonRef(id=i, display_name=n) for i, n in rows}


def relationships(db: Session, viewer_id: UUID) -> dict[UUID, Relationship]:
    """How the viewer relates to others. A decline shows to its sender as still sent (OQ-06)."""
    out: dict[UUID, Relationship] = {}
    rows = db.scalars(
        select(ConnectionRequestRow).where(
            or_(
                ConnectionRequestRow.sender_id == viewer_id,
                ConnectionRequestRow.recipient_id == viewer_id,
            ),
            ConnectionRequestRow.status.in_(("pending", "declined")),
        )
    ).all()
    for r in rows:
        if r.sender_id == viewer_id and not r.sender_hidden:
            out.setdefault(r.recipient_id, Relationship(status="request_sent", request_id=r.id))
    for r in rows:
        if r.recipient_id == viewer_id and r.status == "pending":
            out[r.sender_id] = Relationship(status="request_received", request_id=r.id)
    for other, cid in policy.connected_ids(db, viewer_id).items():
        out[other] = Relationship(status="connected", connection_id=cid)
    return out


def card(pd: ProfileData, relationship: Relationship | None = None) -> PersonCard:
    return PersonCard(
        id=pd.user.id,
        display_name=pd.user.display_name,
        stage=pd.profile.stage,
        summary=pd.public("summary"),
        looking_for=pd.public("looking_for"),
        interests=pd.public("interests"),
        challenges=pd.public("challenges"),
        industry=pd.public("industry"),
        area=pd.public("area"),
        meeting_mode=pd.public("meeting_mode"),
        time_windows=pd.public("time_windows"),
        faith_context=pd.public("faith_context"),
        relationship=relationship or Relationship(status="none"),
    )


def person_cards(db: Session, viewer_id: UUID, ids: Iterable[UUID]) -> list[PersonCard]:
    profiles = load_profiles(db, ids)
    rel = relationships(db, viewer_id)
    cards = [card(pd, rel.get(uid)) for uid, pd in profiles.items()]
    return sorted(cards, key=lambda c: (c.display_name.lower(), str(c.id)))


def person_card(db: Session, viewer_id: UUID, user_id: UUID) -> PersonCard:
    return card(load_profile(db, user_id), relationships(db, viewer_id).get(user_id))


def own_profile(db: Session, user_id: UUID) -> OwnProfile:
    pd = load_profile(db, user_id)
    return OwnProfile(
        display_name=pd.user.display_name,
        stage=pd.profile.stage,
        looking_for=pd.get("looking_for"),
        interests=pd.get("interests"),
        challenges=pd.get("challenges"),
        industry=pd.get("industry"),
        summary=pd.get("summary"),
        area=pd.get("area"),
        meeting_mode=pd.get("meeting_mode"),
        time_windows=pd.get("time_windows"),
        faith_context=pd.get("faith_context"),
        faith_matching_opt_in=pd.profile.faith_matching_opt_in,
        visibility={ProfileField(f): Visibility(pd.visibility_of(f.value)) for f in ProfileField},
        contact=ContactDetails(
            email=pd.profile.contact_email,
            phone=pd.profile.contact_phone,
            other=pd.profile.contact_other,
        ),
        directory_listed=policy.is_listed(db, user_id),
        onboarding_completed=pd.profile.onboarding_completed,
        updated_at=pd.profile.updated_at,
    )


def _plain(value: Any) -> Any:
    if isinstance(value, list):
        return [str(getattr(v, "value", v)) for v in dict.fromkeys(value)]
    return getattr(value, "value", value)


def write_fields(
    db: Session,
    user_id: UUID,
    values: dict[str, Any],
    visibility: dict[ProfileField, Visibility],
) -> None:
    """Upsert the given fields; an empty value removes the field. Other fields are untouched."""
    current = {
        r.field: r
        for r in db.scalars(select(ProfileFieldRow).where(ProfileFieldRow.user_id == user_id))
    }
    chosen = {k.value: v.value for k, v in visibility.items()}
    for name, raw in values.items():
        value = _plain(raw)
        row = current.get(name)
        if value in (None, "", []):
            if row is not None:
                db.delete(row)
            continue
        vis = chosen.get(name) or (row.visibility if row else DEFAULT_VISIBILITY[name])
        if row is None:
            db.add(ProfileFieldRow(user_id=user_id, field=name, value=value, visibility=vis))
        else:
            row.value, row.visibility = value, vis
    for name, vis in chosen.items():
        if name not in values and name in current:
            current[name].visibility = vis
    db.flush()


def save_profile(db: Session, user_id: UUID, body: ProfileFields, onboarded: bool | None) -> None:
    """Replaces editable profile content. Touches no consent row (MN-001, US-002 AC5)."""
    pd = load_profile(db, user_id)
    pd.user.display_name = body.display_name
    pd.profile.stage = body.stage.value
    pd.profile.faith_matching_opt_in = body.faith_matching_opt_in
    pd.profile.contact_email = body.contact.email or None
    pd.profile.contact_phone = body.contact.phone or None
    pd.profile.contact_other = body.contact.other or None
    pd.profile.updated_at = policy.now()
    if onboarded is not None:
        pd.profile.onboarding_completed = onboarded
    values = {f.value: getattr(body, f.value) for f in ProfileField}
    write_fields(db, user_id, values, body.visibility)


def delete_all_fields(db: Session, user_id: UUID) -> None:
    db.execute(delete(ProfileFieldRow).where(ProfileFieldRow.user_id == user_id))


def matching_fields_view(
    db: Session, viewer_id: UUID, role: str, subject_id: UUID, circle_id: UUID | None
) -> MatchingFieldsView:
    """Return `matching_only` fields to permitted staff. The access-log row is written and
    flushed first; if that fails the exception propagates and nothing is returned (CR-016)."""
    pd = load_profile(db, subject_id)
    fields = pd.matching_only_fields()
    entry = StaffAccessLog(
        viewer_id=viewer_id,
        viewer_role=role,
        subject_id=subject_id,
        fields=sorted(fields),
        circle_id=circle_id,
    )
    db.add(entry)
    db.flush()
    return MatchingFieldsView(
        subject_id=subject_id,
        display_name=pd.user.display_name,
        fields={ProfileField(k): v for k, v in fields.items()},
        access_log_id=entry.id,
    )


def _labelled(enum: Iterable[Any]) -> list[LabelledValue]:
    return [LabelledValue(value=e.value, label=vocab.label(e.value)) for e in enum]


def vocabulary() -> Vocabulary:
    return Vocabulary(
        stages=_labelled(vocab.Stage),
        interests=_labelled(vocab.Interest),
        challenges=_labelled(vocab.Challenge),
        looking_for=_labelled(vocab.LookingFor),
        industries=_labelled(vocab.Industry),
        areas=_labelled(vocab.Area),
        meeting_modes=_labelled(vocab.MeetingMode),
        time_windows=_labelled(vocab.TimeWindow),
        visibility_fields=_labelled(vocab.ProfileField),
        limits={
            "summary_max": vocab.SUMMARY_MAX,
            "free_text_max": vocab.FREE_TEXT_MAX,
            "faith_context_max": vocab.FAITH_CONTEXT_MAX,
            "tags_max": vocab.TAGS_MAX,
        },
    )
