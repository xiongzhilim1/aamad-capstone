"""US-001, US-002, US-003, US-023: session identity, profile rules, directory consent."""

from collections.abc import Callable

from app.security import SESSION_COOKIE, SessionData, encode_session
from tests.helpers import Api, names, uid

ApiFactory = Callable[..., Api]


def test_demo_code_gates_the_persona_picker(api: ApiFactory) -> None:
    anon = api()
    assert anon.error("GET", "/session/personas", 403)["code"] == "demo_access_required"
    assert anon.error("POST", "/session/persona", 403, {"persona_id": uid("ada")})["code"] == (
        "demo_access_required"
    )
    wrong = anon.error("POST", "/session/demo-access", 403, {"access_code": "nope"})
    assert wrong["code"] == "access_code_invalid"
    assert anon.ok("GET", "/session") == {"demo_access": False, "user": None}
    anon.ok("POST", "/session/demo-access", {"access_code": "test-demo-code"})
    personas = anon.ok("GET", "/session/personas")
    roles = {r for p in personas for r in p["roles"]}
    assert roles == {"participant", "organiser", "facilitator", "admin"}  # MD-017
    assert {p["stage"] for p in personas} == {"seasoned", "new", "aspiring"}


def test_wrong_access_codes_are_rate_limited(api: ApiFactory) -> None:
    anon = api()
    for _ in range(10):
        anon.error("POST", "/session/demo-access", 403, {"access_code": "guess"})
    limited = anon.error("POST", "/session/demo-access", 429, {"access_code": "test-demo-code"})
    assert limited["code"] == "rate_limited" and limited["retry_at"]


def test_actor_comes_from_the_session_never_from_input(api: ApiFactory) -> None:
    """MN-011, CR-011, EC-016: a forged actor id is rejected or ignored on every channel."""
    mei = api("mei")
    assert mei.ok("GET", "/session")["user"]["display_name"] == "Mei"
    # in the body: unknown keys are refused
    assert mei.error("PUT", "/me/directory-consent", 422, {"listed": False, "user_id": uid("ken")})
    # in the query or a header: ignored, the session actor is used
    profile = mei.http.get(
        "/me/profile", params={"user_id": uid("ken")}, headers={"x-user-id": uid("ken")}
    )
    assert profile.json()["display_name"] == "Mei"
    # a cookie signed with another key, or edited, is not a session
    forged = api()
    forged.http.cookies.set(SESSION_COOKIE, encode_session(SessionData("x", True, None, 1)))
    assert forged.error("GET", "/me/profile", 401)["code"] == "not_signed_in"
    real = mei.http.cookies.get(SESSION_COOKIE)
    assert real is not None
    tampered = api()
    tampered.http.cookies.set(SESSION_COOKIE, real[:-2] + ("00" if real[-2:] != "00" else "11"))
    assert tampered.error("GET", "/me/profile", 401)["code"] == "not_signed_in"
    assert api().error("GET", "/directory", 401)["code"] == "not_signed_in"


def test_non_admin_cannot_reach_admin_endpoints(api: ApiFactory) -> None:
    for persona in ("mei", "olivia", "felix"):
        for path in (
            "/admin/reports",
            "/admin/events/queue",
            "/admin/metrics",
            "/admin/access-log",
        ):
            assert api(persona).error("GET", path, 403)["code"] == "forbidden"


def test_sign_out_ends_the_persona_session(api: ApiFactory) -> None:
    mei = api("mei")
    assert mei.delete("/session").status_code == 204
    assert mei.ok("GET", "/session") == {"demo_access": True, "user": None}
    mei.error("GET", "/me/profile", 401)


def test_profile_requires_a_valid_stage_and_nothing_else(api: ApiFactory) -> None:
    """MD-001, MN-012."""
    tom = api("tom")
    assert tom.error("PUT", "/me/profile", 422, {"display_name": "Tom"})["fields"][0]["field"] == (
        "stage"
    )
    tom.error("PUT", "/me/profile", 422, {"display_name": "Tom", "stage": "expert"})
    tom.error("PUT", "/me/profile", 422, {"display_name": "Tom", "stage": "new", "address": "1 Rd"})
    too_long = {"display_name": "Tom", "stage": "new", "summary": "x" * 201}
    assert tom.error("PUT", "/me/profile", 422, too_long)["fields"][0]["field"] == "summary"
    bad_tag = {"display_name": "Tom", "stage": "new", "interests": ["world_domination"]}
    tom.error("PUT", "/me/profile", 422, bad_tag)
    saved = tom.ok("PUT", "/me/profile", {"display_name": "Tom", "stage": "new"})
    assert saved["stage"] == "new" and saved["interests"] == []
    assert saved["faith_matching_opt_in"] is False  # MN-004 default
    assert saved["visibility"]["faith_context"] == "matching_only"


def test_saving_a_profile_or_finishing_onboarding_never_changes_consent(api: ApiFactory) -> None:
    """MN-001, MN-016, AC-016: directory consent has exactly one writer."""
    tom = api("tom")
    body = {"display_name": "Tom", "stage": "aspiring", "interests": ["product"],
            "onboarding_completed": True}  # fmt: skip
    saved = tom.ok("PUT", "/me/profile", body)
    assert saved["directory_listed"] is False and saved["onboarding_completed"] is True
    assert "Tom" not in names(api("sam").ok("GET", "/directory")["people"])
    assert tom.ok("PUT", "/me/directory-consent", {"listed": True})["directory_listed"] is True
    assert "Tom" in names(api("sam").ok("GET", "/directory")["people"])
    # opting out takes effect on the next load, and existing connections are unaffected
    lily = api("lily")
    lily.ok("PUT", "/me/directory-consent", {"listed": False})
    assert "Lily" not in names(api("mei").ok("GET", "/directory")["people"])
    assert len(lily.ok("GET", "/connections")) == 1


def test_vocabulary_lists_the_closed_tag_sets(api: ApiFactory) -> None:
    vocab = api("mei").ok("GET", "/vocabulary")
    assert {"value": "cash_flow", "label": "Cash flow"} in vocab["challenges"]
    assert vocab["limits"]["free_text_max"] == 1500 and vocab["limits"]["summary_max"] == 200
