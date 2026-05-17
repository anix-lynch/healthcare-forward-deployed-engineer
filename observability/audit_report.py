"""Audit report CLI — slice recent audit rows for on-call.

Referenced by docs/runbook.md P1 drift step:
    python observability/audit_report.py --hours 1

Pulls from outputs/audit.jsonl (written by logging.audit_log on every
triage decision). Real production swap = query Cloud Logging /
Application Insights / CloudWatch with the same shape.

Usage:
    python observability/audit_report.py --hours 1
    python observability/audit_report.py --hours 24 --event triage_decision
    python observability/audit_report.py --case-id PERF-001
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


_OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
LOG_PATH = _OUT_DIR / "audit.jsonl"
PHI_PATH = _OUT_DIR / "phi_archive.jsonl"


def _parse_ts(ts: str) -> datetime:
    """Parse the ISO8601-Z timestamp logging.audit_log writes."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_rows(
    *,
    hours: float | None = None,
    event_filter: str | None = None,
    case_id_filter: str | None = None,
    include_phi: bool = False,
) -> list[dict]:
    """Load audit rows from outputs/audit.jsonl with optional filters.

    If include_phi=True, ALSO reads outputs/phi_archive.jsonl. Prints
    a banner warning — phi_archive contains past-patient narrative
    text and access should be audit-trailed in production.
    """
    sources = [LOG_PATH]
    if include_phi and PHI_PATH.exists():
        print(
            "⚠️  --include-phi: reading outputs/phi_archive.jsonl. "
            "Access should be audit-trailed in production.",
            file=sys.stderr,
        )
        sources.append(PHI_PATH)

    cutoff = None
    if hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    out: list[dict] = []
    for src in sources:
        if not src.exists():
            continue
        out.extend(_load_from(src, cutoff, event_filter, case_id_filter))
    return out


def _load_from(
    path: Path,
    cutoff: datetime | None,
    event_filter: str | None,
    case_id_filter: str | None,
) -> list[dict]:
    out: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if cutoff is not None:
                try:
                    if _parse_ts(row.get("ts", "")) < cutoff:
                        continue
                except ValueError:
                    continue
            if event_filter and row.get("event") != event_filter:
                continue
            if case_id_filter and row.get("case_id") != case_id_filter:
                continue
            out.append(row)
    return out


def summarize(rows: list[dict]) -> dict:
    """Produce the rolling-window summary on-call reads at 3am."""
    by_event = Counter(r.get("event", "<unknown>") for r in rows)
    by_mode = Counter(
        (r.get("payload") or {}).get("mode", "<unknown>") for r in rows
    )
    tiers = [
        (r.get("payload") or {}).get("esi_tier")
        for r in rows
        if (r.get("payload") or {}).get("esi_tier") is not None
    ]
    tier_dist = Counter(tiers)
    return {
        "total_rows": len(rows),
        "by_event": dict(by_event),
        "by_mode": dict(by_mode),
        "esi_tier_distribution": dict(tier_dist),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hours", type=float, default=1.0,
                    help="rolling window in hours (default 1)")
    ap.add_argument("--event", default=None,
                    help="filter to a single event name (e.g. triage_decision)")
    ap.add_argument("--case-id", default=None,
                    help="filter to one case_id (drill-down)")
    ap.add_argument("--raw", action="store_true",
                    help="print full rows as JSONL instead of summary")
    ap.add_argument("--include-phi", action="store_true",
                    help="ALSO read phi_archive.jsonl (restricted; warns to stderr)")
    args = ap.parse_args()

    rows = load_rows(
        hours=args.hours,
        event_filter=args.event,
        case_id_filter=args.case_id,
        include_phi=args.include_phi,
    )

    if args.raw:
        for r in rows:
            print(json.dumps(r))
        return 0

    summary = summarize(rows)
    print(json.dumps(
        {
            "window_hours": args.hours,
            "log_path": str(LOG_PATH),
            **summary,
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
