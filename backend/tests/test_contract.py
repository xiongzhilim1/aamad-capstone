"""The API contract (SAD §4): the committed OpenAPI file is current and uses one error envelope."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from scripts.export_openapi import render

SPEC = app.openapi()
ENVELOPE = "#/components/schemas/ErrorEnvelope"


def test_openapi_file_is_current() -> None:
    target = Path(__file__).resolve().parent.parent / "openapi.json"
    assert target.read_text() == render(), "run `uv run python scripts/export_openapi.py`"


def test_operation_ids_are_unique_and_readable() -> None:
    ids = [op["operationId"] for path in SPEC["paths"].values() for op in path.values()]
    assert len(ids) == len(set(ids))
    assert "send_request" in ids and all("_post" not in i[-5:] for i in ids)


def test_every_error_response_uses_the_envelope() -> None:
    for path, item in SPEC["paths"].items():
        for method, op in item.items():
            for status, response in op["responses"].items():
                if status.startswith("2"):
                    continue
                schema = response["content"]["application/json"]["schema"]
                assert schema == {"$ref": ENVELOPE}, f"{method} {path} {status}"


def test_sad_section_4_endpoints_are_declared() -> None:
    expected = {
        ("post", "/session/persona"), ("delete", "/session"),
        ("get", "/me/profile"), ("put", "/me/profile"), ("post", "/me/profile/draft"),
        ("post", "/me/profile/draft/accept"), ("delete", "/me/profile/draft"),
        ("get", "/directory"), ("get", "/discover"), ("post", "/suggestions"),
        ("post", "/requests"), ("delete", "/requests/{request_id}"),
        ("post", "/requests/{request_id}/accept"), ("post", "/requests/{request_id}/decline"),
        ("put", "/contact-shares/{connection_id}"), ("post", "/blocks"), ("post", "/reports"),
        ("get", "/circles"), ("post", "/circles/{circle_id}/join"),
        ("delete", "/circles/{circle_id}/membership"),
        ("post", "/circles/{circle_id}/applications/{user_id}/approve"),
        ("get", "/circles/{circle_id}/members/{user_id}/matching-fields"),
        ("post", "/events"), ("post", "/events/{event_id}/submit"),
        ("post", "/events/{event_id}/registrations"), ("put", "/events/{event_id}/attendance"),
        ("get", "/events/{event_id}/reconnect"), ("put", "/events/{event_id}/reconnect-consent"),
        ("post", "/events/{event_id}/attendance-claims"),
        ("post", "/events/{event_id}/attendance-claims/{claim_id}/approve"),
        ("post", "/events/{event_id}/attendance-claims/{claim_id}/decline"),
        ("post", "/events/{event_id}/checkin"), ("put", "/events/{event_id}/checkin-code"),
        ("delete", "/events/{event_id}/checkin-code"),
        ("get", "/admin/events/queue"), ("post", "/admin/events/{event_id}/decision"),
        ("get", "/admin/reports"), ("get", "/admin/users/{user_id}/matching-fields"),
        ("get", "/admin/access-log"), ("post", "/admin/venues"), ("get", "/admin/metrics"),
        ("get", "/healthz"),
    }  # fmt: skip
    declared = {(m, p) for p, item in SPEC["paths"].items() for m in item}
    assert expected <= declared, expected - declared


def test_no_booking_or_payment_surface() -> None:
    """MN-009: venue entries are informational only."""
    assert not [p for p in SPEC["paths"] if "book" in p or "pay" in p or "reserv" in p]


def test_unknown_route_and_bad_body_use_the_envelope() -> None:
    client = TestClient(app)
    missing = client.get("/nope")
    assert missing.status_code == 404
    assert set(missing.json()["error"]) >= {"code", "message", "fallback", "trace_id"}
    bad = client.post("/session/demo-access", json={"access_code": "x", "actor_id": "forged"})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "validation_error"
    assert bad.json()["error"]["fields"][0]["field"] == "actor_id"
