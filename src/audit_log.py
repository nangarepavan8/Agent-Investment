"""
STRETCH FEATURE: Audit Trail / Compliance Logging

Directly addresses the "Governance and Security" judging category from
the hackathon poster. Every tool call the agent makes, and every
advisor approve/reject decision, gets written to a persistent local
log file — not just shown live in the UI and then lost.

This is what a compliance team would actually ask for: "show me every
autonomous action this AI system took, when, for which client, and
whether a human approved it."
"""

import os
import csv
import json
from datetime import datetime
from typing import Optional

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audit_log.csv"
)

FIELDNAMES = ["timestamp", "event_type", "client_id", "details"]


def _ensure_log_exists():
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def log_event(event_type: str, client_id: Optional[str], details: dict) -> None:
    """
    Append one audit entry.

    Args:
        event_type: e.g. "tool_call", "approval_decision", "portfolio_scan"
        client_id: the client this event relates to, or None for
                   client-agnostic events (e.g. a full portfolio scan)
        details: any JSON-serializable dict with event-specific info
    """
    _ensure_log_exists()
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": event_type,
            "client_id": client_id or "",
            "details": json.dumps(details),
        })


def load_audit_log():
    """Return the full audit log as a pandas DataFrame (empty if none yet)."""
    import pandas as pd
    _ensure_log_exists()
    return pd.read_csv(LOG_PATH)


def clear_audit_log() -> None:
    """Wipe the log - useful for demo resets."""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    _ensure_log_exists()


if __name__ == "__main__":
    # Quick manual test - run: python -m src.audit_log
    clear_audit_log()
    log_event("tool_call", "CLIENT_001", {"tool": "risk_score_tool", "args": {"client_id": "CLIENT_001"}})
    log_event("approval_decision", "CLIENT_001", {"decision": "approved", "action": "rebalancing"})
    log_event("portfolio_scan", None, {"alerts_found": 4})

    df = load_audit_log()
    print(df.to_string(index=False))
    print(f"\n✅ Audit log working - {len(df)} entries recorded at {LOG_PATH}")
