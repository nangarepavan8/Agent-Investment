"""
Profit-Booking / Tax-Loss Harvesting Suggestions — now TAX-AWARE

Answers "which stocks should I book profit on?" using REAL gain/loss
data AND real holding-period-aware capital gains tax rules — not just
arbitrary gain/loss thresholds. This connects two pieces of real data
that already existed separately in this project: purchase dates (for
holding period) and researched LTCG/STCG tax rates (Section 111A/112A).

For each flagged holding, this now shows:
    - Whether the gain currently qualifies as STCG (≤12 months held,
      taxed at a flat 20%) or LTCG (>12 months, taxed at 12.5% above
      the ₹1.25 lakh annual exemption)
    - The actual tax if sold today
    - If still short-term, how many days remain until it qualifies
      for the lower long-term rate, and the potential tax saved by waiting

IMPORTANT SIMPLIFICATION, clearly stated: the ₹1.25 lakh LTCG exemption
is an ANNUAL, AGGREGATE exemption across ALL of a client's equity LTCG
in a financial year — not per-holding. This tool illustrates the tax
treatment of EACH holding in isolation (as if it were the only equity
sale that year), which is directionally useful for comparing STCG vs.
LTCG treatment, but the actual tax owed depends on total realized gains
across the whole year. This is stated in every result, consistent with
this project's honesty-first approach elsewhere (see tax_guidance.py).
"""

from datetime import date
from typing import Dict, Any
from src.tools.portfolio_summary import get_portfolio_summary

PROFIT_BOOKING_THRESHOLD_PCT = 20.0
TAX_LOSS_HARVEST_THRESHOLD_PCT = -15.0

LTCG_HOLDING_DAYS_THRESHOLD = 365  # equity: >12 months = long-term
STCG_TAX_RATE = 0.20
LTCG_TAX_RATE = 0.125
LTCG_ANNUAL_EXEMPTION = 125000  # ₹1.25 lakh, applied per-holding as a simplification (see docstring)


def _tax_treatment_for_holding(gain_loss: float, purchase_date_str: str) -> Dict[str, Any]:
    """
    Determine real STCG/LTCG tax treatment for one holding's gain,
    based on its actual purchase date.
    """
    try:
        purchase_dt = date.fromisoformat(purchase_date_str)
        holding_days = (date.today() - purchase_dt).days
    except Exception:
        holding_days = 0

    is_long_term = holding_days > LTCG_HOLDING_DAYS_THRESHOLD

    if gain_loss <= 0:
        # Losses don't have a "tax if sold today" in the same sense —
        # handled separately in the loss-harvesting branch
        return {"holding_days": holding_days, "is_long_term": is_long_term}

    if is_long_term:
        taxable_gain = max(0, gain_loss - LTCG_ANNUAL_EXEMPTION)
        tax_if_sold_now = round(taxable_gain * LTCG_TAX_RATE, 2)
        return {
            "holding_days": holding_days,
            "is_long_term": True,
            "tax_treatment": "LTCG (12.5% above ₹1.25L exemption)",
            "tax_if_sold_now": tax_if_sold_now,
        }
    else:
        tax_if_sold_now = round(gain_loss * STCG_TAX_RATE, 2)
        days_until_long_term = LTCG_HOLDING_DAYS_THRESHOLD - holding_days
        taxable_gain_if_wait = max(0, gain_loss - LTCG_ANNUAL_EXEMPTION)
        tax_if_wait = round(taxable_gain_if_wait * LTCG_TAX_RATE, 2)
        potential_savings = round(tax_if_sold_now - tax_if_wait, 2)
        return {
            "holding_days": holding_days,
            "is_long_term": False,
            "tax_treatment": "STCG (20% flat)",
            "tax_if_sold_now": tax_if_sold_now,
            "days_until_long_term": days_until_long_term,
            "tax_if_wait_for_ltcg": tax_if_wait,
            "potential_tax_savings_by_waiting": potential_savings,
        }


def suggest_profit_booking(client_id: str) -> Dict[str, Any]:
    """
    Analyze a client's current holdings (live market prices + real
    purchase dates) and flag candidates for profit-booking or tax-loss
    harvesting, WITH real holding-period-aware tax treatment for each.

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with client_id, client_name, profit_booking_candidates
        (each with real STCG/LTCG tax detail), tax_loss_harvest_candidates
        (each flagged as STCL or LTCL, which offsets what), a summary
        note, and a tax_simplification_disclaimer
    """
    summary = get_portfolio_summary(client_id)

    if "error" in summary:
        return summary  # propagate the error as-is

    profit_candidates = []
    loss_candidates = []

    for holding in summary["holdings"]:
        pct = holding["gain_loss_pct"]
        purchase_date_str = holding.get("purchase_date")

        if pct >= PROFIT_BOOKING_THRESHOLD_PCT:
            tax_info = _tax_treatment_for_holding(holding["gain_loss"], purchase_date_str)

            if tax_info.get("is_long_term"):
                message = (
                    f"{holding['symbol']} is up {pct:.1f}% (₹{holding['gain_loss']:,.2f}) — "
                    f"already long-term ({tax_info['tax_treatment']}). Tax if sold today: "
                    f"₹{tax_info['tax_if_sold_now']:,.2f}."
                )
            else:
                message = (
                    f"{holding['symbol']} is up {pct:.1f}% (₹{holding['gain_loss']:,.2f}) — "
                    f"currently short-term ({tax_info['tax_treatment']}). Tax if sold today: "
                    f"₹{tax_info['tax_if_sold_now']:,.2f}. Waiting {tax_info['days_until_long_term']} "
                    f"more day(s) for long-term treatment could reduce tax to "
                    f"₹{tax_info['tax_if_wait_for_ltcg']:,.2f} "
                    f"(₹{tax_info['potential_tax_savings_by_waiting']:,.2f} potential savings)."
                )

            profit_candidates.append({
                "symbol": holding["symbol"],
                "gain_loss_pct": pct,
                "gain_loss": holding["gain_loss"],
                "tax_info": tax_info,
                "message": message,
            })

        elif pct <= TAX_LOSS_HARVEST_THRESHOLD_PCT:
            tax_info = _tax_treatment_for_holding(holding["gain_loss"], purchase_date_str)
            loss_type = "LTCL (Long-Term Capital Loss)" if tax_info.get("is_long_term") else "STCL (Short-Term Capital Loss)"
            offset_note = (
                "can offset LTCG only" if tax_info.get("is_long_term")
                else "can offset BOTH STCG and LTCG"
            )

            loss_candidates.append({
                "symbol": holding["symbol"],
                "gain_loss_pct": pct,
                "gain_loss": holding["gain_loss"],
                "loss_type": loss_type,
                "message": (
                    f"{holding['symbol']} is down {abs(pct):.1f}% (₹{holding['gain_loss']:,.2f}) — "
                    f"if realized, this is an {loss_type}, which {offset_note} elsewhere in the same financial year."
                ),
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
        "tax_simplification_disclaimer": (
            "Tax figures treat each holding's sale in isolation. The real ₹1.25 lakh LTCG "
            "exemption is an ANNUAL total across ALL equity LTCG in a financial year, not "
            "per-holding — actual tax owed depends on total realized gains for the year. "
            "Verify with a CA before acting."
        ),
    }


if __name__ == "__main__":
    # Quick manual test - run: python -m src.tools.profit_booking
    import json
    print(json.dumps(suggest_profit_booking("CLIENT_001"), indent=2))
