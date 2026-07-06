"""
STRETCH FEATURE: Proactive/Autonomous Risk Monitoring

This is what makes the agent "proactive" rather than purely reactive
(the same distinction your own problem statement draws). Instead of
waiting for an advisor to ask "how risky is CLIENT_003?", this scans
ALL clients at once and surfaces anything that needs attention —
unprompted.

Approach: scan every client's current risk score, compare against the
last saved snapshot (a simple local JSON file), and flag:
  - Any client currently at High risk
  - Any client whose risk score increased since the last scan

This is deliberately deterministic (no LLM call needed for the scan
itself) - fast, free, and reliable for a live demo. The agent/LLM can
still be used afterward to explain a flagged client's situation in
natural language if the advisor asks a follow-up.
"""

import os
import json
from typing import List, Dict, Any

from src.tools.data_loader import load_clients
from src.tools.risk_score import calc_risk_score
from src.audit_log import log_event

SNAPSHOT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "monitoring_snapshot.json"
)


def _load_last_snapshot() -> Dict[str, Any]:
    if not os.path.exists(SNAPSHOT_PATH):
        return {}
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_snapshot(snapshot: Dict[str, Any]) -> None:
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)


def _build_suggested_action(risk_result: Dict[str, Any]) -> str:
    """
    Build a concrete, data-driven suggestion based on THIS client's
    actual biggest risk contributor — not a generic message. Compares
    sector concentration vs. safe-asset allocation and suggests
    whichever real lever would help most.
    """
    top_sector = risk_result["top_sector"]
    max_sector_pct = risk_result["max_sector_pct"]
    safe_ratio_pct = risk_result["safe_ratio_pct"]

    if max_sector_pct >= 35 and safe_ratio_pct < 25:
        return (f"Consider both: rebalancing out of {top_sector} ({max_sector_pct:.0f}% of stock "
                f"holdings) into other sectors, AND increasing allocation to FD/RD/Bonds/PPF "
                f"(currently only {safe_ratio_pct:.0f}% safe assets).")
    elif max_sector_pct >= 35:
        return (f"Consider rebalancing out of {top_sector} ({max_sector_pct:.0f}% of stock "
                f"holdings) into underweighted sectors to reduce concentration risk.")
    elif safe_ratio_pct < 25:
        return (f"Consider increasing allocation to safer instruments (FD/RD/Bonds/PPF) — "
                f"currently only {safe_ratio_pct:.0f}% of this client's total portfolio is in "
                f"safe assets.")
    else:
        return "Risk driven mainly by stated risk profile rather than concentration — review with client directly."


def scan_all_clients() -> List[Dict[str, Any]]:
    """
    Run a risk scan across every client and return a list of alerts for
    anything that needs advisor attention. Updates the snapshot file so
    the NEXT scan can detect score changes.

    Returns:
        list of alert dicts, each with:
            client_id, client_name, risk_score, risk_level,
            alert_type ("high_risk" | "risk_increased"), message,
            suggested_action (data-driven, not generic)
    """
    clients_df = load_clients()
    last_snapshot = _load_last_snapshot()
    new_snapshot = {}
    alerts = []

    for _, client_row in clients_df.iterrows():
        client_id = client_row["client_id"]
        client_name = client_row["name"]

        risk_result = calc_risk_score(client_id)
        current_score = risk_result["risk_score"]
        current_level = risk_result["risk_level"]

        new_snapshot[client_id] = current_score

        previous_score = last_snapshot.get(client_id)
        suggested_action = _build_suggested_action(risk_result)

        if current_level == "High":
            alerts.append({
                "client_id": client_id,
                "client_name": client_name,
                "risk_score": current_score,
                "risk_level": current_level,
                "alert_type": "high_risk",
                "message": f"{client_name} ({client_id}) is at HIGH risk "
                           f"(score {current_score}/100).",
                "suggested_action": suggested_action,
            })
        elif previous_score is not None and current_score > previous_score + 5:
            alerts.append({
                "client_id": client_id,
                "client_name": client_name,
                "risk_score": current_score,
                "risk_level": current_level,
                "alert_type": "risk_increased",
                "message": f"{client_name} ({client_id})'s risk score increased "
                           f"from {previous_score} to {current_score} since the last scan.",
                "suggested_action": suggested_action,
            })

    _save_snapshot(new_snapshot)
    log_event("portfolio_scan", None, {"alerts_found": len(alerts), "client_count": len(clients_df)})
    return alerts


def reset_snapshot() -> None:
    """Delete the snapshot file - useful for demo resets (forces a 'first run' state)."""
    if os.path.exists(SNAPSHOT_PATH):
        os.remove(SNAPSHOT_PATH)


if __name__ == "__main__":
    # Quick manual test - run: python -m src.monitoring
    print("Running portfolio health scan across all clients...\n")
    alerts = scan_all_clients()
    if not alerts:
        print("✅ No alerts - all clients within normal risk range.")
    else:
        for alert in alerts:
            icon = "🔴" if alert["alert_type"] == "high_risk" else "🟠"
            print(f"{icon} {alert['message']}")
