"""Privacy and access boundaries (MP-001): AC-001, AC-003, AC-004, AC-005, AC-010, AC-019."""

import json
from collections.abc import Callable

from tests.helpers import Api, names, uid

ApiFactory = Callable[..., Api]
SURFACES = ("/directory", "/discover")


def test_ac001_people_who_did_not_opt_in_never_appear(api: ApiFactory) -> None:
    sam = api("sam")
    for path in SURFACES:
        shown = names(sam.ok("GET", path)["people"])
        assert {"Nina", "Tom", "Chris", "Ada (Admin)"}.isdisjoint(shown), path
        assert "Sam" not in shown  # never yourself
        assert {"Mei", "Ravi", "Ken"} <= shown


def test_ac005_a_block_hides_both_people_everywhere(api: ApiFactory) -> None:
    mei, ken = api("mei"), api("ken")
    for path in SURFACES:
        assert "Ken" not in names(mei.ok("GET", path)["people"])
        assert "Mei" not in names(ken.ok("GET", path)["people"])
    # requests are rejected both ways, and look the same as "no such person"
    assert ken.error("POST", "/requests", 404, {"recipient_id": uid("mei")})["code"] == "not_found"
    assert mei.error("POST", "/requests", 404, {"recipient_id": uid("ken")})["code"] == "not_found"
    # the blocked person cannot see the block or the report
    assert ken.ok("GET", "/blocks") == []
    assert ken.error("GET", "/admin/reports", 403)
    assert [b["person"]["display_name"] for b in mei.ok("GET", "/blocks")] == ["Ken"]
    # unblocking restores visibility
    assert mei.delete(f"/blocks/{uid('ken')}").status_code == 204
    assert "Ken" in names(mei.ok("GET", "/directory")["people"])


def test_blocking_closes_requests_and_hides_shared_contacts(api: ApiFactory) -> None:
    sam, lily = api("sam"), api("lily")
    conn = uid("conn-sam-lily")
    lily.ok("PUT", f"/contact-shares/{conn}", {"share": True})
    assert sam.ok("GET", f"/connections/{conn}")["their_contact"]["email"] == "lily@example.test"
    lily.ok("POST", "/blocks", {"user_id": uid("sam")}, status=201)
    assert sam.ok("GET", f"/connections/{conn}")["their_contact"] is None  # US-010 AC2
    assert lily.ok("GET", f"/connections/{conn}")["their_contact"] is None
    mei = api("mei")
    assert len(mei.ok("GET", "/requests")["incoming"]) == 1
    mei.ok("POST", "/blocks", {"user_id": uid("ravi")}, status=201)
    assert mei.ok("GET", "/requests")["incoming"] == []


def test_ac019_matching_only_fields_never_reach_other_participants(api: ApiFactory) -> None:
    """Mei keeps `challenges` Private: matching; Lily keeps `faith_context` private."""
    own = api("mei").ok("GET", "/me/profile")
    assert own["challenges"] == ["cash_flow", "pricing"]
    assert own["visibility"]["challenges"] == "matching_only"
    sam = api("sam")
    for path in SURFACES:
        cards = {c["display_name"]: c for c in sam.ok("GET", path)["people"]}
        assert cards["Mei"]["challenges"] == []
        assert cards["Mei"]["interests"] == ["marketing", "branding"]
        assert cards["Lily"]["faith_context"] is None
        assert cards["Grace"]["faith_context"] == "Christian"  # she chose to show it
    # a filter on a hidden field must not reveal it by matching
    by_challenge = sam.ok("GET", "/discover", params={"challenges": "cash_flow"})
    assert "Mei" not in names(by_challenge["people"]) and "Dee" in names(by_challenge["people"])
    # no participant-facing payload carries contact details (MN-002, NFR-002)
    for path in ("/directory", "/discover", "/requests", "/circles"):
        assert "example.test" not in json.dumps(sam.ok("GET", path))


def test_filters_match_every_applied_filter(api: ApiFactory) -> None:
    """MD-004, US-005."""
    sam = api("sam")
    both = sam.ok("GET", "/discover", params={"stage": "new", "interests": ["sales", "marketing"]})
    assert names(both["people"]) == {"Ken"}
    assert names(sam.ok("GET", "/discover", params={"area": "new_territories"})["people"]) == {
        "Ravi",
        "Dee",
    }
    assert (
        sam.ok("GET", "/discover", params={"interests": "exports", "stage": "new"})["people"] == []
    )
    faith = sam.ok("GET", "/discover", params={"circle_faith_tagged": True})["circles"]
    assert [c["name"] for c in faith] == ["Faith & Work Circle"]
    assert sam.http.get("/discover", params={"faith": "Christian"}).status_code == 200  # ignored


def test_requests_dedupe_and_never_auto_accept(api: ApiFactory) -> None:
    """US-007, PRD-v0 T04."""
    ravi, mei = api("ravi"), api("mei")
    again = ravi.ok("POST", "/requests", {"recipient_id": uid("mei")}, status=201)
    assert again["id"] == uid("req-ravi-mei")  # same request, no duplicate
    reverse = mei.error("POST", "/requests", 409, {"recipient_id": uid("ravi")})
    assert reverse["code"] == "request_already_received"
    assert mei.ok("GET", "/connections") == []  # nothing was accepted on anyone's behalf
    # only visible people can be asked: Tom is not listed and shares no event list with Ravi
    assert ravi.error("POST", "/requests", 404, {"recipient_id": uid("tom")})["code"] == "not_found"
    assert ravi.error("POST", "/requests", 422, {"recipient_id": uid("ravi")})
    # withdrawing removes it from the recipient's view
    assert ravi.delete(f"/requests/{uid('req-ravi-mei')}").status_code == 204
    assert mei.ok("GET", "/requests")["incoming"] == []


def test_ac003_only_the_recipient_can_answer_a_request(api: ApiFactory) -> None:
    rid = uid("req-ravi-mei")
    assert api("ravi").error("POST", f"/requests/{rid}/accept", 403)["code"] == "forbidden"
    assert api("ravi").error("POST", f"/requests/{rid}/decline", 403)["code"] == "forbidden"
    for outsider in ("sam", "ada", "felix", "olivia"):
        assert api(outsider).error("POST", f"/requests/{rid}/accept", 404)["code"] == "not_found"
        assert api(outsider).error("DELETE", f"/requests/{rid}", 404)["code"] == "not_found"
    mei = api("mei")
    assert mei.error("DELETE", f"/requests/{rid}", 403)  # the recipient cannot withdraw it
    conn = mei.ok("POST", f"/requests/{rid}/accept")
    assert conn["person"]["display_name"] == "Ravi"
    assert conn["their_contact"] is None and conn["contact_sharing"] == {
        "mine": False,
        "theirs": False,
    }
    assert mei.error("POST", f"/requests/{rid}/accept", 404)  # already answered


def test_a_decline_is_never_revealed_to_the_sender(api: ApiFactory) -> None:
    """US-008 AC3 with the OQ-06 default: the sender keeps seeing "sent"."""
    dee, sam = api("dee"), api("sam")
    outgoing = dee.ok("GET", "/requests")["outgoing"]
    assert [r["person"]["display_name"] for r in outgoing] == ["Sam"]
    card = {c["display_name"]: c for c in dee.ok("GET", "/directory")["people"]}["Sam"]
    assert card["relationship"]["status"] == "request_sent"
    assert sam.ok("GET", "/requests")["incoming"] == []
    # asking again does not pester the person who declined
    dee.ok("POST", "/requests", {"recipient_id": uid("sam")}, status=201)
    assert sam.ok("GET", "/requests")["incoming"] == []
    assert "declined" not in json.dumps(dee.ok("GET", "/requests"))


def test_ac004_contacts_need_both_grants_and_revoke_hides_them(api: ApiFactory) -> None:
    sam, lily = api("sam"), api("lily")
    conn = uid("conn-sam-lily")
    for viewer in (sam, lily):  # only Sam has granted
        assert viewer.ok("GET", f"/connections/{conn}")["their_contact"] is None
        assert "example.test" not in json.dumps(viewer.ok("GET", "/connections"))
    assert lily.ok("GET", f"/connections/{conn}")["contact_sharing"] == {
        "mine": False,
        "theirs": True,
    }
    both = lily.ok("PUT", f"/contact-shares/{conn}", {"share": True})
    assert both["their_contact"]["email"] == "sam@example.test"
    assert sam.ok("GET", f"/connections/{conn}")["their_contact"]["email"] == "lily@example.test"
    sam.ok("PUT", f"/contact-shares/{conn}", {"share": False})  # either side can revoke
    assert lily.ok("GET", f"/connections/{conn}")["their_contact"] is None
    assert sam.ok("GET", f"/connections/{conn}")["their_contact"] is None


def test_ac010_no_role_or_association_opens_private_pair_data(api: ApiFactory) -> None:
    """MN-006: circle co-members, facilitators, hosts and even the admin get not-found."""
    conn = uid("conn-sam-lily")
    for outsider in ("mei", "felix", "grace", "olivia", "chris", "ada"):
        o = api(outsider)
        assert o.error("GET", f"/connections/{conn}", 404)["code"] == "not_found", outsider
        assert o.error("PUT", f"/contact-shares/{conn}", 404, {"share": True})
        assert o.error("PUT", f"/connections/{conn}/follow-ups/1", 404, {"met": True})


def test_ac013_follow_up_reports_are_idempotent_and_keep_no_report_distinct(
    api: ApiFactory,
) -> None:
    sam, lily = api("sam"), api("lily")
    path = f"/connections/{uid('conn-sam-lily')}/follow-ups"
    before = api("ada").ok("GET", "/admin/metrics")["funnel"]
    lily.ok("PUT", f"{path}/1", {"met": True, "usefulness": 5})
    lily.ok("PUT", f"{path}/1", {"met": True, "usefulness": 5})
    sam.ok("PUT", f"{path}/1", {"met": True})
    after = api("ada").ok("GET", "/admin/metrics")["funnel"]
    assert before == after  # the pair was already counted once for catch-up 1
    state = sam.ok("PUT", f"{path}/2", {"met": False})["follow_ups"]
    assert state[1]["met"] is False  # "reported no catch-up"
    second = {u["key"]: u for u in api("ada").ok("GET", "/admin/metrics")["funnel"]}
    assert second["second_catch_ups"]["count"] == 0
    mei_conn = api("mei").ok("POST", f"/requests/{uid('req-ravi-mei')}/accept")
    assert mei_conn["follow_ups"][0]["met"] is None  # "no report" is a different value
    sam.error("PUT", f"{path}/3", 422, {"met": True})


def test_reports_reach_only_the_admin(api: ApiFactory) -> None:
    receipt = api("sam").ok("POST", "/reports", {"subject_id": uid("ken"), "reason": "Spam"}, 201)
    assert set(receipt) == {"id", "created_at"}
    reports = api("ada").ok("GET", "/admin/reports")
    assert {(r["reporter"]["display_name"], r["subject"]["display_name"]) for r in reports} == {
        ("Mei", "Ken"),
        ("Sam", "Ken"),
    }
    assert all(r["created_at"] for r in reports)  # NFR-008


def test_recipient_can_decline_and_nothing_is_created(api: ApiFactory) -> None:
    """US-008: the success path of decline."""
    mei, ravi = api("mei"), api("ravi")
    assert mei.post(f"/requests/{uid('req-ravi-mei')}/decline").status_code == 204
    assert mei.ok("GET", "/requests")["incoming"] == []
    assert mei.ok("GET", "/connections") == [] and ravi.ok("GET", "/connections") == []
    assert [r["person"]["display_name"] for r in ravi.ok("GET", "/requests")["outgoing"]] == ["Mei"]
    assert mei.error("POST", f"/requests/{uid('req-ravi-mei')}/accept", 404)  # already answered
