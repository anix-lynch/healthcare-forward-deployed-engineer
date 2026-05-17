"""FastAPI entrypoint — customer-deployable triage assistant service."""
from __future__ import annotations
from fastapi import FastAPI

from app.routers import ask, status, admin

app = FastAPI(
    title="healthcare-triage-assistant",
    version="0.1.0",
    description=(
        "Customer-deployable ER triage assistant. "
        "Designed for VPC deployment behind hospital firewall, not vendor SaaS."
    ),
)
app.include_router(status.router, tags=["meta"])
app.include_router(ask.router, prefix="/v1", tags=["triage"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
