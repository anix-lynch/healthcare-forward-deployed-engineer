"""Long-lived workload identity for background sync jobs.

In production: uses GCP Workload Identity / Azure Managed Identity /
AWS IAM role attached to the compute instance. NO secrets in env vars,
NO PEMs on disk, NO long-lived API keys.

Here: returns a deterministic principal id. Honest stub.
"""
from __future__ import annotations
import os


def get_service_principal() -> dict:
    """Return the workload identity principal currently mounted."""
    return {
        "principal": os.environ.get("SERVICE_PRINCIPAL", "triage-assistant@customer-vpc"),
        "auth_method": "workload_identity",
        "scopes": ["read:encounters", "write:audit_log"],
    }
