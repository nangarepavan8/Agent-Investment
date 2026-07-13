"""
NEW: Swing Screener — Real Technical, Volume, and News Data

Answers "which stocks have unusual volume/technical activity right
now?" using REAL calculated technical indicators, REAL volume data,
and REAL news — organized like a multi-factor screener, but
DELIBERATELY WITHOUT synthesizing into a Buy/Sell signal, entry price,
stop-loss, price target, or confidence score.

WHY NO SIGNAL/TARGET/CONFIDENCE: short-term (swing) price direction
cannot be reliably predicted by anyone — including professional
quant funds with vastly more data and compute than this project has.
A "confidence score" on a buy signal would fabricate precision that
doesn't exist. This tool instead reports what's REAL and OBSERVABLE
today (indicator values, volume ratios, news) so a human can apply
their own judgment — same honesty pattern as every other tool in this
project (stock_screener, historical_performance, stress_test).

Technical indicators are computed with standard, well-known formulas
(RSI, MACD, EMA, Bollinger Bands, ADX, ATR) applied to REAL historical
price data — the calculation itself is pure, verifiable math, not a
prediction.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np
import yfinance as yf
from src.tools.yf_session import get_yf_session
from src.tools.historical_performance import _resolve_symbol
from src.tools.stock_screener import SCREENER_UNIVERSE, SYMBOL_TO_SECTOR


def _calc_rsi(close: pd.Series, period: int = 14) -> float:
    """Standard 14-period RSI (Relative Strength Index)."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    last_avg_gain = avg_gain.iloc[-1]
    last_avg_loss = avg_loss.iloc[-1]

    if pd.isna(last_avg_gain) or pd.isna(last_avg_loss):
        return None
    if last_avg_loss == 0:
        # No losses in the window: RSI is 100 if there were gains, 50 if flat
        return 100.0 if last_avg_gain > 0 else 50.0

    rs = last_avg_gain / last_avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


def _calc_macd(close: pd.Series) -> Dict[str, Any]:
    """Standard MACD: EMA12 - EMA26, with 9-period signal line."""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": round(float(macd_line.iloc[-1]), 2),
        "signal_line": round(float(signal_line.iloc[-1]), 2),
        "histogram": round(float(histogram.iloc[-1]), 2),
        "macd_above_signal": bool(macd_line.iloc[-1] > signal_line.iloc[-1]),
    }


def _calc_ema_status(close: pd.Series) -> Dict[str, Any]:
    """20 vs 50-period EMA — factual crossover state, not a signal."""
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    return {
        "ema20": round(float(ema20.iloc[-1]), 2),
        "ema50": round(float(ema50.iloc[-1]), 2),
        "ema20_above_ema50": bool(ema20.iloc[-1] > ema50.iloc[-1]),
        "price_above_ema20": bool(close.iloc[-1] > ema20.iloc[-1]),
    }


def _calc_bollinger(close: pd.Series, period: int = 20) -> Dict[str, Any]:
    """Standard 20-period Bollinger Bands (2 standard deviations)."""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    current_price = close.iloc[-1]
    band_width = upper.iloc[-1] - lower.iloc[-1]
    pct_position = ((current_price - lower.iloc[-1]) / band_width) if band_width else 0.5
    return {
        "upper_band": round(float(upper.iloc[-1]), 2),
        "middle_band": round(float(sma.iloc[-1]), 2),
        "lower_band": round(float(lower.iloc[-1]), 2),
        "pct_position_in_bands": round(float(pct_position) * 100, 1),  # 0=at lower, 100=at upper
    }


def _calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Standard 14-period Average True Range (volatility measure)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return round(float(atr.iloc[-1]), 2) if not pd.isna(atr.iloc[-1]) else None


def _calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Standard 14-period ADX (Average Directional Index) — trend STRENGTH, not direction."""
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low, (high - prev_close).abs(), (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=high.index).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=high.index).rolling(period).mean() / atr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(period).mean()
    return round(float(adx.iloc[-1]), 2) if not pd.isna(adx.iloc[-1]) else None


def _calc_volume_analysis(volume: pd.Series, period: int = 20) -> Dict[str, Any]:
    """Real current volume vs. the PRIOR period's average (excluding
    today, so today's volume isn't diluting its own baseline) —
    factual spike detection."""
    current_volume = volume.iloc[-1]
    prior_avg_volume = volume.iloc[-(period + 1):-1].mean()  # prior `period` days, excludes today
    spike_ratio = round(float(current_volume / prior_avg_volume), 2) if prior_avg_volume else None
    return {
        "current_volume": int(current_volume),
        "avg_volume_20d_prior": int(prior_avg_volume) if not pd.isna(prior_avg_volume) else None,
        "volume_spike_ratio": spike_ratio,
        "is_high_volume": bool(spike_ratio and spike_ratio >= 2.0),
    }


def _calc_range_position(close: pd.Series, high: pd.Series, low: pd.Series) -> Dict[str, Any]:
    """Factual proximity to 20-day and 50-day high/low — observation, not a breakout prediction."""
    current_price = close.iloc[-1]
    high_20d = high.rolling(20).max().iloc[-1]
    low_20d = low.rolling(20).min().iloc[-1]
    high_50d = high.rolling(50).max().iloc[-1] if len(high) >= 50 else high_20d
    return {
        "pct_from_20d_high": round(float((current_price - high_20d) / high_20d * 100), 2),
        "pct_from_20d_low": round(float((current_price - low_20d) / low_20d * 100), 2),
        "pct_from_50d_high": round(float((current_price - high_50d) / high_50d * 100), 2),
        "at_20d_high": bool(current_price >= high_20d * 0.995),
    }


def get_swing_analysis(symbol: str) -> Dict[str, Any]:
    """
    Full real-data swing screening analysis for one stock: technical
    indicators, volume analysis, range position, and news — NO Buy/
    Sell signal, NO price target, NO confidence score. Every number is
    real, calculated from real historical price/volume data.

    Args:
        symbol: e.g. "TCS.NS" or "TCS" (auto-resolves Indian exchange suffix)

    Returns:
        dict with resolved_symbol, current_price, technical indicators,
        volume analysis, range position, recent news, and a disclaimer
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        ticker = yf.Ticker(resolved_symbol, session=get_yf_session())
        hist = ticker.history(period="6mo")

        if hist.empty or len(hist) < 50:
            raise ValueError(f"Not enough historical data for '{symbol}' to compute indicators.")

        close, high, low, volume = hist["Close"], hist["High"], hist["Low"], hist["Volume"]

        technical = {
            "rsi_14": _calc_rsi(close),
            "macd": _calc_macd(close),
            "ema_status": _calc_ema_status(close),
            "bollinger_bands": _calc_bollinger(close),
            "atr_14": _calc_atr(high, low, close),
            "adx_14": _calc_adx(high, low, close),
        }
        volume_analysis = _calc_volume_analysis(volume)
        range_position = _calc_range_position(close, high, low)

        # Real recent news (reuse existing, already-tested logic)
        recent_headlines = []
        try:
            news_items = ticker.news or []
            for item in news_items[:3]:
                content = item.get("content", item)
                title = content.get("title")
                if title:
                    recent_headlines.append(title)
        except Exception:
            pass

        return {
            "symbol": symbol,
            "resolved_symbol": resolved_symbol,
            "current_price": round(float(close.iloc[-1]), 2),
            "technical": technical,
            "volume": volume_analysis,
            "range_position": range_position,
            "recent_headlines": recent_headlines,
            "disclaimer": (
                "All figures above are REAL, calculated from real historical price/volume "
                "data as of today. This is NOT a Buy/Sell signal, price target, or prediction "
                "of any kind — no one can reliably predict short-term price direction. Use "
                "your own judgment; this is a data screener, not trading advice."
            ),
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"Could not compute swing analysis: {str(e)}"}


def _screen_one_stock_swing(symbol: str) -> Dict[str, Any]:
    """
    Lighter per-stock version for batch screening — same real technical/
    volume/range calculations as get_swing_analysis(), but skips the
    news fetch (already shown in the single-stock view) to keep a
    multi-stock scan reasonably fast. Returns None on any failure so
    one bad ticker doesn't stop the whole screener.
    """
    try:
        ticker = yf.Ticker(symbol, session=get_yf_session())
        hist = ticker.history(period="6mo")

        if hist.empty or len(hist) < 50:
            return None

        close, high, low, volume = hist["Close"], hist["High"], hist["Low"], hist["Volume"]

        rsi = _calc_rsi(close)
        adx = _calc_adx(high, low, close)
        vol_analysis = _calc_volume_analysis(volume)
        range_position = _calc_range_position(close, high, low)
        ema_status = _calc_ema_status(close)

        # Factual flags only — describing TODAY's state, never a
        # "breakout is coming" prediction
        flags = []
        if vol_analysis["is_high_volume"]:
            flags.append("High Volume")
        if range_position["at_20d_high"]:
            flags.append("Near 20-Day High")
        if adx is not None and adx >= 25:
            flags.append("Strong Trend (ADX)")
        if ema_status["ema20_above_ema50"] and ema_status["price_above_ema20"]:
            flags.append("Above Both EMAs")

        return {
            "symbol": symbol,
            "sector": SYMBOL_TO_SECTOR.get(symbol, "Other"),
            "current_price": round(float(close.iloc[-1]), 2),
            "rsi_14": rsi,
            "adx_14": adx,
            "volume_spike_ratio": vol_analysis["volume_spike_ratio"],
            "pct_from_20d_high": range_position["pct_from_20d_high"],
            "flags": flags,
        }
    except Exception:
        return None


def get_swing_screener_by_sector(min_flags: int = 1) -> Dict[str, Any]:
    """
    Scan the full real stock universe for stocks currently showing
    high volume and/or proximity to their 20-day high, WITH their full
    real technical indicators — grouped by sector. Purely factual
    "what's happening today" flags — NEVER a breakout prediction, Buy/
    Sell signal, or price target.

    Args:
        min_flags: minimum number of factual flags a stock must have
                   to be included (default 1 — any real signal present)

    Returns:
        dict with sectors (dict of sector -> list of flagged stocks,
        each with full technical/volume/range data), disclaimer
    """
    results = []
    for symbol in SCREENER_UNIVERSE:
        screened = _screen_one_stock_swing(symbol)
        if screened and len(screened["flags"]) >= min_flags:
            results.append(screened)

    # Sort within the full list by volume spike ratio, highest first —
    # a factual ranking (most unusual volume today), not a signal ranking
    results.sort(key=lambda r: -(r["volume_spike_ratio"] or 0))

    sectors: Dict[str, list] = {}
    for stock in results:
        sectors.setdefault(stock["sector"], []).append(stock)

    return {
        "sectors": sectors,
        "total_flagged": len(results),
        "universe_size": len(SCREENER_UNIVERSE),
        "disclaimer": (
            "These stocks show REAL, CURRENT high volume and/or proximity to their "
            "20-day high — factual observations about TODAY only. This is NOT a list "
            "of stocks that will break out, and NOT a Buy/Sell signal. No one can "
            "reliably predict whether a real breakout will follow."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_swing_analysis("TCS.NS"), indent=2))
