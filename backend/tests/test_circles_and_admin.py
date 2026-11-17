"""Circles, staff access to Private: matching fields, venues and funnel metrics.

AC-011, AC-012, AC-020, MD-009, MD-010, MD-016, MD-022, MN-004, MN-009, MP-005, CR-016.
"""

import json
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import StaffAccessLog
from app.db.session import new_session
from app.main import app
from app.services import people
from tests.helpers import Api, uid

ApiFactory = Callable[..., Api]
TABLE, FAITH = uid("circle-table"), uid("circle-faith")


def test_ac011_admission_policy_and_leaving(api: ApiFactory) -> None:
    dee, felix = api("dee"), api("felix")
    assert dee.ok("POST", f"/circles/{FAITH}/join")["membership"] == "member"  # open circle
    assert dee.ok("POST", f"/circles/{TABLE}/join")["membership"] == "applicant"
    detail = dee.ok("GET", f"/circles/{TABLE}")
    assert detail["my_membership"] == "applicant" and detail["members"] is None
    assert detail["member_count"] is None  # member list is for members
    assert dee.error("GET", f"/circles/{TABLE}/applications", 403)
    assert dee.error("POST", f"/circles/{TABLE}/applications/{uid('dee')}/approve", 403)
    applicants = felix.ok("GET", f"/circles/{TABLE}/applications")
    assert {a["display_name"] for a in applicants} == {"Ravi", "Dee"}
    assert felix.ok("POST", f"/circles/{TABLE}/applications/{uid('dee')}/approve") == {
        "circle_id": TABLE,
        "membership": "member",
    }
    assert felix.delete(f"/circles/{TABLE}/applications/{uid('ravi')}/decline").status_code == 405
    assert felix.post(f"/circles/{TABLE}/applications/{uid('ravi')}/decline").status_code == 204
    members = {m["display_name"] for m in dee.ok("GET", f"/circles/{TABLE}")["members"]}
    assert members == {"Sam", "Mei", "Dee"}
    assert dee.delete(f"/circles/{TABLE}/membership").status_code == 204  # leaving is immediate
    assert dee.ok("GET", f"/circles/{TABLE}")["my_membership"] == "none"
    assert {c["name"] for c in dee.ok("GET", "/circles", params={"mine": True})} == {
        "Faith & Work Circle"
    }


def test_faith_tagged_circles_are_optional_and_write_no_faith_data(api: ApiFactory) -> None:
    """MD-010, MN-004, US-017."""
    dee = api("dee")
    tagged = dee.ok("GET", "/circles", params={"faith_tagged": True})
    assert [c["name"] for c in tagged] == ["Faith & Work Circle"]
    assert tagged[0]["faith_context_label"] == "Christian"
    untagged = dee.ok("GET", "/circles", params={"faith_tagged": False})
    assert [c["faith_context_label"] for c in untagged] == [None, None]
    before = dee.ok("GET", "/me/profile")
    dee.ok("POST", f"/circles/{FAITH}/join")
    after = dee.ok("GET", "/me/profile")
    assert after["faith_context"] is None and after["faith_matching_opt_in"] is False
    assert before | {"updated_at": 0} == after | {"updated_at": 0}


def test_community_circles_are_browse_only_and_write_nothing_to_the_profile(
    api: ApiFactory,
) -> None:
    """Operator decision 2026-11-17: people who share a background bond by joining a circle.
    Origin is never a profile field, a people filter or model input."""
    dee = api("dee")
    tagged = dee.ok("GET", "/circles", params={"community_tagged": True})
    assert [(c["name"], c["community_label"]) for c in tagged] == [
        ("Filipino Founders in Hong Kong", "Filipino")
    ]
    plain = dee.ok("GET", "/circles", params={"community_tagged": False})
    assert all(c["community_label"] is None for c in plain) and len(plain) == 2
    before = dee.ok("GET", "/me/profile")
    cid = tagged[0]["id"]
    assert dee.ok("POST", f"/circles/{cid}/join")["membership"] == "member"
    assert before | {"updated_at": 0} == dee.ok("GET", "/me/profile") | {"updated_at": 0}
    # nothing about the membership shows on her card to other people
    card = next(
        c for c in api("sam").ok("GET", "/directory")["people"] if c["display_name"] == "Dee"
    )
    assert "Filipino" not in json.dumps(card)
    # there is no origin filter on people: an unknown query key changes nothing
    everyone = api("sam").ok("GET", "/discover")["people"]
    assert api("sam").ok("GET", "/discover", params={"origin": "Filipino"})["people"] == everyone
    bad = {"name": "X", "purpose": "Y", "facilitator_id": uid("sam"), "community_label": "Thai"}
    assert api("ada").error("POST", "/circles", 422, bad)  # a label needs its tag


def test_only_facilitator_or_admin_can_edit_a_circle(api: ApiFactory) -> None:
    """US-016. Circle creation is admin-only (OQ-04 default)."""
    assert api("sam").error("PATCH", f"/circles/{TABLE}", 403, {"name": "Mine now"})
    assert api("grace").error("PATCH", f"/circles/{TABLE}", 403, {"name": "Not my circle"})
    updated = api("felix").ok(
        "PATCH",
        f"/circles/{TABLE}",
        {"member_list_visibility": "everyone", "admission_policy": "open"},
    )
    assert updated["member_list_visibility"] == "everyone"
    assert api("dee").ok("GET", f"/circles/{TABLE}")["member_count"] == 2
    body = {"name": "Makers", "purpose": "For product makers.", "facilitator_id": uid("sam")}
    assert api("felix").error("POST", "/circles", 403, body)
    created = api("ada").ok("POST", "/circles", body, status=201)
    assert [f["display_name"] for f in created["facilitators"]] == ["Sam"]
    assert "facilitator" in api("sam").ok("GET", "/session")["user"]["roles"]


def test_ac020_staff_access_to_matching_only_fields_is_scoped_and_logged(api: ApiFactory) -> None:
    mei, lily, ravi = uid("mei"), uid("lily"), uid("ravi")
    # admin: anyone, logged
    seen = api("ada").ok("GET", f"/admin/users/{mei}/matching-fields")
    assert seen["fields"] == {"challenges": ["cash_flow", "pricing"]}
    # facilitator: members and pending applicants of their own circle only
    felix = api("felix")
    assert felix.ok("GET", f"/circles/{TABLE}/members/{mei}/matching-fields")["fields"] == {
        "challenges": ["cash_flow", "pricing"]
    }
    assert felix.ok("GET", f"/circles/{TABLE}/members/{ravi}/matching-fields")["fields"] == {}
    assert felix.error("GET", f"/circles/{TABLE}/members/{lily}/matching-fields", 404)  # non-member
    # a forged circle id does not widen the scope: Felix does not facilitate the faith circle
    assert felix.error("GET", f"/circles/{FAITH}/members/{lily}/matching-fields", 403)
    assert felix.error("GET", f"/admin/users/{mei}/matching-fields", 403)
    # organisers, co-hosts and fellow members never
    for persona in ("olivia", "chris", "sam"):
        other = api(persona)
        assert other.error("GET", f"/circles/{TABLE}/members/{mei}/matching-fields", 403)
        assert other.error("GET", f"/admin/users/{mei}/matching-fields", 403)
    # exactly the three successful views were logged, with viewer, subject, fields and time
    log = api("ada").ok("GET", "/admin/access-log")
    got = {(e["viewer"]["display_name"], e["viewer_role"], e["subject"]["display_name"],
            tuple(e["fields"])) for e in log}  # fmt: skip
    assert got == {
        ("Ada (Admin)", "admin", "Mei", ("challenges",)),
        ("Felix", "facilitator", "Mei", ("challenges",)),
        ("Felix", "facilitator", "Ravi", ()),
    }
    assert all(e["viewed_at"] for e in log)
    assert felix.error("GET", "/admin/access-log", 403)


def test_cr016_fields_are_not_returned_when_the_access_log_cannot_be_written(
    api: ApiFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail closed: no log entry, no fields."""

    def broken(*_a: object, **_k: object) -> None:
        raise RuntimeError("log unavailable")

    monkeypatch.setattr(people, "StaffAccessLog", broken)
    ada = Api("ada")
    quiet = TestClient(app, base_url="https://testserver", raise_server_exceptions=False)
    quiet.cookies = ada.http.cookies
    ada.http = quiet
    response = ada.http.get(f"/admin/users/{uid('mei')}/matching-fields")
    assert response.status_code == 500
    assert "cash_flow" not in response.text and response.json()["error"]["code"] == "internal_error"
    with new_session() as db:
        assert db.scalars(select(StaffAccessLog)).all() == []


def test_ac012_venues_show_unknown_fields_as_null_and_have_no_booking(api: ApiFactory) -> None:
    venues = {v["name"]: v for v in api("olivia").ok("GET", "/venues")}
    hall = venues["Kowloon Community Hall (synthetic)"]
    assert hall["capacity"] is None and hall["notes"] is None  # rendered as "Unknown"
    assert all(v["synthetic"] for v in venues.values())  # MN-010
    body = {"name": "Test Room"}
    assert api("olivia").error("POST", "/admin/venues", 403, body)  # no user-submitted venues
    ada = api("ada")
    made = ada.ok("POST", "/admin/venues", body, status=201)
    assert made["capacity"] is None
    assert ada.ok("PUT", f"/admin/venues/{made['id']}", body | {"capacity": 12})["capacity"] == 12
    assert ada.delete(f"/admin/venues/{made['id']}").status_code == 204
    for path in ("/venues/book", f"/venues/{hall['id']}/bookings", "/payments", "/bookings"):
        assert ada.http.post(path).status_code == 404  # MN-009


def test_mp005_funnel_metrics_match_hand_counted_seed_values(api: ApiFactory) -> None:
    """Hand count from `app/seed.py`:
    4 registrations and 3 confirmed attendances at the one ended event; 2 of those opted in;
    9 of 13 people are listed; 3 requests were sent (1 accepted, 1 pending, 1 declined);
    1 connected pair, which reported a first catch-up and no second."""
    metrics = api("ada").ok("GET", "/admin/metrics")
    assert metrics["synthetic"] is True
    got = {u["key"]: (u["count"], u["denominator"]) for u in metrics["funnel"]}
    assert got == {
        "opportunities": (3, 4),
        "event_opt_ins": (2, 3),
        "directory_opt_ins": (9, 13),
        "requests": (3, 13),
        "acceptances": (1, 3),
        "first_catch_ups": (1, 1),
        "second_catch_ups": (0, 1),
    }
    self_reported = {u["key"] for u in metrics["funnel"] if u["self_reported"]}
    assert self_reported == {"first_catch_ups", "second_catch_ups"}
    text = json.dumps(metrics)
    assert "rate" not in {u["key"] for u in metrics["funnel"]}  # no combined conversion rate
    assert "Mei" not in text and "Sam" not in text  # aggregates only (US-022 AC4)
    assert metrics["ai"]["calls"] == 0 and metrics["ai"]["ai_enabled"] is True


def test_admin_grants_the_organiser_role(api: ApiFactory) -> None:
    ada = api("ada")
    users = {u["display_name"]: u for u in ada.ok("GET", "/admin/users")}
    assert users["Olivia"]["roles"] == ["participant", "organiser"]
    assert users["Felix"]["roles"] == ["participant", "facilitator"]
    granted = ada.ok("PUT", f"/admin/users/{uid('sam')}/roles", {"organiser": True})
    assert "organiser" in granted["roles"]
    assert api("mei").error("PUT", f"/admin/users/{uid('mei')}/roles", 403, {"organiser": True})
