"""Synthetic seed data (US-001, MD-017). Every record is made up; no real person or venue.

`uv run python -m app.seed` seeds an empty database. `--reset` wipes every table first.
Ids are deterministic (uuid5 of a short key) so tests and demos can refer to them.
"""

import sys
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.models import (
    Attendance,
    Base,
    BlockRow,
    Circle,
    CircleFacilitator,
    CircleMembership,
    ConnectionRequestRow,
    ConnectionRow,
    ContactShare,
    DiscoveryConsent,
    Event,
    EventApprovalRow,
    EventCheckinCode,
    EventHost,
    FollowUpReportRow,
    Profile,
    ProfileFieldRow,
    Registration,
    ReportRow,
    User,
    VenueRow,
)
from app.db.session import new_session
from app.security import hash_event_code
from app.services import policy

NAMESPACE = uuid.UUID("5f0c1d6e-3b1a-4c55-9a51-0c6f2e9d7a10")
SEED_EVENT_CODE = "CAFE42"


def sid(key: str) -> uuid.UUID:
    """Deterministic id for a seed key, e.g. `sid("mei")`."""
    return uuid.uuid5(NAMESPACE, key)


# key: (name, stage, admin, organiser, listed, blurb, fields, matching_only, faith_opt_in)
PEOPLE: dict[str, tuple[str, str, bool, bool, bool, str, dict[str, Any], tuple[str, ...], bool]] = {
    "ada": ("Ada (Admin)", "seasoned", True, False, False,
            "Admin: approves events, sees reports, venues, roles and metrics.",
            {"interests": ["community_building"]}, (), False),
    "olivia": ("Olivia", "seasoned", False, True, True,
               "Organiser: runs the coffee morning and has an event waiting for approval.",
               {"interests": ["community_building", "leadership"], "industry": "food_beverage",
                "looking_for": ["collaborators"], "area": "hong_kong_island",
                "meeting_mode": "in_person", "summary": "Runs a cafe and hosts founder mornings."},
               (), False),
    "chris": ("Chris", "new", False, False, False,
              "Co-host of the coffee morning. Not listed in the directory.",
              {"interests": ["operations"], "industry": "food_beverage"}, (), False),
    "felix": ("Felix", "seasoned", False, False, True,
              "Facilitator of Founders' Table; has one applicant to review.",
              {"interests": ["leadership", "finance"], "looking_for": ["mentee", "peer_support"],
               "industry": "professional_services", "area": "kowloon", "meeting_mode": "either",
               "summary": "Accountant turned founder who enjoys helping first-time owners."},
              (), False),
    "grace": ("Grace", "seasoned", False, False, True,
              "Facilitator of the faith-tagged circle. Faith is public and opted in to matching.",
              {"interests": ["social_impact", "leadership"], "looking_for": ["fellowship", "mentee"],
               "industry": "nonprofit_social", "area": "hong_kong_island", "meeting_mode": "in_person",
               "faith_context": "Christian", "summary": "Leads a social enterprise for youth jobs."},
              (), True),
    "mei": ("Mei", "new", False, False, True,
            "New founder. Attended the coffee morning and opted in to reconnect. "
            "Keeps her challenges Private: matching. Has blocked Ken.",
            {"interests": ["marketing", "branding"], "challenges": ["cash_flow", "pricing"],
             "looking_for": ["peer_support", "mentor"], "industry": "food_beverage",
             "area": "kowloon", "meeting_mode": "in_person", "time_windows": ["weekday_evening"],
             "summary": "Opened a small bakery last year and is learning to market it."},
            ("challenges",), False),
    "ravi": ("Ravi", "aspiring", False, False, True,
             "Thinking of starting. Has asked Mei to connect and applied to Founders' Table.",
             {"interests": ["ai_tools", "product"], "challenges": ["validating_idea"],
              "looking_for": ["mentor", "learning_group"], "industry": "technology",
              "area": "new_territories", "meeting_mode": "online",
              "summary": "Exploring an app idea for tutoring centres while still employed."},
             (), False),
    "sam": ("Sam", "seasoned", False, False, True,
            "Seasoned founder. Connected with Lily; Sam shares contacts, Lily not yet.",
            {"interests": ["sales", "exports"], "challenges": ["hiring_team"],
             "looking_for": ["peer_support", "mentee"], "industry": "logistics_trade",
             "area": "kowloon", "meeting_mode": "either", "time_windows": ["weekday_daytime"],
             "summary": "Has run a trading company for twelve years and now mentors new owners."},
            (), False),
    "nina": ("Nina", "new", False, False, False,
             "Not in the directory, but attended the coffee morning and opted in to reconnect.",
             {"interests": ["ecommerce", "marketing"], "challenges": ["finding_customers"],
              "looking_for": ["accountability_partner"], "industry": "retail",
              "area": "hong_kong_island", "meeting_mode": "either",
              "summary": "Sells handmade stationery online."}, (), False),
    "ken": ("Ken", "new", False, False, True,
            "Listed in the directory. Blocked by Mei, and reported once.",
            {"interests": ["sales", "marketing"], "challenges": ["finding_customers"],
             "looking_for": ["customer_intros"], "industry": "retail", "area": "kowloon",
             "meeting_mode": "in_person", "summary": "Runs a phone accessories stall."}, (), False),
    "lily": ("Lily", "aspiring", False, False, True,
             "Thinking of starting. Faith opted in to matching; member of the faith-tagged circle.",
             {"interests": ["social_impact", "sustainability"], "challenges": ["validating_idea"],
              "looking_for": ["fellowship", "mentor"], "industry": "education",
              "area": "hong_kong_island", "meeting_mode": "in_person", "faith_context": "Christian",
              "summary": "Planning a tutoring service for low-income families."},
             ("faith_context",), True),
    "tom": ("Tom", "aspiring", False, False, False,
            "Registered for the coffee morning but did not attend. Not listed.",
            {"interests": ["product"]}, (), False),
    "dee": ("Dee", "new", False, False, True,
            "Sent Sam a request that was declined (Dee still sees it as sent).",
            {"interests": ["finance", "operations"], "challenges": ["cash_flow", "scaling_operations"],
             "looking_for": ["mentor"], "industry": "manufacturing", "area": "new_territories",
             "meeting_mode": "online", "summary": "Took over a family packaging workshop."},
            (), False),
}  # fmt: skip


def is_empty(db: Session) -> bool:
    return not db.scalar(select(func.count()).select_from(User))


def wipe(db: Session) -> None:
    names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    db.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


def seed(db: Session) -> None:
    now = policy.now()
    for key, (
        name,
        stage,
        admin,
        organiser,
        listed,
        blurb,
        fields,
        private,
        faith,
    ) in PEOPLE.items():
        uid = sid(key)
        db.add(User(id=uid, display_name=name, is_admin=admin, is_organiser=organiser,
                    persona_blurb=blurb))  # fmt: skip
        db.flush()
        db.add(Profile(user_id=uid, stage=stage, faith_matching_opt_in=faith,
                       onboarding_completed=True, contact_email=f"{key}@example.test",
                       contact_other=f"WhatsApp: {key}-synthetic"))  # fmt: skip
        for field, value in fields.items():
            default = "matching_only" if field == "faith_context" and key != "grace" else "public"
            visibility = "matching_only" if field in private else default
            db.add(ProfileFieldRow(user_id=uid, field=field, value=value, visibility=visibility))
        if listed:
            db.add(DiscoveryConsent(user_id=uid, event_id=None))
    db.flush()

    db.add_all([
        VenueRow(id=sid("venue-cafe"), name="Harbour Beans Cafe (synthetic)", area="Sheung Wan",
                 address_hint="Ground floor, near the MTR", capacity=30, notes="Quiet before 10am"),
        VenueRow(id=sid("venue-hall"), name="Kowloon Community Hall (synthetic)", area="Mong Kok"),
    ])  # fmt: skip
    db.add_all([
        Circle(id=sid("circle-table"), name="Founders' Table",
               purpose="A monthly table for owners in their first three years to compare notes "
                       "on customers, cash and hiring.",
               tags=["finding_customers", "cash_flow", "hiring_team"], admission_policy="approval",
               member_list_visibility="members", meeting_mode="in_person", area="kowloon"),
        Circle(id=sid("circle-faith"), name="Faith & Work Circle",
               purpose="Entrepreneurs who want to talk about work, purpose and community together.",
               tags=["social_impact", "leadership"], admission_policy="open",
               member_list_visibility="everyone", meeting_mode="in_person",
               area="hong_kong_island", faith_tagged=True, faith_context_label="Christian"),
        Circle(id=sid("circle-community"), name="Filipino Founders in Hong Kong",
               purpose="A circle for founders with roots in the Philippines to share contacts, "
                       "suppliers and encouragement. Anyone who feels at home here is welcome.",
               tags=["finding_customers", "community_building"], admission_policy="open",
               member_list_visibility="members", meeting_mode="either",
               community_tagged=True, community_label="Filipino"),
    ])  # fmt: skip
    db.flush()
    db.add_all([
        CircleFacilitator(circle_id=sid("circle-table"), user_id=sid("felix")),
        CircleFacilitator(circle_id=sid("circle-faith"), user_id=sid("grace")),
        CircleFacilitator(circle_id=sid("circle-community"), user_id=sid("chris")),
        CircleMembership(circle_id=sid("circle-table"), user_id=sid("sam"), status="member"),
        CircleMembership(circle_id=sid("circle-table"), user_id=sid("mei"), status="member"),
        CircleMembership(circle_id=sid("circle-table"), user_id=sid("ravi"), status="applicant"),
        CircleMembership(circle_id=sid("circle-faith"), user_id=sid("lily"), status="member"),
    ])  # fmt: skip

    def event(key: str, title: str, start: timedelta, state: str, **kw: Any) -> Event:
        starts = now + start
        return Event(id=sid(key), organiser_id=sid("olivia"), title=title, starts_at=starts,
                     ends_at=starts + timedelta(hours=2), mode="in_person", state=state,
                     price_amount=80, price_currency="HKD", includes="One drink", **kw)  # fmt: skip

    db.add_all([
        event("event-coffee", "Founders' Coffee Morning", timedelta(days=-3), "approved",
              venue_id=sid("venue-cafe"), description="An informal morning for owners to meet.",
              capacity=20),
        event("event-pricing", "Pricing Workshop for New Owners", timedelta(days=14), "submitted",
              venue_id=sid("venue-hall"), description="Hands-on session on setting prices."),
        event("event-evening", "Founders' Table Open Evening", timedelta(days=7), "approved",
              venue_text="Felix's office, Tsim Sha Tsui", circle_id=sid("circle-table"),
              description="Meet the Founders' Table circle."),
        event("event-draft", "Export Basics (draft)", timedelta(days=30), "draft"),
    ])  # fmt: skip
    db.flush()
    coffee = sid("event-coffee")
    db.add(EventHost(event_id=coffee, user_id=sid("chris")))
    for key in ("event-coffee", "event-evening"):
        db.add(EventApprovalRow(event_id=sid(key), admin_id=sid("ada"), decision="approve",
                                decided_at=now - timedelta(days=10)))  # fmt: skip
    for key in ("mei", "nina", "tom", "ravi"):
        db.add(Registration(event_id=coffee, user_id=sid(key)))
    for key in ("mei", "nina", "ravi"):
        db.add(
            Attendance(event_id=coffee, user_id=sid(key), status="confirmed", source="organiser")
        )
    db.flush()
    for key in ("mei", "nina"):
        db.add(DiscoveryConsent(user_id=sid(key), event_id=coffee))
    db.add(EventCheckinCode(event_id=coffee, code_hash=hash_event_code(coffee, SEED_EVENT_CODE),
                            valid_until=now + timedelta(days=4), active=True))  # fmt: skip

    accepted = ConnectionRequestRow(
        id=sid("req-sam-lily"),
        sender_id=sid("sam"),
        recipient_id=sid("lily"),
        status="accepted",
        responded_at=now,
    )
    db.add_all([
        accepted,
        ConnectionRequestRow(id=sid("req-ravi-mei"), sender_id=sid("ravi"), recipient_id=sid("mei")),
        ConnectionRequestRow(id=sid("req-dee-sam"), sender_id=sid("dee"), recipient_id=sid("sam"),
                             status="declined", responded_at=now),
    ])  # fmt: skip
    db.flush()
    a, b = sorted((sid("sam"), sid("lily")))
    db.add(ConnectionRow(id=sid("conn-sam-lily"), user_a=a, user_b=b, request_id=accepted.id))
    db.flush()
    db.add_all([
        ContactShare(connection_id=sid("conn-sam-lily"), user_id=sid("sam")),
        FollowUpReportRow(connection_id=sid("conn-sam-lily"), number=1, reporter_id=sid("sam"),
                          met=True, usefulness=4),
        BlockRow(blocker_id=sid("mei"), blocked_id=sid("ken")),
        ReportRow(reporter_id=sid("mei"), subject_id=sid("ken"),
                  reason="Kept messaging me elsewhere after I said no (synthetic example)."),
    ])  # fmt: skip
    db.flush()


def reset(db: Session) -> None:
    wipe(db)
    seed(db)


def main() -> int:
    with new_session() as db:
        if "--reset" in sys.argv:
            reset(db)
            print("database wiped and seeded with synthetic data")
        elif is_empty(db):
            seed(db)
            print("seeded synthetic data")
        else:
            print("database is not empty; nothing changed (use --reset to wipe and reseed)")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
