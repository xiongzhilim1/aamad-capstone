"""Test setup: a separate Postgres database, migrated with Alembic, reseeded for every test.

No test calls a model: `run_crew` is replaced with a stub that fails loudly unless a test
installs its own fake (see `fake_crew`).
"""

import os
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_base = make_url(
    os.environ.get("DATABASE_URL", "postgresql+psycopg://peers:peers@localhost:5432/peers")
)
_name = str(_base.database)
_test_url = _base.set(database=_name if _name.endswith("_test") else f"{_name}_test")
os.environ.update(
    DATABASE_URL=_test_url.render_as_string(hide_password=False),
    DEMO_ACCESS_CODE="test-demo-code",
    SESSION_SECRET="test-session-secret",
    ANTHROPIC_API_KEY="test-key-not-real",
    AI_SPEND_CAP_USD="20",
    AI_MODEL_SUGGEST="claude-sonnet-5-5",
    AI_MODEL_ASSIST="claude-sonnet-5-5",
    ALLOWED_ORIGINS="http://localhost:3000",
)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app import seed  # noqa: E402
from app.ai import controls, profile_assistant  # noqa: E402
from app.api.routes import session as session_routes  # noqa: E402
from app.crews import runtime  # noqa: E402
from app.crews.runtime import CallStats, CrewRun  # noqa: E402
from app.db.session import new_session  # noqa: E402
from app.settings import get_settings  # noqa: E402
from tests.helpers import Api  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def _database(tmp_path_factory: pytest.TempPathFactory) -> None:
    admin = create_engine(_base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{_test_url.database}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{_test_url.database}"'))
    admin.dispose()
    os.environ["TRACE_LOG_DIR"] = str(tmp_path_factory.mktemp("traces"))
    get_settings.cache_clear()
    cfg = Config(os.path.join(BACKEND, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND, "migrations"))
    command.upgrade(cfg, "head")


def _no_model(*_args: Any, **_kwargs: Any) -> CrewRun:
    raise AssertionError("a test reached the model without installing fake_crew")


@pytest.fixture(autouse=True)
def _fresh(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with new_session() as db:
        seed.reset(db)
        db.commit()
    controls.breaker.reset()
    profile_assistant.store.clear()
    session_routes._attempts.reset()
    monkeypatch.setattr(runtime, "run_crew", _no_model)
    yield


@pytest.fixture
def api() -> Callable[[str | None], Api]:
    return lambda persona=None: Api(persona)


@pytest.fixture
def fake_crew(monkeypatch: pytest.MonkeyPatch) -> Callable[..., list[dict[str, Any]]]:
    """Install a stand-in for the crew. `output` is a model instance, a callable taking the
    task inputs, or None for a failure. Returns the list of recorded calls."""

    def install(
        output: Any = None,
        *,
        failure: str | None = None,
        cost: float = 0.01,
        before_return: Callable[[], None] | None = None,
    ) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        def run(task_id: str, inputs: dict[str, str], output_model: type, guard: Any) -> CrewRun:
            calls.append({"task_id": task_id, "inputs": inputs})
            stats = CallStats(
                model_calls=1, stop_reason="end_turn", input_tokens=100, output_tokens=50
            )
            result = CrewRun(task_id=task_id, model="claude-sonnet-5-5", effort="low", stats=stats,
                             latency_ms=1200, cost_usd=cost)  # fmt: skip
            if failure is not None:
                result.failure = failure
                return result
            value = output(inputs) if callable(output) else output
            result.guarded = guard(output_model.model_validate(value))
            if before_return:
                before_return()
            return result

        monkeypatch.setattr(runtime, "run_crew", run)
        return calls

    return install
