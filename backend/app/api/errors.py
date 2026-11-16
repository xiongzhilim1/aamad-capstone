"""Error envelope (SAD §4): every non-2xx response is `{"error": {...}}` with a trace id."""

import logging
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.common import ErrorBody, ErrorEnvelope, FieldError

log = logging.getLogger("app.api")

Fallback = Literal["filters", "manual"] | None


class ApiError(Exception):
    """Raise from services and routes; rendered as the error envelope."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        fallback: Fallback = None,
        retry_at: datetime | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fallback = fallback
        self.retry_at = retry_at


def not_found(message: str = "We couldn't find that.") -> ApiError:
    """Also used for resources whose existence is private (unpublished events, others' requests)."""
    return ApiError(404, "not_found", message)


def forbidden(message: str = "You can't do that.", code: str = "forbidden") -> ApiError:
    return ApiError(403, code, message)


def conflict(code: str, message: str) -> ApiError:
    return ApiError(409, code, message)


def trace_id_of(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if not isinstance(trace_id, str):
        trace_id = uuid.uuid4().hex
        request.state.trace_id = trace_id
    return trace_id


def _render(request: Request, status: int, body: ErrorBody) -> JSONResponse:
    content = ErrorEnvelope(error=body).model_dump(mode="json", exclude_none=True)
    content["error"].setdefault("fallback", None)
    return JSONResponse(status_code=status, content=content)


_STATUS_CODES = {
    400: "bad_request",
    401: "not_signed_in",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    429: "rate_limited",
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        body = ErrorBody(
            code=exc.code,
            message=exc.message,
            fallback=exc.fallback,
            trace_id=trace_id_of(request),
            retry_at=exc.retry_at,
        )
        return _render(request, exc.status, body)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for err in exc.errors():
            loc: tuple[Any, ...] = tuple(err.get("loc", ()))
            path = ".".join(str(p) for p in loc if p not in ("body", "query", "path"))
            fields.append(FieldError(field=path or "body", message=str(err.get("msg", "Invalid"))))
        body = ErrorBody(
            code="validation_error",
            message="Some of what you entered needs a change. Nothing was lost.",
            trace_id=trace_id_of(request),
            fields=fields,
        )
        return _render(request, 422, body)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, "error")
        message = "We couldn't find that." if exc.status_code == 404 else "That didn't work."
        body = ErrorBody(code=code, message=message, trace_id=trace_id_of(request))
        return _render(request, exc.status_code, body)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        trace_id = trace_id_of(request)
        log.exception("unhandled error trace_id=%s", trace_id)
        body = ErrorBody(
            code="internal_error",
            message="Something went wrong on our side. Nothing was lost; please try again.",
            trace_id=trace_id,
        )
        return _render(request, 500, body)


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` entries that all use the error envelope."""
    descriptions = {
        401: "Not signed in",
        403: "Not allowed",
        404: "Not found, or not visible to you",
        409: "Conflicts with the current state",
        422: "Validation error",
        429: "Rate limited",
        503: "Temporarily unavailable",
    }
    return {
        s: {"model": ErrorEnvelope, "description": descriptions.get(s, "Error")} for s in statuses
    }
