"""Events: publication gate, registration, attendance, late attendance, reconnection.

AC-002, AC-006, AC-021, AC-022, AC-023, MN-001, MN-005, MN-007, MN-017, CR-014, CR-017.
"""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, update

from app.db.models import AttendanceLog, CheckinAttempt, Event, EventCheckinCode
from app.db.session import new_session
from app.seed import SEED_EVENT_CODE
from tests.helpers import Api, names, uid

ApiFactory = Callable[..., Api]
COFFEE, PRICING, EVENING, DRAFT = (
    uid("event-coffee"),
    uid("event-pricing"),
    uid("event-evening"),
    uid("event-draft"),
)


def new_event(**over: Any) -> dict[str, Any]:
    start = datetime.now(UTC) + timedelta(days=5)
    body = {"title": "Bookkeeping Basics", "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=2)).isoformat(), "mode": "in_person"}  # fmt: skip
    return body | over


def test_ac006_unapproved_events_do_not_exist_for_other_people(api: ApiFactory) -> None:
    """Every endpoint that takes an event id is checked, not only the listing (MN-005)."""
    mark = {"user_id": uid("mei"), "attended": True}
    participant_calls = [
        ("GET", "", None), ("POST", "/registrations", None), ("DELETE", "/registrations/me", None),
        ("GET", "/attendance", None), ("PUT", "/attendance", mark),
        ("POST", "/attendance-claims", None), ("DELETE", "/attendance-claims/me", None),
        ("POST", "/checkin", {"code": "ABC123"}), ("PUT", "/checkin-code", None),
        ("DELETE", "/checkin-code", None), ("PUT", "/reconnect-consent", {"opted_in": True}),
        ("GET", "/reconnect", None), ("PUT", "", new_event()), ("POST", "/submit", None),
        ("POST", "/withdraw", None), ("POST", "/cancel", None),
        ("PUT", f"/co-hosts/{uid('mei')}", None),
    ]  # fmt: skip
    for persona in ("mei", "felix", "chris"):
        viewer = api(persona)
        listed = {e["id"] for e in viewer.ok("GET", "/events")}
        assert listed == {COFFEE, EVENING}
        for event in (PRICING, DRAFT):
            for method, suffix, body in participant_calls:
                err = viewer.error(method, f"/events/{event}{suffix}", 404, body)
                assert err["code"] == "not_found", (persona, method, suffix)
        assert (
            viewer.error("GET", f"/events/{uid('no-such-event')}", 404)["message"]
            == (viewer.error("GET", f"/events/{PRICING}", 404)["message"])
        )
        assert PRICING not in json.dumps(viewer.ok("GET", f"/circles/{uid('circle-table')}"))
    # the organiser and the admin can see it
    assert api("olivia").ok("GET", f"/events/{PRICING}")["state"] == "submitted"
    assert api("ada").ok("GET", f"/events/{PRICING}")["state"] == "submitted"


def test_ac006_only_an_admin_decision_publishes_and_it_is_logged(api: ApiFactory) -> None:
    olivia, ada, mei = api("olivia"), api("ada"), api("mei")
    for persona in ("olivia", "mei", "felix"):  # nobody else can decide, not even the organiser
        assert api(persona).error(
            "POST", f"/admin/events/{PRICING}/decision", 403, {"decision": "approve"}
        )
    assert [e["id"] for e in ada.ok("GET", "/admin/events/queue")] == [PRICING]
    decided = ada.ok("POST", f"/admin/events/{PRICING}/decision", {"decision": "approve"})
    assert decided["state"] == "approved"
    log = decided["approvals"][-1]
    assert log["admin"]["display_name"] == "Ada (Admin)" and log["decision"] == "approve"
    assert log["decided_at"]
    assert PRICING in {e["id"] for e in mei.ok("GET", "/events")}
    assert mei.ok("GET", f"/events/{PRICING}")["approvals"] is None  # log is for staff
    assert ada.error("POST", f"/admin/events/{PRICING}/decision", 409, {"decision": "reject"})
    # a draft cannot be decided: it was never submitted
    assert ada.error("POST", f"/admin/events/{DRAFT}/decision", 409, {"decision": "approve"})
    # rejection returns it to the organiser with the reason, and it stays invisible
    olivia.ok("POST", f"/events/{DRAFT}/submit")
    rejected = ada.ok(
        "POST", f"/admin/events/{DRAFT}/decision", {"decision": "reject", "reason": "Add a venue"}
    )
    assert rejected["state"] == "rejected"
    assert olivia.ok("GET", f"/events/{DRAFT}")["approvals"][-1]["reason"] == "Add a venue"
    mei.error("GET", f"/events/{DRAFT}", 404)


def test_organiser_flow_and_ac023_past_dated_events(api: ApiFactory) -> None:
    """US-012, MD-025: draft, edit, submit, withdraw; a past date still needs approval."""
    olivia, mei = api("olivia"), api("mei")
    assert mei.error("POST", "/events", 403, new_event())["code"] == "forbidden"
    past = datetime.now(UTC) - timedelta(days=2)
    body = new_event(title="Cafe Meetup", starts_at=past.isoformat(),
                     ends_at=(past + timedelta(hours=2)).isoformat())  # fmt: skip
    created = olivia.ok("POST", "/events", body, status=201)
    assert created["state"] == "draft" and created["added_after_event"] is True
    eid = created["id"]
    mei.error("GET", f"/events/{eid}", 404)
    olivia.error("POST", "/events", 422, new_event(ends_at=new_event()["starts_at"]))
    olivia.error("POST", "/events", 422, new_event(price_amount="10.00"))
    olivia.ok("POST", f"/events/{eid}/submit")
    assert olivia.error("PUT", f"/events/{eid}", 409, body)["code"] == "not_editable"
    assert eid in {e["id"] for e in api("ada").ok("GET", "/admin/events/queue")}
    mei.error("GET", f"/events/{eid}", 404)  # AC-023: invisible until approved
    olivia.ok("POST", f"/events/{eid}/withdraw")
    assert olivia.ok("PUT", f"/events/{eid}", body | {"title": "Cafe Meetup 2"})["title"] == (
        "Cafe Meetup 2"
    )
    assert {e["id"] for e in olivia.ok("GET", "/events/mine")} >= {eid, DRAFT, PRICING}


def test_co_hosts_manage_one_event_and_cannot_publish(api: ApiFactory) -> None:
    """US-018, MD-013."""
    olivia, chris, mei = api("olivia"), api("chris"), api("mei")
    assert chris.ok("GET", f"/events/{COFFEE}")["my"]["can_manage"] is True
    assert chris.ok("GET", f"/events/{COFFEE}/attendance")["counts"]["registered"] == 4
    chris.error("GET", f"/events/{DRAFT}", 404)  # co-host of the coffee morning only
    assert chris.error("PUT", f"/events/{COFFEE}/co-hosts/{uid('mei')}", 403)
    assert mei.error("GET", f"/events/{COFFEE}/attendance", 403)["code"] == "forbidden"
    olivia.ok("PUT", f"/events/{DRAFT}/co-hosts/{uid('chris')}")
    assert chris.ok("GET", f"/events/{DRAFT}")["state"] == "draft"
    assert chris.error("POST", f"/events/{DRAFT}/submit", 403)
    assert chris.error("POST", f"/admin/events/{DRAFT}/decision", 403, {"decision": "approve"})
    olivia.ok("DELETE", f"/events/{DRAFT}/co-hosts/{uid('chris')}")
    chris.error("GET", f"/events/{DRAFT}", 404)


def test_registration_changes_no_consent_and_no_membership(api: ApiFactory) -> None:
    """MN-001, MN-007, US-014."""
    dee = api("dee")
    before = dee.ok("GET", "/me/profile")["directory_listed"]
    assert dee.ok("POST", f"/events/{EVENING}/registrations") == {
        "event_id": EVENING,
        "registered": True,
    }
    status = dee.ok("GET", f"/events/{EVENING}")["my"]
    assert status["registered"] is True and status["attendance"] == "none"
    assert status["reconnect_opted_in"] is False
    assert dee.ok("GET", "/me/profile")["directory_listed"] is before
    circle = dee.ok("GET", f"/circles/{uid('circle-table')}")  # the event is linked to it
    assert circle["my_membership"] == "none" and circle["members"] is None
    assert dee.ok("DELETE", f"/events/{EVENING}/registrations/me")["registered"] is False
    assert dee.error("POST", f"/events/{COFFEE}/registrations", 409)["code"] == "event_ended"


def test_ac002_reconnection_needs_confirmed_attendance_and_opt_in(api: ApiFactory) -> None:
    mei, nina, tom, ravi = api("mei"), api("nina"), api("tom"), api("ravi")
    path = f"/events/{COFFEE}/reconnect"
    assert names(mei.ok("GET", path)["people"]) == {"Nina"}
    assert names(nina.ok("GET", path)["people"]) == {"Mei"}
    # Tom registered but was not confirmed: no list, and he cannot opt in
    assert tom.error("GET", path, 403)["code"] == "attendance_not_confirmed"
    err = tom.error("PUT", f"/events/{COFFEE}/reconnect-consent", 403, {"opted_in": True})
    assert err["code"] == "attendance_not_confirmed"
    # Ravi attended but has not opted in: attendance alone opts nobody in (US-015 AC2)
    assert ravi.error("GET", path, 403)["code"] == "reconnect_not_opted_in"
    assert "Ravi" not in names(mei.ok("GET", path)["people"])
    ravi.ok("PUT", f"/events/{COFFEE}/reconnect-consent", {"opted_in": True})
    assert names(ravi.ok("GET", path)["people"]) == {"Mei", "Nina"}
    # event consent is not directory consent (MN-001): Nina is still not in the directory
    assert nina.ok("GET", "/me/profile")["directory_listed"] is False
    assert "Nina" not in names(api("sam").ok("GET", "/directory")["people"])
    # but people on the same list can ask each other to connect (US-004 AC5)
    sent = mei.ok("POST", "/requests", {"recipient_id": uid("nina")}, status=201)
    assert sent["person"]["display_name"] == "Nina"
    assert api("sam").error("POST", "/requests", 404, {"recipient_id": uid("nina")})
    # blocks apply here too (AC-005)
    nina.ok("POST", "/blocks", {"user_id": uid("ravi")}, status=201)
    assert names(ravi.ok("GET", path)["people"]) == {"Mei"}
    # reconnection opens only after the event ends
    assert mei.error("GET", f"/events/{EVENING}/reconnect", 403)["code"] == (
        "attendance_not_confirmed"
    )


def test_attendance_marks_are_host_only_logged_and_reversible(api: ApiFactory) -> None:
    """US-015."""
    olivia, mei = api("olivia"), api("mei")
    path = f"/events/{COFFEE}/attendance"
    assert mei.error("PUT", path, 403, {"user_id": uid("tom"), "attended": True})
    assert olivia.error("PUT", path, 404, {"user_id": uid("dee"), "attended": True})  # not listed
    not_started = {"user_id": uid("mei"), "attended": True}
    olivia.ok("POST", f"/events/{EVENING}/registrations")
    assert olivia.error("PUT", f"/events/{EVENING}/attendance", 409, not_started)["code"] == (
        "event_not_started"
    )
    after = olivia.ok("PUT", path, {"user_id": uid("tom"), "attended": True})
    assert after["counts"]["confirmed"] == 4
    # correcting Mei to "did not attend" removes her from the reconnection list at once
    corrected = olivia.ok("PUT", path, {"user_id": uid("mei"), "attended": False})
    assert corrected["counts"] == {
        "registered": 4, "confirmed": 3, "confirmed_by_organiser": 3, "confirmed_by_claim": 0,
        "confirmed_by_code": 0, "claims_pending": 0,
    }  # fmt: skip
    assert (
        mei.error("GET", f"/events/{COFFEE}/reconnect", 403)["code"] == "attendance_not_confirmed"
    )
    assert "Mei" not in names(api("nina").ok("GET", f"/events/{COFFEE}/reconnect")["people"])
    with new_session() as db:
        changes = db.execute(select(AttendanceLog.from_status, AttendanceLog.to_status)).all()
    assert sorted(changes) == [("confirmed", "none"), ("none", "confirmed")]


def test_ac021_i_was_there_claim_reveals_nothing_until_the_host_approves(api: ApiFactory) -> None:
    dee, sam, olivia, chris = api("dee"), api("sam"), api("olivia"), api("chris")
    for person in (dee, sam):  # neither registered beforehand
        claimed = person.ok("POST", f"/events/{COFFEE}/attendance-claims", status=201)
        assert claimed == {
            "event_id": COFFEE,
            "attendance": "claimed",
            "attendance_source": "claim",
        }
        assert person.error("GET", f"/events/{COFFEE}/reconnect", 403)["code"] == (
            "attendance_not_confirmed"
        )
        person.error("PUT", f"/events/{COFFEE}/reconnect-consent", 403, {"opted_in": True})
        assert "Nina" not in json.dumps(person.ok("GET", f"/events/{COFFEE}"))
    claims = {
        c["display_name"]: c["claim_id"]
        for c in olivia.ok("GET", f"/events/{COFFEE}/attendance")["claims"]
    }
    assert set(claims) == {"Dee", "Sam"}
    base = f"/events/{COFFEE}/attendance-claims"
    assert dee.error("POST", f"{base}/{claims['Dee']}/approve", 403)  # cannot approve yourself
    host = chris.ok("POST", f"{base}/{claims['Dee']}/approve")  # a co-host may decide
    assert host["counts"]["confirmed_by_claim"] == 1 and host["counts"]["claims_pending"] == 1
    olivia.ok("POST", f"{base}/{claims['Sam']}/decline")
    # approved: Dee can now opt in and see the list
    assert dee.ok("GET", f"/events/{COFFEE}")["my"]["attendance"] == "confirmed"
    dee.ok("PUT", f"/events/{COFFEE}/reconnect-consent", {"opted_in": True})
    assert names(dee.ok("GET", f"/events/{COFFEE}/reconnect")["people"]) == {"Mei", "Nina"}
    # declined: nothing is revealed, and claiming again does not reopen it
    assert sam.ok("GET", f"/events/{COFFEE}")["my"]["attendance"] == "declined"
    assert sam.ok("POST", f"/events/{COFFEE}/attendance-claims", status=201)["attendance"] == (
        "declined"
    )
    assert (
        sam.error("GET", f"/events/{COFFEE}/reconnect", 403)["code"] == "attendance_not_confirmed"
    )
    # claims work only on approved, started events (MN-017)
    assert dee.error("POST", f"/events/{EVENING}/attendance-claims", 409)["code"] == (
        "event_not_started"
    )
    dee.error("POST", f"/events/{PRICING}/attendance-claims", 404)


def test_ac022_event_code_confirms_at_once_and_fails_closed(api: ApiFactory) -> None:
    dee, olivia = api("dee"), api("olivia")
    path = f"/events/{COFFEE}/checkin"
    wrong = dee.error("POST", path, 422, {"code": "WRONG1"})
    assert wrong["code"] == "code_invalid"
    assert dee.ok("GET", f"/events/{COFFEE}")["my"]["attendance"] == "none"  # nothing changed
    ok = dee.ok("POST", path, {"code": f" {SEED_EVENT_CODE.lower()} "})
    assert ok == {"event_id": COFFEE, "attendance": "confirmed", "attendance_source": "code"}
    host = olivia.ok("GET", f"/events/{COFFEE}/attendance")
    assert [r["display_name"] for r in host["joined_by_code"]] == ["Dee"]
    # confirmed attendance still needs the person's own opt-in (US-025 AC6)
    assert dee.error("GET", f"/events/{COFFEE}/reconnect", 403)["code"] == "reconnect_not_opted_in"
    dee.ok("PUT", f"/events/{COFFEE}/reconnect-consent", {"opted_in": True})
    # the organiser can remove someone who joined by code; they drop off the list at once
    olivia.ok("PUT", f"/events/{COFFEE}/attendance", {"user_id": uid("dee"), "attended": False})
    assert (
        dee.error("GET", f"/events/{COFFEE}/reconnect", 403)["code"] == "attendance_not_confirmed"
    )
    # rotating invalidates the old code; the new one is shown once and only its hash is stored
    issued = olivia.ok("PUT", f"/events/{COFFEE}/checkin-code")
    assert len(issued["code"]) == 6 and issued["active"] is True
    assert api("mei").error("PUT", f"/events/{COFFEE}/checkin-code", 403)
    sam = api("sam")
    assert sam.error("POST", path, 422, {"code": SEED_EVENT_CODE})["code"] == "code_invalid"
    with new_session() as db:
        stored = db.get(EventCheckinCode, COFFEE)
        assert stored is not None and issued["code"] not in stored.code_hash
    assert "code" not in olivia.ok("GET", f"/events/{COFFEE}/attendance")["checkin_code"]
    assert sam.ok("POST", path, {"code": issued["code"]})["attendance"] == "confirmed"
    # disabled
    assert olivia.delete(f"/events/{COFFEE}/checkin-code").status_code == 204
    assert api("ken").error("POST", path, 422, {"code": issued["code"]})["code"] == "code_invalid"
    # expired: more than 7 days after the event ended
    olivia.ok("PUT", f"/events/{COFFEE}/checkin-code")
    with new_session() as db:
        db.execute(
            update(EventCheckinCode).values(valid_until=datetime.now(UTC) - timedelta(minutes=1))
        )
        db.commit()
    assert api("ken").error("POST", path, 422, {"code": "ANYTHING"})["code"] == "code_expired"
    assert api("ken").ok("GET", f"/events/{COFFEE}")["my"]["attendance"] == "none"


def test_ac022_sixth_wrong_code_in_an_hour_is_refused(api: ApiFactory) -> None:
    felix = api("felix")
    path = f"/events/{COFFEE}/checkin"
    for _ in range(5):
        assert felix.error("POST", path, 422, {"code": "WRONG1"})["code"] == "code_invalid"
    refused = felix.error("POST", path, 429, {"code": SEED_EVENT_CODE})  # even the right code
    assert refused["code"] == "rate_limited" and refused["retry_at"]
    assert felix.ok("GET", f"/events/{COFFEE}")["my"]["attendance"] == "none"
    with new_session() as db:  # the failed attempts were stored despite the error responses
        assert len(db.scalars(select(CheckinAttempt)).all()) == 5
    # the limit is per person: someone else is unaffected
    assert api("dee").ok("POST", path, {"code": SEED_EVENT_CODE})["attendance"] == "confirmed"


def test_code_window_is_seven_days_after_the_event_ends(api: ApiFactory) -> None:
    issued = api("olivia").ok("PUT", f"/events/{COFFEE}/checkin-code")
    with new_session() as db:
        event = db.get(Event, COFFEE)
        assert event is not None
        expected = event.ends_at + timedelta(days=7)
    assert datetime.fromisoformat(issued["valid_until"]) == expected


def test_cancelled_events_accept_no_participant_actions(api: ApiFactory) -> None:
    api("olivia").ok("POST", f"/events/{EVENING}/cancel")
    mei = api("mei")
    assert EVENING not in {e["id"] for e in mei.ok("GET", "/events")}
    assert mei.ok("GET", f"/events/{EVENING}")["state"] == "cancelled"
    assert mei.error("POST", f"/events/{EVENING}/registrations", 409)["code"] == "event_cancelled"


def test_a_pending_claim_can_be_withdrawn(api: ApiFactory) -> None:
    """ux.md Waiting state: "withdraw the claim"."""
    dee, olivia = api("dee"), api("olivia")
    dee.ok("POST", f"/events/{COFFEE}/attendance-claims", status=201)
    assert len(olivia.ok("GET", f"/events/{COFFEE}/attendance")["claims"]) == 1
    withdrawn = dee.ok("DELETE", f"/events/{COFFEE}/attendance-claims/me")
    assert withdrawn == {"event_id": COFFEE, "attendance": "none", "attendance_source": None}
    assert olivia.ok("GET", f"/events/{COFFEE}/attendance")["claims"] == []
    # withdrawing does not undo a confirmed attendance
    mei = api("mei")
    assert mei.ok("DELETE", f"/events/{COFFEE}/attendance-claims/me")["attendance"] == "confirmed"
