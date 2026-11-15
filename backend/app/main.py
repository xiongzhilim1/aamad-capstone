"""FastAPI entrypoint. Setup scaffold only: business routes are added by @backend.eng (SAD §4)."""

from fastapi import FastAPI

app = FastAPI(title="Peers & Circles API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness check used by the container host and CI (SAD §5)."""
    return {"status": "ok"}
