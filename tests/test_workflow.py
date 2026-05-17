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


def test_admin_mode_switch(client, monkeypatch):
    # Wire a deterministic bearer token for the test.
    monkeypatch.setenv("ADMIN_BEARER_TOKEN", "test-token-fixture")
    headers = {"Authorization": "Bearer test-token-fixture"}
    r = client.post("/admin/mode", json={"mode": "rules_fallback"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["new_mode"] == "rules_fallback"
    # Restore
    r2 = client.post("/admin/mode", json={"mode": "ai_assist"}, headers=headers)
    assert r2.status_code == 200


def test_admin_mode_rejects_missing_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_BEARER_TOKEN", "test-token-fixture")
    r = client.post("/admin/mode", json={"mode": "off"})  # no headers
    assert r.status_code == 401, "missing bearer token must 401"


def test_admin_mode_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_BEARER_TOKEN", "test-token-fixture")
    headers = {"Authorization": "Bearer wrong-token"}
    r = client.post("/admin/mode", json={"mode": "off"}, headers=headers)
    assert r.status_code == 401, "wrong bearer token must 401"


def test_input_guard_blocks_empty(client):
    r = client.post("/v1/ask", json={"case_id": "T", "chief_complaint": ""})
    assert r.status_code == 422  # pydantic rejects before our guard fires


def test_generation_masks_pii_from_snippet():
    """generate_answer() must NOT re-emit PII from retrieved snippets.

    Per Cowork audit: in Epic-backed retrieval, snippets ARE past-patient
    narrative text. Even with ingest-time PHI redaction, a defensive mask
    at the generation layer is fail-closed protection against any pattern
    the ingest layer missed.
    """
    from generation.generate import generate_answer
    fake_hits = [{
        "case_id": "L1-SSN-LEAK",
        "snippet": "62yo M, SSN 123-45-6789 visited last week, complained chest pain",
        "score": 1.0,
    }]
    out = generate_answer("chest pain", fake_hits)
    assert "123-45-6789" not in out["answer"], \
        "SSN leaked through to rationale despite mask_pii()"
    assert any("redacted" in w for w in out.get("warnings", [])), \
        "redaction warning should be appended when mask fires"


def test_process_time_header_present(client):
    """Middleware must stamp X-Process-Time-Ms on every response for
    request-boundary p95 measurement (includes validation + serialization,
    not just internal triage() timing).
    """
    r = client.get("/health")
    assert "X-Process-Time-Ms" in r.headers, \
        "X-Process-Time-Ms middleware header missing"
    assert int(r.headers["X-Process-Time-Ms"]) >= 0
