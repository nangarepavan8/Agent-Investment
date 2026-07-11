"""
NEW: Historical Stress-Test

Answers the emotionally real question every client asks — "what if
the market crashes?" — HONESTLY: by replaying REAL historical
drawdown periods against a client's ACTUAL current holdings, using
REAL historical prices for those same stocks. This is purely backward-
looking, zero prediction — the same honesty pattern as
historical_performance.py and growth_illustrator.py elsewhere in this
project.

For each of the client's current stock holdings, this fetches the
REAL price at the start and end of a historical stress period (e.g.
the COVID-19 crash) and applies that SAME real percentage change to
the holding's CURRENT value — showing what a similarly-sized shock
would do to today's portfolio, not predicting that it will happen.

Non-stock assets (FD/RD/Bonds/schemes, cash) are treated as unaffected
by market stress, consistent with their fixed-return, government-
backed nature — a reasonable simplification stated explicitly.
"""

from typing import Dict, Any
import yfinance as yf
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.yf_session import get_yf_session

# Real historical drawdown periods (Indian market context)
STRESS_SCENARIOS = {
    "COVID Crash (Feb-Mar 2020)": {"start": "2020-02-01", "end": "2020-03-23"},
    "2022 Market Correction (Jan-Jun 2022)": {"start": "2022-01-01", "end": "2022-06-17"},
}


def _get_real_historical_change_pct(symbol: str, start: str, end: str):
    """Fetch the REAL % change for one stock over a historical date range.
    Returns None on any failure (missing data, delisted, etc.)."""
    try:
        ticker = yf.Ticker(symbol, session=get_yf_session())
        hist = ticker.history(start=start, end=end)
        if hist.empty or len(hist) < 2:
            return None
        start_price = float(hist["Close"].iloc[0])
        end_price = float(hist["Close"].iloc[-1])
        return round(((end_price - start_price) / start_price) * 100, 2)
    except Exception:
        return None


def run_stress_test(client_id: str, scenario_name: str) -> Dict[str, Any]:
    """
    Replay a real historical drawdown against a client's actual current
    holdings.

    Args:
        client_id: e.g. "CLIENT_001"
        scenario_name: one of STRESS_SCENARIOS' keys

    Returns:
        dict with scenario details, per-holding stressed values, total
        current vs. stressed portfolio value (including unaffected
        safe assets), and a clear "this is historical replay, not a
        prediction" disclaimer
    """
    if scenario_name not in STRESS_SCENARIOS:
        return {"error": f"Unknown scenario '{scenario_name}'. Valid options: {list(STRESS_SCENARIOS.keys())}"}

    summary = get_portfolio_summary(client_id)
    if "error" in summary:
        return summary

    scenario = STRESS_SCENARIOS[scenario_name]
    holding_results = []
    stressed_stock_total = 0.0
    current_stock_total = 0.0
    any_missing_data = False

    for holding in summary["holdings"]:
        symbol = holding["symbol"]
        current_value = holding["current_value"]
        change_pct = _get_real_historical_change_pct(symbol, scenario["start"], scenario["end"])

        if change_pct is None:
            # Graceful fallback: assume no change for this one holding
            # rather than failing the whole stress test, but flag it
            stressed_value = current_value
            any_missing_data = True
        else:
            stressed_value = round(current_value * (1 + change_pct / 100), 2)

        current_stock_total += current_value
        stressed_stock_total += stressed_value

        holding_results.append({
            "symbol": symbol,
            "current_value": current_value,
            "historical_change_pct": change_pct,
            "stressed_value": stressed_value,
            "data_available": change_pct is not None,
        })

    # Safe assets (FD/RD/Bonds/schemes/cash) assumed unaffected by market stress
    safe_assets_value = summary["total_value"] - current_stock_total

    current_total = round(current_stock_total + safe_assets_value, 2)
    stressed_total = round(stressed_stock_total + safe_assets_value, 2)
    total_drawdown = round(stressed_total - current_total, 2)
    total_drawdown_pct = round((total_drawdown / current_total) * 100, 2) if current_total else 0.0

    return {
        "client_id": client_id,
        "client_name": summary["client_name"],
        "scenario": scenario_name,
        "scenario_period": f"{scenario['start']} to {scenario['end']}",
        "current_total_value": current_total,
        "stressed_total_value": stressed_total,
        "total_drawdown": total_drawdown,
        "total_drawdown_pct": total_drawdown_pct,
        "safe_assets_unaffected": round(safe_assets_value, 2),
        "holding_results": holding_results,
        "any_missing_data": any_missing_data,
        "disclaimer": (
            "This replays REAL historical price movements from this period against your "
            "CURRENT holdings — it is a backward-looking illustration, NOT a prediction "
            "that a similar event will happen again. FD/RD/Bonds/cash are assumed "
            "unaffected, consistent with their fixed-return nature."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_stress_test("CLIENT_001", "COVID Crash (Feb-Mar 2020)"), indent=2))
