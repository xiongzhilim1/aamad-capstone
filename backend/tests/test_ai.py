"""The two AI paths with a stand-in crew: input assembly, output checks, fallbacks, controls.

AC-007, AC-008, AC-009, AC-017, AC-018, AC-019, MN-003, MN-013, MN-015, CR-001, CR-002,
CR-006, CR-008 to CR-010, CR-013, EC-015. No test here calls a model.
"""

import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import func, select

from app.ai import controls, profile_assistant
from app.crews import runtime
from app.db.models import (
    CircleMembership,
    ConnectionRequestRow,
    ModelTrace,
    ProfileFieldRow,
)
from app.db.session import new_session
from app.settings import get_settings
from tests.helpers import Api, uid

ApiFactory = Callable[..., Api]
FakeCrew = Callable[..., list[dict[str, Any]]]


def payload_of(calls: list[dict[str, Any]]) -> dict[str, Any]:
    text = calls[-1]["inputs"]["payload"].replace("(", "{").replace(")", "}")
    data: dict[str, Any] = json.loads(text)
    return data


def suggest_all(reason: str = "You both care about marketing.") -> Callable[[dict[str, str]], Any]:
    """A fake model that suggests every candidate, citing `interests`, plus an invented id."""

    def output(inputs: dict[str, str]) -> dict[str, Any]:
        data = json.loads(inputs["payload"].replace("(", "{").replace(")", "}"))
        items = [
            {
                "candidate_id": p["id"],
                "kind": "person",
                "reason": reason,
                "cited_fields": ["interests"],
            }
            for p in data["people"]
        ]
        items.append({"candidate_id": "p77", "kind": "person", "reason": reason,
                      "cited_fields": ["interests"]})  # fmt: skip
        return {"items": items}

    return output


def traces() -> list[ModelTrace]:
    with new_session() as db:
        return list(db.scalars(select(ModelTrace).order_by(ModelTrace.created_at)))


def test_ac007_suggestions_are_eligible_grounded_and_change_no_state(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(suggest_all())
    mei = api("mei")
    with new_session() as db:
        before = (
            db.scalar(select(func.count()).select_from(ConnectionRequestRow)),
            db.scalar(select(func.count()).select_from(CircleMembership)),
        )
    body = mei.ok("POST", "/suggestions")
    assert body["status"] == "ok" and body["fallback"] is None and len(calls) == 1
    shown = {i["person"]["display_name"] for i in body["items"]}
    # eligible = listed, not Mei, not blocked (Ken), so never Nina/Tom/Chris/Ada/Ken
    assert shown <= {"Olivia", "Felix", "Grace", "Ravi", "Sam", "Lily", "Dee"}
    assert shown.isdisjoint({"Mei", "Ken", "Nina", "Tom", "Chris", "Ada (Admin)"})
    with new_session() as db:
        after = (
            db.scalar(select(func.count()).select_from(ConnectionRequestRow)),
            db.scalar(select(func.count()).select_from(CircleMembership)),
        )
    assert before == after  # MN-003: the AI path has no write path


def test_cr001_cr002_only_eligible_people_and_allowlisted_fields_reach_the_prompt(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(suggest_all())
    api("sam").ok("POST", "/suggestions")
    data = payload_of(calls)
    raw = calls[-1]["inputs"]["payload"]
    assert len(data["people"]) == 7  # 9 listed - Sam - Lily (already connected)
    assert len(data["people"]) <= 50 and len(data["circles"]) <= 20
    # no names, ids, contact details or consent state (MD-021, CR-002)
    for forbidden in ("Mei", "Ravi", "Olivia", "example.test", "WhatsApp", uid("mei"), "listed",
                      "block", "display_name"):  # fmt: skip
        assert forbidden not in raw, forbidden
    allowed = {"stage", "looking_for", "interests", "challenges", "industry", "summary", "area",
               "meeting_mode", "time_windows", "faith_context"}  # fmt: skip
    for person in data["people"]:
        assert set(person) <= {"id", "citable", "rank_only"}
        assert set(person["citable"]) | set(person.get("rank_only", {})) <= allowed
    # CR-015: Mei's matching-only challenges are in rank_only, never citable
    mei = next(p for p in data["people"] if p["citable"].get("industry") == "food_beverage"
               and p["citable"]["stage"] == "new")  # fmt: skip
    assert mei["rank_only"] == {"challenges": ["cash_flow", "pricing"]}
    assert "challenges" not in mei["citable"]
    # circles: Sam is already in Founders' Table; the faith circle needs his opt-in
    assert data["circles"] == []


def test_ac008_faith_reaches_the_prompt_only_with_both_opt_ins(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(suggest_all())
    api("mei").ok("POST", "/suggestions")  # Mei has no faith context and no opt-in
    raw = calls[-1]["inputs"]["payload"]
    assert "faith" not in raw.lower() and "Christian" not in raw
    api("grace").ok("POST", "/suggestions")  # Grace opted in; only Lily also did
    data = payload_of(calls)
    assert data["viewer"]["faith_context"] == "Christian"
    with_faith = [p for p in data["people"] if "faith_context" in json.dumps(p)]
    assert len(with_faith) == 1 and with_faith[0]["rank_only"] == {"faith_context": "Christian"}
    # a faith reason for someone without both opt-ins is dropped before display
    fake_crew(suggest_all("You both like marketing and share a strong Christian faith."))
    body = api("mei").ok("POST", "/suggestions")
    assert body["status"] == "fallback" and body["fallback"]["code"] == "ai_unavailable"
    assert body["filter_results"]["people"]


def test_guardrail_drops_are_invisible_to_the_user_but_logged(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    fake_crew(suggest_all())
    body = api("ravi").ok("POST", "/suggestions")
    assert body["status"] == "ok" and "dropped" not in json.dumps(body)  # ux.md Partial state
    trace = traces()[-1]
    assert trace.outcome == "ok" and trace.crew == "suggestion" and trace.task_id == "suggest_v1"
    assert "unknown:id_not_in_input_set" in trace.dropped
    assert trace.model == "claude-sonnet-5-5" and trace.effort == "low" and trace.model_calls == 1
    assert all(i.startswith(("p", "c")) and len(i) == 3 for i in trace.input_ids + trace.output_ids)
    log = Path(get_settings().trace_log_dir) / "model-traces.jsonl"
    line = json.loads(log.read_text().splitlines()[-1])
    assert line["trace_id"] == body["trace_id"] and line["cost_usd"] == 0.01
    assert "marketing" not in json.dumps(line)  # CR-013: ids and counts, never content


def test_cr006_eligibility_is_rechecked_after_the_call(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    """Someone opts out while the model call is running: they are not shown."""
    felix = api("felix")

    def felix_opts_out() -> None:
        felix.ok("PUT", "/me/directory-consent", {"listed": False})

    fake_crew(suggest_all(), before_return=felix_opts_out)
    body = api("ravi").ok("POST", "/suggestions")
    assert "Felix" not in {i["person"]["display_name"] for i in body["items"]}
    assert any(d.endswith(":no_longer_eligible") for d in traces()[-1].dropped)


@pytest.mark.parametrize("failure", ["timeout", "schema", "refusal", "error"])
def test_ac009_any_model_failure_falls_back_to_filters(
    api: ApiFactory, fake_crew: FakeCrew, failure: str
) -> None:
    """MC-005, EC-015: a clear message, filter results, and discovery still works."""
    fake_crew(failure=failure)
    mei = api("mei")
    body = mei.ok("POST", "/suggestions")
    assert body["status"] == "fallback" and body["items"] == []
    assert body["fallback"]["code"] == ("ai_timeout" if failure == "timeout" else "ai_unavailable")
    assert body["fallback"]["message"] and body["filter_results"]["people"]
    assert "Ken" not in {p["display_name"] for p in body["filter_results"]["people"]}
    assert mei.ok("GET", "/discover")["people"]
    assert traces()[-1].outcome == "fallback"


def test_cr010_rate_limit_is_ten_per_hour_per_user_and_action(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(suggest_all())
    mei = api("mei")
    for _ in range(10):
        assert mei.ok("POST", "/suggestions")["status"] == "ok"
    limited = mei.ok("POST", "/suggestions")
    assert limited["fallback"]["code"] == "rate_limited" and limited["fallback"]["retry_at"]
    assert limited["filter_results"]["people"] and len(calls) == 10  # no eleventh model call
    assert api("ravi").ok("POST", "/suggestions")["status"] == "ok"  # per user


def test_cr010_spend_cap_switches_ai_off(api: ApiFactory, fake_crew: FakeCrew) -> None:
    calls = fake_crew(suggest_all(), cost=19.99)
    assert api("mei").ok("POST", "/suggestions")["status"] == "ok"
    calls2 = fake_crew(suggest_all(), cost=0.02)
    assert api("ravi").ok("POST", "/suggestions")["status"] == "ok"  # 19.99 < 20
    off = api("sam").ok("POST", "/suggestions")
    assert off["fallback"]["code"] == "ai_budget_exhausted" and len(calls) + len(calls2) == 2
    draft = api("sam").ok("POST", "/me/profile/draft", {"text": "I sell tea."})
    assert draft["status"] == "fallback" and draft["fallback"]["code"] == "ai_budget_exhausted"
    health = api("ada").ok("GET", "/admin/metrics")["ai"]
    assert health["ai_enabled"] is False and health["spend_usd"] == pytest.approx(20.01)
    with new_session() as db:
        assert db.scalar(select(func.sum(ModelTrace.cost_usd))) == Decimal("20.010000")


def test_circuit_breaker_opens_after_five_consecutive_failures(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(failure="error")
    for persona in ("mei", "ravi", "sam", "dee", "felix"):
        api(persona).ok("POST", "/suggestions")
    assert controls.breaker.is_open()
    api("grace").ok("POST", "/suggestions")
    assert len(calls) == 5  # the sixth request made no model call


def test_missing_api_key_fails_closed_without_a_call(
    api: ApiFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    try:
        body = api("mei").ok("POST", "/suggestions")  # the default stub would raise if called
        assert body["fallback"]["code"] == "ai_unavailable"
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


TEXT = "I run a small bakery. Getting new customers is hard. I'd love a mentor. I go to church."
DRAFT = {
    "interests": [{"tag": "marketing", "evidence": "new customers"}],
    "challenges": [{"tag": "finding_customers", "evidence": "Getting new customers is hard"}],
    "looking_for": [{"tag": "mentor", "evidence": "I'd love a mentor"},
                    {"tag": "fellowship", "evidence": "I go to church"}],
    "industry": {"tag": "food_beverage", "evidence": "small bakery"},
    "summary": "Runs a small bakery and wants a mentor.",
}  # fmt: skip


def fields_of(persona: str) -> dict[str, Any]:
    with new_session() as db:
        rows = db.scalars(select(ProfileFieldRow).where(ProfileFieldRow.user_id == uid(persona)))
        return {r.field: (r.value, r.visibility) for r in rows}


def test_ac017_ac018_draft_saves_nothing_until_accepted(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    calls = fake_crew(DRAFT)
    tom = api("tom")
    before = fields_of("tom")
    body = tom.ok("POST", "/me/profile/draft", {"text": TEXT})
    assert body["status"] == "draft" and len(calls) == 1
    assert body["draft"] == {
        "interests": ["marketing"],
        "challenges": ["finding_customers"],
        "looking_for": ["mentor"],
        "industry": "food_beverage",
        "summary": "Runs a small bakery and wants a mentor.",
    }  # fmt: skip  (AC-018: the church-based tag is gone)
    assert fields_of("tom") == before  # MN-013: nothing saved
    # the model sees only the author's text and the vocabulary (SAD minimum data)
    assert set(calls[0]["inputs"]) == {
        "text",
        "interests",
        "challenges",
        "looking_for",
        "industries",
    }
    assert tom.ok("GET", "/me/profile/draft")["source_text"] == TEXT
    assert api("mei").error("GET", "/me/profile/draft", 404)  # MN-015: private to its author
    # the author edits, then accepts only some fields, choosing visibility
    accepted = tom.ok(
        "POST",
        "/me/profile/draft/accept",
        {"challenges": ["finding_customers", "pricing"], "looking_for": ["mentor"],
         "summary": "Runs a small bakery.", "visibility": {"challenges": "matching_only"}},
    )  # fmt: skip
    assert accepted["challenges"] == ["finding_customers", "pricing"]
    assert accepted["visibility"]["challenges"] == "matching_only"
    assert accepted["interests"] == ["product"]  # not submitted, so not touched
    assert accepted["industry"] is None  # drafted but not accepted, so not saved
    assert accepted["directory_listed"] is False  # MN-016
    # raw text is deleted on accept, and was never stored in the database
    tom.error("GET", "/me/profile/draft", 404)
    assert profile_assistant.store.get(tom.ok("GET", "/session") and "x") is None
    with new_session() as db:
        dump = json.dumps([[str(c) for c in row] for row in db.execute(
            select(ProfileFieldRow.value)).all()])  # fmt: skip
    assert "I go to church" not in dump and "Getting new customers" not in dump
    assert traces()[-1].review_outcome == "accepted"
    assert tom.error("POST", "/me/profile/draft/accept", 404, {"interests": ["sales"]})


def test_draft_discard_and_sign_out_delete_the_raw_text(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    fake_crew(DRAFT)
    tom = api("tom")
    before = fields_of("tom")
    tom.ok("POST", "/me/profile/draft", {"text": TEXT})
    assert tom.delete("/me/profile/draft").status_code == 204
    tom.error("GET", "/me/profile/draft", 404)
    assert fields_of("tom") == before and traces()[-1].review_outcome == "discarded"
    tom.ok("POST", "/me/profile/draft", {"text": TEXT})
    tom.delete("/session")
    tom.login("tom")
    tom.error("GET", "/me/profile/draft", 404)


def test_assistant_input_cap_and_fallback_to_manual(api: ApiFactory, fake_crew: FakeCrew) -> None:
    """CR-003, MC-006."""
    tom = api("tom")
    too_long = tom.error("POST", "/me/profile/draft", 422, {"text": "x" * 1501})
    assert too_long["fields"][0]["field"] == "text"  # rejected before any model call
    fake_crew(failure="timeout")
    body = tom.ok("POST", "/me/profile/draft", {"text": TEXT})
    assert body["status"] == "fallback" and body["fallback"]["code"] == "ai_timeout"
    assert (
        body["source_text"] == TEXT and body["draft"] is None
    )  # the text is kept for manual entry
    saved = tom.ok("POST", "/me/profile/draft/accept", {"interests": ["sales"]})
    assert saved["interests"] == ["sales"]  # manual tags still save


def test_ac019_raw_text_and_other_peoples_data_never_reach_the_other_model(
    api: ApiFactory, fake_crew: FakeCrew
) -> None:
    """MN-015: the suggestion prompt holds accepted fields only, never anyone's free text."""
    fake_crew(DRAFT)
    dee = api("dee")
    secret = "I owe my supplier money. " + TEXT
    dee.ok("POST", "/me/profile/draft", {"text": secret})
    calls = fake_crew(suggest_all())
    api("sam").ok("POST", "/suggestions")
    api("dee").ok("POST", "/suggestions")
    for call in calls:
        assert "supplier" not in call["inputs"]["payload"]


def test_cr008_crews_have_no_tools_and_bad_config_refuses_to_boot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime.validate_config()  # the shipped config is valid
    agents, tasks = runtime.load_config()
    assert set(agents) == {"peer_matcher", "profile_drafter"}
    assert set(tasks) == {"suggest_v1", "draft_profile_v1"}
    for cfg in agents.values():
        assert cfg["allow_delegation"] is False and cfg["max_iter"] <= 2
        assert cfg["max_retry_limit"] >= 2 and cfg["max_execution_time"] == 20
        assert "tools" not in cfg and "temperature" not in cfg and "llm" not in cfg
    assert "temperature" not in (runtime.CONFIG_DIR / "agents.yaml").read_text().split("#")[0]
    for name, patch in (
        ("agents.yaml", {"tools": ["web_search"]}),
        ("agents.yaml", {"allow_delegation": True}),
        ("agents.yaml", {"temperature": 0.2}),
        ("agents.yaml", {"max_iter": 12}),
        ("tasks.yaml", {"tools": ["db_write"]}),
    ):
        for source in ("agents.yaml", "tasks.yaml"):
            data = yaml.safe_load((runtime.CONFIG_DIR / source).read_text())
            if source == name:
                data[next(iter(data))].update(patch)
            (tmp_path / source).write_text(yaml.safe_dump(data))
        monkeypatch.setattr(runtime, "CONFIG_DIR", tmp_path)
        runtime.load_config.cache_clear()
        with pytest.raises(runtime.CrewConfigError):
            runtime.validate_config()
    monkeypatch.undo()
    runtime.load_config.cache_clear()


def test_cost_is_computed_from_usage() -> None:
    stats = runtime.CallStats(input_tokens=1000, output_tokens=2000, cache_read_tokens=4000,
                              cache_write_tokens=1000)  # fmt: skip
    # sonnet: 1000*2 + 1000*2*1.25 + 4000*0.10 + 2000*10 = 24,900 micro-dollars per million
    assert runtime.cost_usd("claude-sonnet-5-5", stats) == pytest.approx(0.0249)
    assert runtime.cost_usd("claude-haiku-5-5", stats) == pytest.approx(0.001265)


def test_transport_hook_adds_effort_drops_temperature_and_reads_usage() -> None:
    """OQ-A03: CrewAI has no effort setting, so the request hook adds it. The response hook
    gets a response with no request attached, and must not depend on one."""
    import httpx

    stats = runtime.CallStats()
    hook = runtime._Transport("low", stats)
    body = {"model": "claude-sonnet-5-5", "temperature": 0.2, "messages": [], "system": "s"}
    sent = hook.on_outbound(
        httpx.Request("POST", "https://api.anthropic.com/v1/messages", json=body)
    )
    out = json.loads(sent.content)
    assert out["output_config"] == {"effort": "low"} and "temperature" not in out
    assert int(sent.headers["content-length"]) == len(sent.content)
    reply = {"stop_reason": "end_turn", "usage": {"input_tokens": 7, "output_tokens": 9,
                                                   "cache_read_input_tokens": 100}}  # fmt: skip
    hook.on_inbound(httpx.Response(200, json=reply))  # no request attached
    assert (stats.model_calls, stats.stop_reason, stats.input_tokens, stats.output_tokens) == (
        1, "end_turn", 7, 9,
    )  # fmt: skip
    assert stats.cache_read_tokens == 100 and stats.prompt_sha256
    # token counting passes through untouched and is not counted as a model call
    count = httpx.Request("POST", "https://api.anthropic.com/v1/messages/count_tokens", json=body)
    assert hook.on_outbound(count) is count and stats.model_calls == 1
    hook.on_inbound(httpx.Response(200, json={"input_tokens": 5}))
    assert stats.input_tokens == 7
