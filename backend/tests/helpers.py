"""Test helpers: a browser-like API client per persona."""

from typing import Any

from fastapi.testclient import TestClient

from app import seed
from app.main import app


class Api:
    """A browser-like client for one persona. Uses https so the Secure cookie is sent."""

    def __init__(self, persona: str | None = None) -> None:
        self.http = TestClient(app, base_url="https://testserver")
        if persona:
            self.login(persona)

    def login(self, persona: str) -> None:
        ok = self.http.post("/session/demo-access", json={"access_code": "test-demo-code"})
        assert ok.status_code == 200, ok.text
        chosen = self.http.post("/session/persona", json={"persona_id": str(seed.sid(persona))})
        assert chosen.status_code == 200, chosen.text

    def get(self, path: str, **kw: Any) -> Any:
        return self.http.get(path, **kw)

    def post(self, path: str, json: Any = None) -> Any:
        return self.http.post(path, json=json)

    def put(self, path: str, json: Any = None) -> Any:
        return self.http.put(path, json=json)

    def patch(self, path: str, json: Any = None) -> Any:
        return self.http.patch(path, json=json)

    def delete(self, path: str) -> Any:
        return self.http.delete(path)

    def ok(
        self, method: str, path: str, json: Any = None, status: int = 200, params: Any = None
    ) -> Any:
        response = self.http.request(method, path, json=json, params=params)
        assert response.status_code == status, (
            f"{method} {path}: {response.status_code} {response.text}"
        )
        return response.json() if response.content else None

    def error(self, method: str, path: str, status: int, json: Any = None) -> dict[str, Any]:
        response = self.http.request(method, path, json=json)
        assert response.status_code == status, (
            f"{method} {path}: {response.status_code} {response.text}"
        )
        body: dict[str, Any] = response.json()["error"]
        return body


def uid(key: str) -> str:
    return str(seed.sid(key))


def names(cards: list[dict[str, Any]]) -> set[str]:
    return {c["display_name"] for c in cards}
