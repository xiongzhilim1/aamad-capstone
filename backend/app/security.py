"""Signed session cookie and event-code hashing (SAD §8). No secrets are logged."""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID

from fastapi import Response

from app.settings import get_settings

log = logging.getLogger("app.security")

SESSION_COOKIE = "pc_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L
CODE_LENGTH = 6


@lru_cache
def _secret() -> bytes:
    configured = get_settings().session_secret
    if configured:
        return configured.encode()
    log.warning("SESSION_SECRET is not set: using a random secret; sessions end on restart")
    return secrets.token_bytes(32)


def _sign(data: bytes) -> str:
    return hmac.new(_secret(), data, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class SessionData:
    """What the cookie carries. The server is the only party that can mint it."""

    sid: str
    demo: bool
    user_id: UUID | None
    expires_at: int

    def with_user(self, user_id: UUID | None) -> "SessionData":
        return SessionData(self.sid, self.demo, user_id, self.expires_at)


def new_session_data() -> SessionData:
    return SessionData(secrets.token_hex(16), True, None, int(time.time()) + SESSION_TTL_SECONDS)


def encode_session(data: SessionData) -> str:
    payload = json.dumps(
        {
            "sid": data.sid,
            "demo": data.demo,
            "uid": str(data.user_id) if data.user_id else None,
            "exp": data.expires_at,
        },
        separators=(",", ":"),
    ).encode()
    body = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return f"{body}.{_sign(body.encode())}"


def decode_session(cookie: str | None) -> SessionData | None:
    """Returns None for a missing, forged, malformed or expired cookie."""
    if not cookie or "." not in cookie:
        return None
    body, signature = cookie.rsplit(".", 1)
    if not hmac.compare_digest(signature, _sign(body.encode())):
        return None
    try:
        raw = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        data = SessionData(
            sid=str(raw["sid"]),
            demo=bool(raw["demo"]),
            user_id=UUID(raw["uid"]) if raw.get("uid") else None,
            expires_at=int(raw["exp"]),
        )
    except (ValueError, KeyError, TypeError):
        return None
    return data if data.expires_at > time.time() else None


def set_session_cookie(response: Response, data: SessionData) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        encode_session(data),
        max_age=max(0, data.expires_at - int(time.time())),
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        path="/",
    )


def demo_code_matches(candidate: str) -> bool:
    """Fails closed: with no DEMO_ACCESS_CODE configured, nobody gets in (SAD §8)."""
    expected = get_settings().demo_access_code
    if not expected:
        return False
    return hmac.compare_digest(candidate.strip().encode(), expected.encode())


def new_event_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def hash_event_code(event_id: UUID, code: str) -> str:
    normalised = code.strip().upper().replace(" ", "").replace("-", "")
    return _sign(f"checkin:{event_id}:{normalised}".encode())
