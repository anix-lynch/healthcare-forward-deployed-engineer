"""Scheduled background syncs — refresh identity map + warm caches.

In production: triggered by cron / Cloud Scheduler / Airflow DAG.
Here: runnable directly. Each job is idempotent and logs to observability.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def refresh_identity_map() -> dict:
    """Rebuild encounter → patient_id map from the current EHR snapshot.

    Returns: status dict for observability logging.
    """
    t0 = time.time()
    from integrations.ehr_adapter import _load_mock_rows
    from integrations.identity_mapper import patient_id_from_name

    rows = _load_mock_rows()
    map = {f"L1-{i:06d}": patient_id_from_name(r.get("Name", "")) for i, r in enumerate(rows)}
    return {
        "job": "refresh_identity_map",
        "n_encounters": len(map),
        "n_patients": len(set(map.values())),
        "duration_s": round(time.time() - t0, 3),
        "status": "ok",
    }


def warm_retrieval_index() -> dict:
    """Touch the retrieval pipeline so the BM25 index is warm before first /ask."""
    t0 = time.time()
    from retrieval.query_pipeline import QueryPipeline
    pipeline = QueryPipeline()
    _ = pipeline.retrieve("warm-up query", k=1)
    return {
        "job": "warm_retrieval_index",
        "duration_s": round(time.time() - t0, 3),
        "status": "ok",
    }


if __name__ == "__main__":
    import json
    for fn in [refresh_identity_map, warm_retrieval_index]:
        print(json.dumps(fn(), indent=2))
