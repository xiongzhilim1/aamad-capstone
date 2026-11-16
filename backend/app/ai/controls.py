"""Runtime controls around the two model calls: rate limit, spend breaker, circuit breaker,
and the per-request trace (CR-010, CR-013, SAD Production Shape)."""

import json
import logging
import threading
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.schemas import Dropped
from app.api.schemas.common import AiFallback
from app.crews.runtime import CrewRun
from app.db.models import ModelTrace
from app.db.session import new_session
from app.settings import get_settings

log = logging.getLogger("app.ai")

RATE_LIMIT_PER_HOUR = 10  # per user, per action (OQ-A04)
BREAKER_FAILURES = 5
BREAKER_WINDOW_SECONDS = 5 * 60
BREAKER_OPEN_SECONDS = 10 * 60

MESSAGES = {
    "ai_unavailable": "This didn't work just now. Nothing was lost.",
    "ai_timeout": "This took too long, so we stopped. Nothing was lost.",
    "ai_budget_exhausted": "AI help is switched off for this demo because its budget is used up.",
    "rate_limited": "You've used {limit} of these this hour.",
    "no_candidates": "There is nobody to suggest yet. Try the filters, or check back later.",
}


class CircuitBreaker:
    """5 consecutive model failures within 5 minutes switch the AI off for 10 minutes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._failures: deque[float] = deque(maxlen=BREAKER_FAILURES)
        self._open_until = 0.0

    def is_open(self) -> bool:
        return time.monotonic() < self._open_until

    def record(self, ok: bool) -> None:
        with self._lock:
            if ok:
                self._failures.clear()
                return
            now = time.monotonic()
            self._failures.append(now)
            full = len(self._failures) == BREAKER_FAILURES
            if full and now - self._failures[0] <= BREAKER_WINDOW_SECONDS:
                self._open_until = now + BREAKER_OPEN_SECONDS
                self._failures.clear()
                log.error("AI circuit breaker opened for %ss", BREAKER_OPEN_SECONDS)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()
            self._open_until = 0.0


breaker = CircuitBreaker()


def fallback(code: str, retry_at: datetime | None = None) -> AiFallback:
    message = MESSAGES[code].format(limit=RATE_LIMIT_PER_HOUR)
    return AiFallback(code=code, message=message, retry_at=retry_at)


def preflight(db: Session, user_id: UUID, crew: str) -> AiFallback | None:
    """Checks that run before any model call. Each one fails closed: no call is made."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return fallback("ai_unavailable")
    spent = db.scalar(select(func.coalesce(func.sum(ModelTrace.cost_usd), 0))) or Decimal(0)
    if float(spent) >= settings.ai_spend_cap_usd:
        log.error("AI spend cap reached: AI is off (CR-010)")
        return fallback("ai_budget_exhausted")
    since = datetime.now(UTC) - timedelta(hours=1)
    used = db.scalars(
        select(ModelTrace.created_at)
        .where(
            ModelTrace.user_id == user_id, ModelTrace.crew == crew, ModelTrace.created_at > since
        )
        .order_by(ModelTrace.created_at)
    ).all()
    if len(used) >= RATE_LIMIT_PER_HOUR:
        return fallback("rate_limited", used[-RATE_LIMIT_PER_HOUR] + timedelta(hours=1))
    if breaker.is_open():
        return fallback("ai_unavailable")
    return None


def failure_code(run: CrewRun) -> str:
    return "ai_timeout" if run.failure == "timeout" else "ai_unavailable"


def write_trace(
    *,
    trace_id: str,
    crew: str,
    user_id: UUID,
    run: CrewRun | None,
    outcome: str,
    fallback_code: str | None = None,
    input_ids: list[str] | None = None,
    output_ids: list[str] | None = None,
    dropped: list[Dropped] | None = None,
    task_id: str = "",
) -> None:
    """One decision-log record per AI request: ids, counts, cost and latency; never profile
    content or prompt text (CR-013). Written in its own transaction so it survives a failed
    request. Fails open: a logging error is reported but does not block the user."""
    settings = get_settings()
    record = {
        "trace_id": trace_id,
        "crew": crew,
        "task_id": run.task_id if run else task_id,
        "model": run.model if run else "",
        "effort": run.effort if run else settings.ai_effort,
        "user_id": str(user_id),
        "outcome": outcome,
        "fallback_code": fallback_code,
        "input_ids": input_ids or [],
        "output_ids": output_ids or [],
        "dropped": [f"{d.item}:{d.reason}" for d in dropped or []],
        "model_calls": run.stats.model_calls if run else 0,
        "schema_failures": run.schema_failures if run else 0,
        "stop_reason": run.stats.stop_reason if run else None,
        "input_tokens": (
            run.stats.input_tokens + run.stats.cache_read_tokens + run.stats.cache_write_tokens
            if run
            else 0
        ),
        "output_tokens": run.stats.output_tokens if run else 0,
        "cost_usd": round(run.cost_usd, 6) if run else 0.0,
        "latency_ms": run.latency_ms if run else 0,
    }
    try:
        with new_session() as db:
            row = dict(record, user_id=user_id, cost_usd=Decimal(str(record["cost_usd"])))
            db.add(ModelTrace(**row))
            db.commit()
        line = dict(
            record,
            at=datetime.now(UTC).isoformat(timespec="seconds"),
            prompt_sha256=run.stats.prompt_sha256 if run else None,
            failure=run.failure if run else None,
        )
        directory = Path(settings.trace_log_dir)
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "model-traces.jsonl").open("a") as handle:
            handle.write(json.dumps(line, sort_keys=True) + "\n")
    except Exception:  # noqa: BLE001 - CR-013 fails open, with an alert
        log.exception("ALERT model trace could not be written trace_id=%s", trace_id)


def set_review_outcome(db: Session, trace_id: str | None, outcome: str) -> None:
    """Record whether the author accepted or discarded an assistant draft (aggregate view)."""
    if not trace_id:
        return
    row = db.scalar(select(ModelTrace).where(ModelTrace.trace_id == trace_id))
    if row is not None:
        row.review_outcome = outcome
