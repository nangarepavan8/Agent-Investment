"""
NEW: Goal Gap Analysis

Answers the question a real advisor exists to answer: "am I on track
for my goal?" — not just "what's my portfolio worth today."

Projects current corpus + planned monthly contributions forward using
a CLEARLY-LABELED ASSUMED annual return (based on historical
asset-class averages for the risk category, not a prediction of what
will actually happen), compares to the target amount, and — if there's
a shortfall — computes the additional monthly SIP required to close
it using the standard future-value-of-annuity formula.

This is well-defined financial-planning arithmetic, not a forecast:
the same honesty pattern used throughout this project (see
calc_risk_score, suggest_rebalancing, growth_illustrator).
"""

from typing import Dict, Any

# Assumed long-term average annual returns by risk category — based on
# broad historical asset-class averages (a mix of equity/debt/gold
# consistent with each risk category's typical allocation), NOT a
# prediction of actual future returns for any specific investment.
ASSUMED_ANNUAL_RETURN_PCT = {
    "Conservative": 7.0,
    "Moderate": 10.0,
    "Aggressive": 12.0,
}


def calc_goal_gap(current_corpus: float, monthly_contribution: float,
                   target_amount: float, years: float,
                   risk_category: str = "Moderate") -> Dict[str, Any]:
    """
    Project current corpus + monthly contributions forward and compare
    to a target amount.

    Args:
        current_corpus: what's already invested/saved toward this goal, in INR
        monthly_contribution: planned ongoing monthly contribution, in INR
        target_amount: the goal amount needed, in INR
        years: years remaining until the goal date
        risk_category: "Conservative" | "Moderate" | "Aggressive" — determines
                       the assumed annual return used for projection

    Returns:
        dict with assumed_annual_return_pct, projected_corpus, target_amount,
        gap (positive = shortfall, negative = surplus), is_shortfall,
        required_additional_monthly_sip, disclaimer
    """
    years = max(years, 0.1)  # avoid division-by-zero edge cases
    rate_pct = ASSUMED_ANNUAL_RETURN_PCT.get(risk_category, 10.0)
    annual_rate = rate_pct / 100
    monthly_rate = annual_rate / 12
    months = years * 12

    # Future value of the current lump sum
    fv_corpus = current_corpus * ((1 + annual_rate) ** years)

    # Future value of an ordinary annuity (monthly contributions)
    if monthly_rate > 0:
        fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_contributions = monthly_contribution * months

    projected_corpus = fv_corpus + fv_contributions
    gap = round(target_amount - projected_corpus, 2)
    is_shortfall = gap > 0

    # If there's a shortfall, solve for the ADDITIONAL monthly SIP needed
    # to close it exactly (standard annuity-solve-for-payment formula)
    if is_shortfall:
        if monthly_rate > 0:
            required_additional_sip = gap / (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            required_additional_sip = gap / months
    else:
        required_additional_sip = 0.0

    return {
        "current_corpus": round(current_corpus, 2),
        "monthly_contribution": round(monthly_contribution, 2),
        "target_amount": round(target_amount, 2),
        "years": years,
        "risk_category": risk_category,
        "assumed_annual_return_pct": rate_pct,
        "projected_corpus": round(projected_corpus, 2),
        "gap": abs(gap),
        "is_shortfall": is_shortfall,
        "required_additional_monthly_sip": round(required_additional_sip, 2),
        "disclaimer": (
            f"Uses a CLEARLY-ASSUMED {rate_pct:.0f}%/year average return based on "
            f"broad historical asset-class averages for a {risk_category} risk "
            f"profile — this is an assumption for planning purposes, NOT a "
            f"prediction or guarantee of actual future returns."
        ),
    }


if __name__ == "__main__":
    import json
    # Example: 30-year-old, ₹5L already saved, ₹10k/month, wants ₹50L in 15 years
    result = calc_goal_gap(
        current_corpus=500000, monthly_contribution=10000,
        target_amount=5000000, years=15, risk_category="Moderate"
    )
    print(json.dumps(result, indent=2))
