"""Customer-deployable workflows — one job per file. Today: triage."""
from .triage_assistant import triage
from .fallback_logic import to_rules_fallback, should_escalate
