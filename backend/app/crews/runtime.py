"""CrewAI hosting for the two augmented calls (SAD Pattern Decision, §2; CrewAI adapter rule).

Each crew is one agent, one task, no tools, sequential, memory off. Agents and tasks are
declared in `config/agents.yaml` and `config/tasks.yaml`. This module is the only place that
imports CrewAI; `app/ai/*` calls `run_crew` and the API routes never see it.

Transport notes (OQ-A03, verified 2026-11-16 with crewai 1.15.41 + anthropic 0.73.0):
* CrewAI sends no `temperature` unless one is configured, and none is.
* CrewAI has no `effort` setting, so the request hook below adds `output_config.effort`.
* The same hook records stop reason and token usage for the trace (CR-005, CR-013).
"""

import hashlib
import json
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import BaseModel

# Must be set before CrewAI is imported: no telemetry or hosted tracing leaves the backend.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.llms.hooks.base import BaseInterceptor  # noqa: E402

from app.settings import get_settings  # noqa: E402

CONFIG_DIR = Path(__file__).parent / "config"
TIMEOUT_SECONDS = 20  # overall per request (SAD Production Shape)
MAX_MODEL_CALLS = 2  # one call plus at most one retry (CR-005)
MAX_RPM = 30

AGENT_KEYS = {
    "role", "goal", "backstory", "allow_delegation", "max_iter", "max_retry_limit",
    "max_execution_time", "verbose",
}  # fmt: skip
TASK_KEYS = {"agent", "description", "expected_output", "max_tokens"}

# USD per million tokens: input, output, cache read. Cache writes cost 1.25x input.
# List prices from the claude-api skill reference (cached 2026-11-03); re-check on a swap.
PRICES = {
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}
BAD_STOP_REASONS = {"refusal", "max_tokens"}

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="crew")


class CrewConfigError(RuntimeError):
    """The crew YAML breaks a control. The service refuses to boot (CR-008)."""


@lru_cache
def load_config() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    agents = yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text())
    tasks = yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text())
    return agents, tasks


def validate_config() -> None:
    """Startup check (CR-008, SAD §2): no tools anywhere, no unknown keys, bounded iterations."""
    agents, tasks = load_config()
    for name, cfg in agents.items():
        unknown = set(cfg) - AGENT_KEYS
        if unknown:
            raise CrewConfigError(f"agent {name}: keys not allowed: {sorted(unknown)}")
        if cfg.get("allow_delegation") is not False:
            raise CrewConfigError(f"agent {name}: allow_delegation must be false")
        if not 1 <= int(cfg.get("max_iter", 0)) <= MAX_MODEL_CALLS:
            raise CrewConfigError(f"agent {name}: max_iter must be 1 or {MAX_MODEL_CALLS}")
    for name, cfg in tasks.items():
        unknown = set(cfg) - TASK_KEYS
        if unknown:
            raise CrewConfigError(f"task {name}: keys not allowed: {sorted(unknown)}")
        if cfg.get("agent") not in agents:
            raise CrewConfigError(f"task {name}: unknown agent {cfg.get('agent')!r}")
        if not isinstance(cfg.get("max_tokens"), int):
            raise CrewConfigError(f"task {name}: max_tokens is required")


@dataclass
class CallStats:
    model_calls: int = 0
    stop_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    prompt_sha256: str | None = None


class _Transport(BaseInterceptor[httpx.Request, httpx.Response]):
    """Adds `output_config.effort` and records usage. Never logs prompt or response content."""

    def __init__(self, effort: str, stats: CallStats) -> None:
        self.effort = effort
        self.stats = stats
        self._awaiting_message = False

    def on_outbound(self, message: httpx.Request) -> httpx.Request:
        # The response hook cannot see its request, so remember what kind of call is in flight.
        self._awaiting_message = message.url.path.rstrip("/").endswith("/messages")
        if not self._awaiting_message:
            return message  # token counting and other calls pass through untouched
        body = json.loads(message.content)
        body.pop("temperature", None)  # defence in depth: 5.5-generation models reject it
        body.setdefault("output_config", {})["effort"] = self.effort
        data = json.dumps(body).encode()
        self.stats.model_calls += 1
        self.stats.prompt_sha256 = hashlib.sha256(
            json.dumps([body.get("system"), body.get("messages")], sort_keys=True).encode()
        ).hexdigest()
        headers = dict(message.headers)
        headers["content-length"] = str(len(data))
        return httpx.Request(message.method, message.url, headers=headers, content=data)

    def on_inbound(self, message: httpx.Response) -> httpx.Response:
        if not self._awaiting_message:
            return message
        try:
            message.read()
            payload = message.json()
        except Exception:  # noqa: BLE001 - a logging hook must never break the call
            return message
        if isinstance(payload, dict) and message.status_code == 200:
            usage = payload.get("usage") or {}
            self.stats.stop_reason = payload.get("stop_reason")
            self.stats.input_tokens += int(usage.get("input_tokens") or 0)
            self.stats.output_tokens += int(usage.get("output_tokens") or 0)
            self.stats.cache_read_tokens += int(usage.get("cache_read_input_tokens") or 0)
            self.stats.cache_write_tokens += int(usage.get("cache_creation_input_tokens") or 0)
        return message


def cost_usd(model: str, stats: CallStats) -> float:
    price_in, price_out, price_read = PRICES.get(model, PRICES["claude-sonnet-5-5"])
    return (
        stats.input_tokens * price_in
        + stats.cache_write_tokens * price_in * 1.25
        + stats.cache_read_tokens * price_read
        + stats.output_tokens * price_out
    ) / 1_000_000


@dataclass
class CrewRun:
    """Outcome of one crew kickoff. `failure` is None on success."""

    task_id: str
    model: str
    effort: str
    guarded: Any = None
    failure: str | None = None  # timeout | schema | refusal | error
    schema_failures: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    stats: CallStats = field(default_factory=CallStats)


def run_crew(
    task_id: str,
    inputs: dict[str, str],
    output_model: type[BaseModel],
    guard: Callable[[Any], Any],
) -> CrewRun:
    """Run one single-task crew and return its guarded output or a typed failure.

    `guard` receives the schema-valid output and returns what the caller may use; it runs
    inside `Task.guardrail` (W08 or W22). A schema miss, a refusal or a truncated response
    fails the guardrail, which gives exactly one retry; a second failure is a fallback.
    """
    settings = get_settings()
    agents_cfg, tasks_cfg = load_config()
    task_cfg = dict(tasks_cfg[task_id])
    agent_name = task_cfg.pop("agent")
    max_tokens = int(task_cfg.pop("max_tokens"))
    model = settings.ai_model_suggest if agent_name == "peer_matcher" else settings.ai_model_assist
    stats = CallStats()
    run = CrewRun(task_id=task_id, model=model, effort=settings.ai_effort, stats=stats)
    holder: dict[str, Any] = {}

    def guardrail(output: Any) -> tuple[bool, Any]:
        parsed = getattr(output, "pydantic", None)
        if stats.stop_reason in BAD_STOP_REASONS:
            run.schema_failures += 1
            holder["failure"] = "refusal" if stats.stop_reason == "refusal" else "schema"
            return False, "The response was incomplete. Return the complete JSON object."
        if not isinstance(parsed, output_model):
            run.schema_failures += 1
            holder["failure"] = "schema"
            return False, "The response did not match the required JSON schema."
        holder.pop("failure", None)
        holder["guarded"] = guard(parsed)
        return True, parsed

    def kickoff() -> None:
        llm = LLM(
            model=f"anthropic/{model}",
            api_key=settings.anthropic_api_key,
            max_tokens=max_tokens,
            timeout=TIMEOUT_SECONDS,
            max_retries=2,
            interceptor=_Transport(settings.ai_effort, stats),
        )
        agent = Agent(llm=llm, tools=[], **agents_cfg[agent_name])
        task = Task(
            name=task_id,
            agent=agent,
            output_pydantic=output_model,
            guardrail=guardrail,
            guardrail_max_retries=MAX_MODEL_CALLS - 1,
            **task_cfg,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            memory=False,
            max_rpm=MAX_RPM,
            verbose=False,
        )
        if any(a.tools for a in crew.agents) or any(t.tools for t in crew.tasks):
            raise CrewConfigError("a tool is bound to a crew (CR-008)")
        crew.kickoff(inputs=inputs)

    started = time.monotonic()
    future = _executor.submit(kickoff)
    try:
        future.result(timeout=TIMEOUT_SECONDS)
        run.guarded = holder.get("guarded")
        if run.guarded is None:
            run.failure = holder.get("failure", "schema")
    except FutureTimeout:
        run.failure = "timeout"  # the worker's late result is discarded
    except Exception:  # noqa: BLE001 - any runtime error becomes a typed fallback (MC-005)
        run.failure = holder.get("failure", "error")
    run.latency_ms = int((time.monotonic() - started) * 1000)
    run.cost_usd = cost_usd(model, stats)
    return run
