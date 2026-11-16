"""Fixed vocabulary for profile tags and enumerated states (SAD §4 Validation, CR-003).

Tags are a closed set so that user-authored text reaching a prompt is limited to the
summary line and the assistant's free text. Labels are display strings for the UI.
The tag lists are a Build-phase assumption (see backend.md): the Define artifacts
require a fixed vocabulary but do not enumerate it.
"""

from enum import StrEnum


class Stage(StrEnum):
    seasoned = "seasoned"
    new = "new"
    aspiring = "aspiring"


class Interest(StrEnum):
    marketing = "marketing"
    sales = "sales"
    branding = "branding"
    product = "product"
    operations = "operations"
    finance = "finance"
    fundraising = "fundraising"
    hiring = "hiring"
    leadership = "leadership"
    ai_tools = "ai_tools"
    ecommerce = "ecommerce"
    exports = "exports"
    sustainability = "sustainability"
    social_impact = "social_impact"
    community_building = "community_building"


class Challenge(StrEnum):
    validating_idea = "validating_idea"
    finding_customers = "finding_customers"
    pricing = "pricing"
    cash_flow = "cash_flow"
    raising_capital = "raising_capital"
    hiring_team = "hiring_team"
    finding_cofounder = "finding_cofounder"
    time_management = "time_management"
    scaling_operations = "scaling_operations"
    going_digital = "going_digital"
    licensing_regulation = "licensing_regulation"


class LookingFor(StrEnum):
    peer_support = "peer_support"
    accountability_partner = "accountability_partner"
    mentor = "mentor"
    mentee = "mentee"
    cofounder = "cofounder"
    collaborators = "collaborators"
    customer_intros = "customer_intros"
    investor_intros = "investor_intros"
    learning_group = "learning_group"
    fellowship = "fellowship"


class Industry(StrEnum):
    food_beverage = "food_beverage"
    retail = "retail"
    technology = "technology"
    professional_services = "professional_services"
    education = "education"
    health_wellness = "health_wellness"
    creative_media = "creative_media"
    finance_fintech = "finance_fintech"
    logistics_trade = "logistics_trade"
    manufacturing = "manufacturing"
    hospitality_tourism = "hospitality_tourism"
    nonprofit_social = "nonprofit_social"
    other = "other"


class Area(StrEnum):
    """Coarse meetup areas only (MN-012): no district-level address, no live location."""

    hong_kong_island = "hong_kong_island"
    kowloon = "kowloon"
    new_territories = "new_territories"
    outlying_islands = "outlying_islands"


class MeetingMode(StrEnum):
    in_person = "in_person"
    online = "online"
    either = "either"


class TimeWindow(StrEnum):
    weekday_daytime = "weekday_daytime"
    weekday_evening = "weekday_evening"
    weekend = "weekend"


class Visibility(StrEnum):
    """MD-020. `matching_only` is labelled "Private: matching" in the UI (ux.md OQ-UX02)."""

    public = "public"
    matching_only = "matching_only"


class ProfileField(StrEnum):
    """Profile fields with a per-field visibility. Display name and stage are always public."""

    looking_for = "looking_for"
    interests = "interests"
    challenges = "challenges"
    industry = "industry"
    summary = "summary"
    area = "area"
    meeting_mode = "meeting_mode"
    time_windows = "time_windows"
    faith_context = "faith_context"


# MD-021: the only fields the suggestion model may receive (faith only with its opt-in).
MATCHING_FIELDS: tuple[ProfileField, ...] = tuple(ProfileField)
# Fields a suggestion reason may cite (stage is always public and always citable).
CITABLE_FIELD_NAMES: tuple[str, ...] = ("stage", *[f.value for f in ProfileField])


class Role(StrEnum):
    participant = "participant"
    organiser = "organiser"
    facilitator = "facilitator"
    admin = "admin"


class RequestStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    withdrawn = "withdrawn"


class AdmissionPolicy(StrEnum):
    open = "open"
    approval = "approval"


class MemberListVisibility(StrEnum):
    members = "members"
    everyone = "everyone"
    facilitators = "facilitators"


class MembershipStatus(StrEnum):
    none = "none"
    applicant = "applicant"
    member = "member"


class EventState(StrEnum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class EventMode(StrEnum):
    in_person = "in_person"
    online = "online"
    hybrid = "hybrid"


class AttendanceStatus(StrEnum):
    none = "none"
    claimed = "claimed"
    confirmed = "confirmed"
    declined = "declined"


class AttendanceSource(StrEnum):
    organiser = "organiser"
    claim = "claim"
    code = "code"


class Decision(StrEnum):
    approve = "approve"
    reject = "reject"


SUMMARY_MAX = 200  # "bio" cap, CR-003
FREE_TEXT_MAX = 1500  # assistant free text cap, CR-003
FAITH_CONTEXT_MAX = 80
TAGS_MAX = 8
REASON_MAX_WORDS = 25


_LABELS = {
    "ai_tools": "AI tools",
    "ecommerce": "E-commerce",
    "new": "New entrepreneur",
    "seasoned": "Seasoned entrepreneur",
    "aspiring": "Thinking of starting",
    "food_beverage": "Food & beverage",
    "health_wellness": "Health & wellness",
    "creative_media": "Creative & media",
    "finance_fintech": "Finance & fintech",
    "logistics_trade": "Logistics & trade",
    "hospitality_tourism": "Hospitality & tourism",
    "nonprofit_social": "Non-profit & social enterprise",
    "hong_kong_island": "Hong Kong Island",
    "cofounder": "Co-founder",
    "finding_cofounder": "Finding a co-founder",
    "licensing_regulation": "Licensing & regulation",
    "in_person": "In person",
}


def label(value: str) -> str:
    """Display label for a vocabulary value."""
    return _LABELS.get(value, value.replace("_", " ").capitalize())
