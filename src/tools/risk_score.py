"""
Tool 2: Risk Score Calculator — upgraded to also factor in safe-asset
allocation (cash, FD, RD, bonds, government schemes).

Simple, explainable scoring (not a real quant model) — deliberately
transparent so it's easy to explain to judges:

    score = sector_concentration_penalty
          + single_position_concentration_penalty
          + risk_profile_bias
          - safe_asset_discount

Each factor is capped so the total stays within 0-100. The safe-asset
discount reflects a real principle: a client heavily concentrated in
one stock sector is genuinely less risky overall if they also hold
substantial FD/RD/bonds/cash elsewhere — risk should be assessed
across the FULL portfolio, not just the equity slice.
"""

from typing import Dict, Any
from src.tools.data_loader import get_client_holdings, get_client_info, get_client_other_investments
from src.tools.fixed_income import inr_to_usd

RISK_PROFILE_BIAS = {
    "Conservative": 0,
    "Moderate": 10,
    "Aggressive": 20,
}


def calc_risk_score(client_id: str) -> Dict[str, Any]:
    """
    Calculate a 0-100 risk score for a client's portfolio based on
    sector concentration, single-position concentration, the client's
    stated risk profile, and their safe-asset allocation (cash, FD,
    RD, bonds, government schemes offset stock-only concentration risk).

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with risk_score, risk_level, contributing_factors
    """
    client_info = get_client_info(client_id)
    holdings_df = get_client_holdings(client_id).copy()
    holdings_df["value"] = holdings_df["quantity"] * holdings_df["purchase_price"]

    total_value = holdings_df["value"].sum()
    factors = []

    # Factor 1: sector concentration — highest single-sector % of portfolio
    sector_pct = (holdings_df.groupby("sector")["value"].sum() / total_value * 100)
    max_sector_pct = sector_pct.max()
    top_sector = sector_pct.idxmax()

    if max_sector_pct >= 50:
        sector_penalty = 35
        factors.append(f"High concentration: {top_sector} makes up {max_sector_pct:.0f}% of portfolio")
    elif max_sector_pct >= 35:
        sector_penalty = 20
        factors.append(f"Moderate concentration: {top_sector} makes up {max_sector_pct:.0f}% of portfolio")
    else:
        sector_penalty = 5
        factors.append(f"Well diversified across sectors (largest: {top_sector} at {max_sector_pct:.0f}%)")

    # Factor 2: single-position concentration — highest single-stock % of portfolio
    position_pct = (holdings_df["value"] / total_value * 100)
    max_position_pct = position_pct.max()
    top_symbol = holdings_df.loc[position_pct.idxmax(), "symbol"]

    if max_position_pct >= 40:
        position_penalty = 25
        factors.append(f"Single-stock risk: {top_symbol} makes up {max_position_pct:.0f}% of portfolio")
    elif max_position_pct >= 25:
        position_penalty = 15
        factors.append(f"Some single-stock risk: {top_symbol} makes up {max_position_pct:.0f}% of portfolio")
    else:
        position_penalty = 5
        factors.append(f"No single position dominates (largest: {top_symbol} at {max_position_pct:.0f}%)")

    # Factor 3: stated risk profile bias
    profile_bias = RISK_PROFILE_BIAS.get(client_info["risk_profile"], 10)
    factors.append(f"Client risk profile on file: {client_info['risk_profile']}")

    # Factor 4: safe-asset allocation (cash + FD/RD/Bonds/govt schemes)
    # offsets pure stock-concentration risk, assessed across the FULL
    # portfolio. NOTE: cash/FD/RD/bonds are held in INR while stocks are
    # in USD (real US tickers) — convert to USD equivalent (fixed demo
    # rate) before comparing, otherwise rupees get miscounted as dollars.
    other_df = get_client_other_investments(client_id)
    safe_assets_inr = float(other_df["principal_amount"].sum()) + float(client_info.get("cash_balance", 0))
    safe_assets = inr_to_usd(safe_assets_inr)
    risky_assets = float(total_value)
    total_assets = safe_assets + risky_assets
    safe_ratio_pct = (safe_assets / total_assets * 100) if total_assets else 0

    if safe_ratio_pct >= 50:
        safe_asset_discount = 15
        factors.append(f"Substantial safe-asset allocation ({safe_ratio_pct:.0f}% in cash/FD/RD/bonds/govt schemes) reduces overall risk")
    elif safe_ratio_pct >= 25:
        safe_asset_discount = 8
        factors.append(f"Moderate safe-asset allocation ({safe_ratio_pct:.0f}% in cash/FD/RD/bonds/govt schemes)")
    else:
        safe_asset_discount = 0
        factors.append(f"Low safe-asset allocation ({safe_ratio_pct:.0f}% in cash/FD/RD/bonds/govt schemes) — most holdings are market-exposed")

    raw_score = sector_penalty + position_penalty + profile_bias - safe_asset_discount
    risk_score = max(0, min(100, raw_score))

    if risk_score >= 60:
        risk_level = "High"
    elif risk_score >= 35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "client_id": client_id,
        "client_name": client_info["name"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "contributing_factors": factors,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(calc_risk_score("CLIENT_001"), indent=2))
    print(json.dumps(calc_risk_score("CLIENT_003"), indent=2))
