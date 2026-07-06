"""
NEW: End-User Investor Guidance (rule-based, explainable)

Answers "based on my age and how much I want to invest, what should my
risk profile and asset allocation look like?" for a GENERIC end user —
distinct from the 10 synthetic advisor-facing clients elsewhere in this
project. No client_id needed; this takes raw age/amount/goal directly
from a self-service investor.

DELIBERATELY RULE-BASED AND TRANSPARENT (same philosophy as
calc_risk_score and suggest_rebalancing elsewhere in this project) —
uses the well-known "100 minus age = equity %" rule of thumb, adjusted
for stated goal and time horizon. This is educational guidance, NOT
personalized financial advice, and is clearly labeled as such wherever
it's shown to the user.
"""

from typing import Dict, Any, Optional

VALID_GOALS = ["Retirement", "Wealth Growth", "Child Education", "Home Purchase", "Regular Income"]
VALID_HORIZONS = ["Short-term (<3 yrs)", "Medium-term (3-7 yrs)", "Long-term (>7 yrs)"]


def get_investment_guidance(age: int, investment_amount: float,
                             goal: str = "Wealth Growth",
                             time_horizon: Optional[str] = None) -> Dict[str, Any]:
    """
    Produce a rule-based, explainable risk profile and asset-allocation
    suggestion for a self-service investor based on age, investable
    amount, goal, and time horizon.

    Args:
        age: investor's age in years
        investment_amount: amount they want to invest, in INR
        goal: one of VALID_GOALS (defaults to "Wealth Growth" if unrecognized)
        time_horizon: one of VALID_HORIZONS, optional (inferred from age/goal if not given)

    Returns:
        dict with risk_category, allocation_pct, allocation_amount (INR),
        contributing_factors (plain-language explanation)
    """
    if goal not in VALID_GOALS:
        goal = "Wealth Growth"

    factors = []

    # Classic rule of thumb: equity % = 100 - age, capped to a sane range
    base_equity_pct = 100 - age
    base_equity_pct = max(10, min(90, base_equity_pct))
    factors.append(f"Starting point: 100 minus age ({age}) = {100 - age}% in equity (capped 10-90%)")

    # Infer time horizon from goal/age if not explicitly given
    if not time_horizon:
        if goal == "Retirement" or age >= 55:
            time_horizon = "Short-term (<3 yrs)" if age >= 60 else "Medium-term (3-7 yrs)"
        else:
            time_horizon = "Long-term (>7 yrs)"

    # Adjust for goal and horizon
    if goal == "Retirement" or time_horizon == "Short-term (<3 yrs)":
        base_equity_pct -= 15
        factors.append(f"Reduced by 15 points: goal/horizon ({goal}, {time_horizon}) favors capital preservation over growth")
    elif goal == "Wealth Growth" and time_horizon == "Long-term (>7 yrs)":
        base_equity_pct += 10
        factors.append(f"Increased by 10 points: goal/horizon ({goal}, {time_horizon}) allows more time to ride out volatility")

    equity_pct = max(10, min(90, base_equity_pct))
    remaining_pct = 100 - equity_pct

    # Split the non-equity remainder: majority safe debt instruments, some gold, small cash buffer
    debt_pct = round(remaining_pct * 0.70)
    gold_pct = round(remaining_pct * 0.15)
    cash_pct = 100 - equity_pct - debt_pct - gold_pct

    allocation_pct = {
        "Equity (Stocks)": equity_pct,
        "Debt (FD/RD/Bonds)": debt_pct,
        "Gold (Sovereign Gold Bond)": gold_pct,
        "Cash": cash_pct,
    }
    allocation_amount = {
        label: round(investment_amount * pct / 100, 2)
        for label, pct in allocation_pct.items()
    }

    if equity_pct >= 65:
        risk_category = "Aggressive"
    elif equity_pct >= 40:
        risk_category = "Moderate"
    else:
        risk_category = "Conservative"

    factors.append(f"Final equity allocation: {equity_pct}% → risk category: {risk_category}")

    return {
        "age": age,
        "investment_amount": round(investment_amount, 2),
        "goal": goal,
        "time_horizon": time_horizon,
        "risk_category": risk_category,
        "allocation_pct": allocation_pct,
        "allocation_amount": allocation_amount,
        "contributing_factors": factors,
        "disclaimer": (
            "This is educational, rule-based guidance only — not personalized "
            "financial advice. Consult a licensed financial advisor before "
            "making investment decisions."
        ),
    }


if __name__ == "__main__":
    import json
    print("--- Young investor, long-term wealth growth ---")
    print(json.dumps(get_investment_guidance(28, 100000, "Wealth Growth", "Long-term (>7 yrs)"), indent=2))

    print("\n--- Older investor, retirement ---")
    print(json.dumps(get_investment_guidance(58, 500000, "Retirement"), indent=2))
