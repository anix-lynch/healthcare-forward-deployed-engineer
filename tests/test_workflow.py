"""End-to-end smoke for the triage workflow + API surface."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "healthcare-triage-assistant"


def test_status_endpoint(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert "mode" in body
    assert "ehr_connector" in body


def test_triage_returns_complete_response(client):
    r = client.post(
        "/v1/ask",
        json={
            "case_id": "TEST-001",
            "chief_complaint": "chest pain",
            "hpi": "62yo M substernal pressure",
            "age": 62,
            "arrival_mode": "ambulance",
            "vitals": {"bp_sys": 95, "hr": 122, "spo2": 92},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Per customer contract: every response must include these fields
    for key in (
        "case_id", "esi_tier", "tier_bucket", "confidence",
        "red_flags", "rationale", "citations", "similar_cases",
        "human_review_required", "mode",
    ):
        assert key in body, f"missing field: {key}"
    assert body["esi_tier"] in (1, 2, 3, 4, 5)
    # Chest pain with diaphoresis + hypotension should be ESI ≤ 2
    assert body["esi_tier"] <= 2


def test_admin_mode_switch(client):
    r = client.post("/admin/mode", json={"mode": "rules_fallback"})
    assert r.status_code == 200
    assert r.json()["new_mode"] == "rules_fallback"
    # Restore
    r2 = client.post("/admin/mode", json={"mode": "ai_assist"})
    assert r2.status_code == 200


def test_input_guard_blocks_empty(client):
    r = client.post("/v1/ask", json={"case_id": "T", "chief_complaint": ""})
    assert r.status_code == 422  # pydantic rejects before our guard fires
