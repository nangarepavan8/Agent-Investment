"""
Tool 1: Portfolio Summary — upgraded with real-time market pricing AND
full asset-class coverage (stocks, Fixed Deposits, Recurring Deposits,
Corporate Bonds, PPF, NSC, Sovereign Gold Bonds, and cash).

IMPORTANT UPGRADE #1: originally, "value" was calculated at purchase
price (cost basis). This version fetches LIVE current prices per stock
holding via yfinance and computes both current market value and
unrealized gain/loss vs. cost basis.

IMPORTANT UPGRADE #2: a real client's portfolio isn't just stocks —
this now includes non-stock instruments (FD/RD/Bonds/government
schemes) valued via src.tools.fixed_income, plus uninvested cash, so
"what is this client's total net worth under management" is answered
correctly across the FULL portfolio, not just the equity slice.

If a live stock price can't be fetched (network issue, rate limit,
delisted ticker), that holding gracefully falls back to its purchase
price and is flagged "price_is_live": False, so the rest of the
portfolio still renders correctly instead of the whole tool failing.
"""

from typing import Dict, Any
import yfinance as yf
from src.tools.data_loader import get_client_holdings, get_client_info, get_client_other_investments
from src.tools.fixed_income import value_instrument


def _get_live_price(symbol: str):
    """Fetch current price for one symbol. Returns None on any failure."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        return float(price) if price else None
    except Exception:
        return None


def get_portfolio_summary(client_id: str) -> Dict[str, Any]:
    """
    Return a full summary of a client's portfolio across ALL asset
    classes: stocks (real-time priced), Fixed Deposits, Recurring
    Deposits, Corporate Bonds, government schemes (PPF/NSC/Sovereign
    Gold Bond), and uninvested cash.

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with total_value (grand total across everything),
        total_cost_basis, total_gain_loss, total_gain_loss_pct,
        holdings (stocks), other_investments (FD/RD/Bond/govt schemes),
        cash_balance, sector_allocation (within stocks),
        asset_allocation (across ALL asset classes)
    """
    client_info = get_client_info(client_id)

    # --- Stocks (real-time priced) ---
    holdings_df = get_client_holdings(client_id).copy()
    holdings_df["cost_basis"] = holdings_df["quantity"] * holdings_df["purchase_price"]

    unique_symbols = holdings_df["symbol"].unique()
    live_prices = {symbol: _get_live_price(symbol) for symbol in unique_symbols}

    holdings_list = []
    stocks_current_value = 0.0
    stocks_cost_basis = 0.0

    for _, row in holdings_df.iterrows():
        symbol = row["symbol"]
        quantity = int(row["quantity"])
        cost_basis = round(row["cost_basis"], 2)
        live_price = live_prices.get(symbol)

        if live_price is not None:
            current_value = round(quantity * live_price, 2)
            price_is_live = True
        else:
            current_value = cost_basis
            price_is_live = False

        gain_loss = round(current_value - cost_basis, 2)
        gain_loss_pct = round((gain_loss / cost_basis) * 100, 2) if cost_basis else 0.0

        stocks_current_value += current_value
        stocks_cost_basis += cost_basis

        holdings_list.append({
            "symbol": symbol,
            "sector": row["sector"],
            "quantity": quantity,
            "purchase_date": row.get("purchase_date"),
            "cost_basis": cost_basis,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "price_is_live": price_is_live,
        })

    # --- Non-stock instruments: FD, RD, Corporate Bonds, PPF, NSC, SGB ---
    other_df = get_client_other_investments(client_id)
    other_investments_list = []
    other_current_value = 0.0
    other_cost_basis = 0.0

    for _, row in other_df.iterrows():
        valuation = value_instrument(
            instrument_type=row["instrument_type"],
            principal_amount=row["principal_amount"],
            annual_interest_rate=row["annual_interest_rate"],
            start_date_str=row["start_date"],
            tenure_years=row["tenure_years"],
        )
        current_value = valuation["current_value"]
        principal = round(row["principal_amount"], 2)
        gain_loss = round(current_value - principal, 2)

        other_current_value += current_value
        other_cost_basis += principal

        other_investments_list.append({
            "instrument_type": row["instrument_type"],
            "principal_amount": principal,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "annual_interest_rate": row["annual_interest_rate"],
            "start_date": row["start_date"],
            "tenure_years": row["tenure_years"],
            "years_elapsed": valuation["years_elapsed"],
            "is_matured": valuation["is_matured"],
        })

    # --- Cash (no gain/loss, just uninvested balance) ---
    # Stocks, cash, and FD/RD/Bonds/schemes are ALL in INR now (real
    # Indian tickers via NSE) — no currency conversion needed.
    cash_balance_inr = round(float(client_info["cash_balance"]), 2)

    # --- Grand totals across ALL asset classes (all INR) ---
    total_current_value = round(stocks_current_value + other_current_value + cash_balance_inr, 2)
    total_cost_basis = round(stocks_cost_basis + other_cost_basis + cash_balance_inr, 2)
    total_gain_loss = round(total_current_value - total_cost_basis, 2)
    total_gain_loss_pct = round((total_gain_loss / total_cost_basis) * 100, 2) if total_cost_basis else 0.0

    # --- Sector allocation (within STOCKS only — doesn't apply to FD/RD/etc.) ---
    sector_current_totals = {}
    for h in holdings_list:
        sector_current_totals[h["sector"]] = sector_current_totals.get(h["sector"], 0) + h["current_value"]
    sector_allocation = {
        sector: round((value / stocks_current_value) * 100, 1)
        for sector, value in sector_current_totals.items()
    } if stocks_current_value else {}

    # --- Asset-class allocation (across EVERYTHING — the bigger picture) ---
    asset_totals = {"Stocks": round(stocks_current_value, 2)}
    for inv in other_investments_list:
        asset_totals[inv["instrument_type"]] = asset_totals.get(inv["instrument_type"], 0) + inv["current_value"]
    if cash_balance_inr:
        asset_totals["Cash"] = cash_balance_inr

    asset_allocation = {
        asset_type: round((value / total_current_value) * 100, 1)
        for asset_type, value in asset_totals.items()
    } if total_current_value else {}

    any_stale_prices = any(not h["price_is_live"] for h in holdings_list)

    return {
        "client_id": client_id,
        "client_name": client_info["name"],
        "risk_profile": client_info["risk_profile"],
        "age": int(client_info.get("age")) if client_info.get("age") is not None else None,
        "investment_goal": client_info.get("investment_goal"),
        "time_horizon": client_info.get("time_horizon"),
        "total_value": total_current_value,
        "total_value_currency_note": "All figures in INR (₹) — stocks are real NSE-listed Indian tickers, consistent with cash/FD/RD/bonds/schemes.",
        "total_cost_basis": total_cost_basis,
        "total_gain_loss": total_gain_loss,
        "total_gain_loss_pct": total_gain_loss_pct,
        "cash_balance_inr": cash_balance_inr,
        "holdings": holdings_list,
        "other_investments": other_investments_list,
        "sector_allocation": sector_allocation,
        "asset_allocation": asset_allocation,
        "note": "Some stock prices could not be fetched live and fall back to purchase price."
                if any_stale_prices else None,
    }


if __name__ == "__main__":
    # Quick manual test - run: python -m src.tools.portfolio_summary
    import json
    print(json.dumps(get_portfolio_summary("CLIENT_003"), indent=2))
