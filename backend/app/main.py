"""FastAPI entrypoint (SAD §4). Routes live in `app/api/routes`; the contract is `openapi.json`."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.errors import error_responses, install_error_handlers
from app.api.routes import admin, circles, connections, discovery, events, profile, session
from app.crews.runtime import validate_config
from app.settings import get_settings

DESCRIPTION = """
REST over JSON for the Peers & Circles capstone (synthetic data only).

* **Auth**: `POST /session/demo-access`, then `POST /session/persona`. The server sets an
  HttpOnly cookie; the actor always comes from it, never from request input.
* **Errors**: every non-2xx response is `{"error": {code, message, fallback, trace_id}}`.
  Resources whose existence is private return `404`.
* **AI**: `POST /suggestions` and `POST /me/profile/draft` return HTTP 200 with
  `status: "fallback"` when the model path is unavailable. No streaming.
"""


def _operation_id(route: APIRoute) -> str:
    """Use the handler name so generated clients get readable method names."""
    return route.name


def create_app() -> FastAPI:
    settings = get_settings()
    validate_config()  # CR-008: refuse to boot if a tool is bound or the crew YAML is off-contract
    app = FastAPI(
        title="Peers & Circles API",
        version="0.2.0",
        description=DESCRIPTION,
        responses=error_responses(422),
        generate_unique_id_function=_operation_id,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["content-type"],
    )

    @app.middleware("http")
    async def _trace(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.trace_id = uuid.uuid4().hex
        response = await call_next(request)
        response.headers["x-trace-id"] = request.state.trace_id
        return response

    install_error_handlers(app)

    @app.get("/healthz", tags=["ops"], summary="Liveness check")
    def healthz() -> dict[str, str]:
        """Unauthenticated; used by the container host and CI (SAD §5)."""
        return {"status": "ok"}

    for module in (session, profile, discovery, connections, circles, events, admin):
        app.include_router(module.router)
    return app


app = create_app()
