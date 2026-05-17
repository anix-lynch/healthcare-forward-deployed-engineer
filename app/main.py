"""FastAPI entrypoint — customer-deployable triage assistant service."""
from __future__ import annotations
import time
from fastapi import FastAPI, Request

from app.routers import ask, status, admin

app = FastAPI(
    title="healthcare-triage-assistant",
    version="0.1.0",
    description=(
        "Customer-deployable ER triage assistant. "
        "Designed for VPC deployment behind hospital firewall, not vendor SaaS."
    ),
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """Stamp X-Process-Time-Ms on every response.

    Triage's internal `latency_ms` only covers retrieval + ESI + generation.
    For honest p95 against the customer SLO (800ms), measure at the request
    boundary — includes pydantic validation, PII masking, serialization.
    PERF-001 / PERF-002 acceptance tests assert against THIS header, not
    the internal counter.
    """
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    return response


app.include_router(status.router, tags=["meta"])
app.include_router(ask.router, prefix="/v1", tags=["triage"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
