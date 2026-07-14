"""
NEW: Gold Analysis — Real Price, Real Technical Indicators, No Predictions

Answers "what's happening with gold right now?" honestly: real
current price (USD/oz via COMEX futures, converted to an approximate
INR/10g figure using the real live USD/INR rate), real technical
indicators (reusing the exact same tested RSI/MACD/EMA/Bollinger/ATR/
ADX functions already used for stocks), and real Sovereign Gold Bond
facts — WITHOUT a specific buy/sell price target, entry/exit level, or
"AI predicts" signal. Same honesty pattern as every other tool here.

The INR/10g conversion is a real, verifiable UNIT CONVERSION (troy
ounces to grams, USD to INR at the live rate) — not a prediction. It
will differ slightly from actual Indian bullion market rates (which
include import duty, GST, and dealer premiums this doesn't account
for), which is stated clearly in the disclaimer.
"""

from typing import Dict, Any
import yfinance as yf
from src.tools.yf_session import get_yf_session
from src.tools.swing_screener import (
    _calc_rsi, _calc_macd, _calc_ema_status, _calc_bollinger,
    _calc_atr, _calc_adx, _calc_indicator_tally,
)

GOLD_FUTURES_TICKER = "GC=F"  # COMEX Gold Futures, USD per troy ounce
USDINR_TICKER = "USDINR=X"
TROY_OZ_TO_GRAMS = 31.1035

SGB_FACTS = {
    "what_it_is": (
        "Sovereign Gold Bond (SGB) — a government-issued bond denominated in grams of "
        "gold, an alternative to holding physical gold."
    ),
    "benefits": [
        "2.5% fixed annual interest, paid on top of any gold price movement",
        "No making charges or storage risk, unlike physical gold",
        "Capital gains are tax-free if held to maturity (8 years)",
        "Backed by the Government of India",
    ],
    "tradeoffs": [
        "8-year tenure (early exit only after year 5, or via exchange trading)",
        "Gold price can fall — SGBs are NOT protected against gold price declines",
        "New tranches are issued periodically by RBI, not always available on-demand",
    ],
}


def get_gold_analysis() -> Dict[str, Any]:
    """
    Real gold price and technical analysis — current price (USD/oz and
    approximate INR/10g), real technical indicators, an indicator
    tally (factual count, NOT a buy/sell signal), and Sovereign Gold
    Bond facts. NO price target, NO "buy at X / sell at Y" level.

    Returns:
        dict with prices, technical indicators, indicator_tally, sgb_facts,
        disclaimer
    """
    try:
        gold_ticker = yf.Ticker(GOLD_FUTURES_TICKER, session=get_yf_session())
        hist = gold_ticker.history(period="6mo")

        if hist.empty or len(hist) < 50:
            raise ValueError("Not enough historical gold price data available right now.")

        close, high, low = hist["Close"], hist["High"], hist["Low"]
        current_price_usd_oz = round(float(close.iloc[-1]), 2)

        # Real unit conversion: USD/oz -> INR/10g using the live USD/INR rate
        inr_per_10g = None
        try:
            fx_ticker = yf.Ticker(USDINR_TICKER, session=get_yf_session())
            fx_info = fx_ticker.info
            usd_inr_rate = fx_info.get("regularMarketPrice") or fx_info.get("currentPrice")
            if usd_inr_rate:
                price_per_gram_usd = current_price_usd_oz / TROY_OZ_TO_GRAMS
                inr_per_10g = round(price_per_gram_usd * usd_inr_rate * 10, 2)
        except Exception:
            pass

        technical = {
            "rsi_14": _calc_rsi(close),
            "macd": _calc_macd(close),
            "ema_status": _calc_ema_status(close),
            "bollinger_bands": _calc_bollinger(close),
            "atr_14": _calc_atr(high, low, close),
            "adx_14": _calc_adx(high, low, close),
        }
        indicator_tally = _calc_indicator_tally(technical)

        # Real historical change (backward-looking only, same pattern as historical_performance.py)
        periods = {"1_month": 21, "3_month": 63, "6_month": len(close) - 1}
        historical_changes = {}
        for label, days_back in periods.items():
            idx = max(0, len(close) - 1 - days_back)
            past_price = float(close.iloc[idx])
            change_pct = round(((current_price_usd_oz - past_price) / past_price) * 100, 2)
            historical_changes[label] = change_pct

        return {
            "current_price_usd_per_oz": current_price_usd_oz,
            "current_price_inr_per_10g_approx": inr_per_10g,
            "technical": technical,
            "indicator_tally": indicator_tally,
            "historical_change_pct": historical_changes,
            "sgb_facts": SGB_FACTS,
            "disclaimer": (
                "All figures are REAL, calculated from real gold futures price data as of "
                "today. The INR/10g figure is an approximate unit conversion (does NOT "
                "include import duty, GST, or dealer premiums — actual Indian bullion "
                "prices will differ). This is NOT a buy/sell signal, price target, or "
                "prediction — no one can reliably predict gold's future price."
            ),
        }
    except Exception as e:
        return {"error": f"Could not fetch gold analysis: {str(e)}"}


if __name__ == "__main__":
    import json
    print(json.dumps(get_gold_analysis(), indent=2))
