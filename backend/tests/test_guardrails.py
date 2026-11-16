"""W08 and W22 against crafted model outputs (SAD §9 guardrail fault injection).

CR-006, CR-007, CR-015, AC-007, AC-008, AC-018, EC-003 to EC-008. No model is involved.
"""

from typing import Any

from app.ai.guardrails import (
    CircleContext,
    PersonContext,
    SuggestionContext,
    check_draft,
    check_suggestions,
    mentions_faith,
    mentions_sensitive,
)
from app.ai.schemas import ProfileDraftOut, SuggestionResult

CTX = SuggestionContext(
    viewer_fields={"stage": "new", "interests": ["marketing"], "challenges": ["cash_flow"],
                   "industry": "food_beverage"},
    people={
        "p01": PersonContext(
            citable={"stage": "seasoned", "interests": ["marketing", "sales"]},
            rank_only={"challenges": ["cash_flow"], "summary": "Recovering from a failed launch"},
        ),
        "p02": PersonContext(
            citable={"stage": "new", "interests": ["marketing"], "faith_context": "Christian"},
            faith_allowed=True,
        ),
        "p03": PersonContext(citable={"stage": "new", "industry": "food_beverage"}),
    },
    circles={
        "c01": CircleContext({"purpose": "Owners compare notes", "tags": ["cash_flow"]}),
        "c02": CircleContext({"purpose": "Work and purpose", "tags": ["leadership"],
                              "faith_context": "Christian"}, faith_allowed=True),
    },
)  # fmt: skip


def item(cid: str, reason: str, cited: list[str], kind: str = "person") -> dict[str, Any]:
    return {"candidate_id": cid, "kind": kind, "reason": reason, "cited_fields": cited}


def run(*items: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    checked = check_suggestions(SuggestionResult.model_validate({"items": list(items)}), CTX)
    return [s.candidate_id for s in checked.value], {d.item: d.reason for d in checked.dropped}


def test_grounded_eligible_suggestions_pass_in_order() -> None:
    kept, dropped = run(
        item(
            "p01", "You both care about marketing and they have years of experience.", ["interests"]
        ),
        item("c01", "This circle compares notes on cash flow.", ["tags"], "circle"),
        item("p03", "You both work in food and beverage.", ["industry"]),
    )
    assert kept == ["p01", "c01", "p03"] and dropped == {}


def test_ids_outside_the_input_set_and_duplicates_are_dropped() -> None:
    kept, dropped = run(
        item("p99", "Invented person.", ["interests"]),
        item("c01", "A circle id used as a person.", ["interests"]),
        item("p01", "You both care about marketing.", ["interests"]),
        item("p01", "Again.", ["interests"]),
    )
    assert kept == ["p01"]
    assert dropped == {"unknown": "id_not_in_input_set", "p01": "duplicate"}


def test_every_cited_field_must_exist_and_be_citable_on_both_sides() -> None:
    _, dropped = run(item("p03", "You share an interest in marketing.", ["interests"]))
    assert dropped == {"p03": "field_not_citable"}  # p03 has no public interests
    _, dropped = run(item("p01", "You both face cash flow pressure.", ["challenges"]))
    assert dropped == {"p01": "field_not_citable"}  # matching-only on the candidate (CR-015)
    _, dropped = run(item("p02", "You both like long meetings.", ["meeting_mode"]))
    assert dropped == {"p02": "field_not_citable"}
    _, dropped = run(item("p01", "They are great.", []))
    assert dropped == {"p01": "no_cited_field"}
    _, dropped = run(item("p01", "They have a nice email.", ["contact_email"]))
    assert dropped == {"p01": "unknown_field"}
    viewer_lacks = SuggestionContext({"stage": "new"}, CTX.people, CTX.circles)
    checked = check_suggestions(
        SuggestionResult.model_validate(
            {"items": [item("p01", "You share an interest in marketing.", ["interests"])]}
        ),
        viewer_lacks,
    )
    assert [d.reason for d in checked.dropped] == ["field_not_shared"]


def test_cr015_matching_only_values_never_appear_in_a_reason() -> None:
    for reason in (
        "You both like marketing, and they also struggle with cash flow.",
        "Marketing fan who knows about Cash Flow.",
        "Marketing fan; tag cash_flow applies.",
        "Likes marketing and is recovering from a failed project.",
    ):
        kept, dropped = run(item("p01", reason, ["interests"]))
        assert kept == [] and dropped == {"p01": "rank_only_leak"}, reason


def test_faith_reasons_need_both_opt_ins() -> None:
    """AC-008, MN-004, EC-006."""
    kept, dropped = run(
        item("p01", "You both like marketing and may share Christian values.", ["interests"]),
        item("p03", "You both work in food and could pray together.", ["industry"]),
        item("c01", "A church-friendly circle about cash flow.", ["tags"], "circle"),
        item("p02", "You both like marketing and share a Christian faith.", ["interests"]),
        item("c02", "A Christian circle about work and purpose.", ["purpose"], "circle"),
    )
    assert kept == ["p02", "c02"]
    assert set(dropped.values()) == {"faith_without_opt_in"}
    assert mentions_faith("They attend CHURCH weekly") and not mentions_faith(
        "good at goal setting"
    )


def test_reasons_are_capped_at_25_words_and_lists_at_10() -> None:
    long_reason = " ".join(["marketing"] * 26)
    _, dropped = run(item("p01", long_reason, ["interests"]))
    assert dropped == {"p01": "reason_length"}
    people = {f"p{i:02d}": PersonContext({"stage": "new", "interests": ["marketing"]})
              for i in range(1, 13)}  # fmt: skip
    ctx = SuggestionContext(CTX.viewer_fields, people, {})
    result = SuggestionResult.model_validate(
        {"items": [item(k, "You both like marketing.", ["interests"]) for k in people]}
    )
    checked = check_suggestions(result, ctx)
    assert len(checked.value) == 10 and {d.reason for d in checked.dropped} == {"over_limit"}


TEXT = (
    "I run a small bakery in Mong Kok. Getting new customers is hard and I never know what to "
    "charge for cakes. I'd love a mentor. My church group and my husband keep me going, and "
    "I was diagnosed with diabetes last year."
)


def draft(**over: Any) -> ProfileDraftOut:
    base: dict[str, Any] = {"interests": [], "challenges": [], "looking_for": [], "industry": None,
                            "summary": "Runs a small bakery and wants a mentor."}  # fmt: skip
    return ProfileDraftOut.model_validate(base | over)


def test_w22_keeps_tags_that_quote_the_authors_words() -> None:
    checked = check_draft(
        draft(
            challenges=[
                {"tag": "finding_customers", "evidence": "Getting new customers is hard"},
                {"tag": "pricing", "evidence": "never know what to charge"},
            ],
            looking_for=[{"tag": "mentor", "evidence": "I'd love a mentor"}],
            industry={"tag": "food_beverage", "evidence": "small bakery"},
        ),  # fmt: skip
        TEXT,
    )
    d = checked.value
    assert [t.value for t in d.challenges] == ["finding_customers", "pricing"]
    assert [t.value for t in d.looking_for] == ["mentor"] and d.industry == "food_beverage"
    assert d.summary == "Runs a small bakery and wants a mentor." and checked.dropped == []


def test_w22_drops_tags_without_a_verbatim_quote() -> None:
    """MN-014, EC-004: an invented or paraphrased-from-nothing tag does not survive."""
    checked = check_draft(
        draft(
            interests=[
                {"tag": "exports", "evidence": "wants to sell overseas"},
                {"tag": "ai_tools", "evidence": ""},
            ],
            challenges=[{"tag": "pricing", "evidence": "NEVER know   what to charge"}],
        ),  # fmt: skip
        TEXT,
    )
    assert checked.value.interests == []
    assert [t.value for t in checked.value.challenges] == [
        "pricing"
    ]  # case and spacing differ only
    assert {d.item: d.reason for d in checked.dropped} == {
        "interests:exports": "not_traceable",
        "interests:ai_tools": "not_traceable",
    }


def test_ac018_no_faith_health_or_family_content_survives() -> None:
    checked = check_draft(
        draft(
            looking_for=[
                {"tag": "fellowship", "evidence": "My church group"},
                {"tag": "peer_support", "evidence": "my husband keep me going"},
            ],
            challenges=[{"tag": "time_management", "evidence": "diagnosed with diabetes"}],
            summary="A bakery owner supported by her church and husband.",
        ),  # fmt: skip
        TEXT,
    )
    d = checked.value
    assert d.looking_for == [] and d.challenges == [] and d.summary is None
    assert {x.reason for x in checked.dropped} == {"sensitive_evidence", "sensitive"}
    assert mentions_sensitive("my daughter") and mentions_sensitive("in therapy")
    assert not mentions_sensitive("I sell family-size cakes to cafes")


def test_w22_drops_an_ungrounded_or_overlong_summary() -> None:
    invented = draft(summary="Award-winning restaurateur who raised two seed rounds in Singapore.")
    assert check_draft(invented, TEXT).value.summary is None
    assert check_draft(draft(summary="x" * 201), TEXT).value.summary is None
