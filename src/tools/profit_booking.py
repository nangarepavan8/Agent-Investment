"""
NEW TOOL: Profit-Booking / Tax-Loss Harvesting Suggestions

Answers "which stocks should I book profit on?" using REAL gain/loss
data from get_portfolio_summary() (which now uses live market prices).
This is a genuinely answerable, rule-based question — unlike "will
this stock go up," which no tool or model can reliably predict.

Rule-based thresholds (deliberately simple and explainable, consistent
with the rest of this project's philosophy — see calc_risk_score and
suggest_rebalancing for the same pattern):
    - Gain >= 20%  -> "Consider booking profit"
    - Loss <= -15% -> "Consider tax-loss harvesting" (selling at a loss
                       to offset capital gains tax elsewhere)
    - Everything else -> no action flagged
"""

from typing import Dict, Any
from src.tools.portfolio_summary import get_portfolio_summary

PROFIT_BOOKING_THRESHOLD_PCT = 20.0
TAX_LOSS_HARVEST_THRESHOLD_PCT = -15.0


def suggest_profit_booking(client_id: str) -> Dict[str, Any]:
    """
    Analyze a client's current holdings (using live market prices) and
    flag any with significant unrealized gains (candidates for profit-
    booking) or significant unrealized losses (candidates for tax-loss
    harvesting).

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with client_id, client_name, profit_booking_candidates,
        tax_loss_harvest_candidates, and a summary note
    """
    summary = get_portfolio_summary(client_id)

    if "error" in summary:
        return summary  # propagate the error as-is

    profit_candidates = []
    loss_candidates = []

    for holding in summary["holdings"]:
        pct = holding["gain_loss_pct"]
        if pct >= PROFIT_BOOKING_THRESHOLD_PCT:
            profit_candidates.append({
                "symbol": holding["symbol"],
                "gain_loss_pct": pct,
                "gain_loss": holding["gain_loss"],
                "message": f"{holding['symbol']} is up {pct:.1f}% "
                           f"(${holding['gain_loss']:,.2f}) — consider booking profit.",
            })
        elif pct <= TAX_LOSS_HARVEST_THRESHOLD_PCT:
            loss_candidates.append({
                "symbol": holding["symbol"],
                "gain_loss_pct": pct,
                "gain_loss": holding["gain_loss"],
                "message": f"{holding['symbol']} is down {abs(pct):.1f}% "
                           f"(${holding['gain_loss']:,.2f}) — potential tax-loss "
                           f"harvesting candidate.",
            })

    if not profit_candidates and not loss_candidates:
        note = "No holdings currently cross the profit-booking or tax-loss thresholds."
    else:
        note = (f"{len(profit_candidates)} profit-booking candidate(s), "
                f"{len(loss_candidates)} tax-loss harvesting candidate(s).")

    return {
        "client_id": client_id,
        "client_name": summary["client_name"],
        "profit_booking_candidates": profit_candidates,
        "tax_loss_harvest_candidates": loss_candidates,
        "note": note,
        "price_data_note": summary.get("note"),  # surfaces if prices were stale
    }


if __name__ == "__main__":
    # Quick manual test - run: python -m src.tools.profit_booking
    import json
    print(json.dumps(suggest_profit_booking("CLIENT_001"), indent=2))
