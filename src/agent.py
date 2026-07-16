"""
DAY 4: The Agentic Core

Wraps the 4 existing tool functions as LangChain @tool-decorated
functions, then builds a GPT-4o powered agent that reads the user's
natural-language query, decides which tool(s) to call, executes them,
and synthesizes a final answer.

This is the heart of the "agentic" story: the LLM is not just
generating text — it's reasoning about which specialized function to
invoke based on user intent, exactly like the hackathon brief asks for.
"""

import json
import time
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.tools.rebalancing import suggest_rebalancing
from src.tools.market_context import get_market_context
from src.tools.profit_booking import suggest_profit_booking
from src.tools.sector_performance import get_sector_performance
from src.tools.investor_guidance import get_investment_guidance
from src.tools.historical_performance import get_historical_returns
from src.tools.stock_screener import get_stock_screener
from src.tools.growth_illustrator import get_hypothetical_growth
from src.tools.goal_gap_analysis import calc_goal_gap
from src.tools.tax_guidance import get_capital_gains_rules, get_tax_saving_instruments
from src.tools.stress_test import run_stress_test, STRESS_SCENARIOS
from src.tools.swing_screener import get_swing_analysis, get_swing_screener_by_sector
from src.tools.nse_live_data import get_nse_most_active_by_volume
from src.tools.premarket_briefing import get_premarket_briefing
from src.tools.gold_analysis import get_gold_analysis
from src.tools.mutual_fund_data import search_mutual_funds, calc_sip_future_value, MUTUAL_FUND_EDUCATION
from src.tools.mutual_fund_analysis import get_mutual_fund_historical_returns
from src.tools.investing_news import get_aggregated_investing_news
from src.tools.client_management import add_client, add_holding, add_other_investment, list_user_added_clients
from src.memory import store_memory, retrieve_relevant_memory
from src.audit_log import log_event


# ---------------------------------------------------------------------------
# Wrap each existing tool function with LangChain's @tool decorator.
# The docstring here is what GPT-4o reads to decide WHEN to call each tool,
# so keep them clear and specific.
# ---------------------------------------------------------------------------

@tool
def portfolio_summary_tool(client_id: str) -> str:
    """Get a FULL summary of a client's portfolio across ALL asset
    classes: stocks (real-time priced), Fixed Deposits, Recurring
    Deposits, Corporate Bonds, government schemes (PPF/NSC/Sovereign
    Gold Bond), and uninvested cash. Includes current market value,
    unrealized gain/loss vs. cost basis, client profile (age,
    investment goal, time horizon), and both sector allocation
    (within stocks) and asset-class allocation (across everything).
    Use this when the user asks what a portfolio contains, its current
    worth, whether the client is up or down, which holdings are
    performing well, how much cash/FD/RD/bonds a client holds, or how
    it's allocated. client_id must be in the format CLIENT_001 through
    CLIENT_010."""
    try:
        return json.dumps(get_portfolio_summary(client_id))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def risk_score_tool(client_id: str) -> str:
    """Calculate a 0-100 risk score for a client's portfolio, including
    the risk level (Low/Medium/High) and the specific factors driving
    that score. Use this when the user asks how risky a portfolio is
    or wants a risk assessment. client_id must be in the format
    CLIENT_001 through CLIENT_010."""
    try:
        return json.dumps(calc_risk_score(client_id))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def rebalancing_tool(client_id: str) -> str:
    """Suggest specific portfolio rebalancing actions to reduce
    concentration risk, comparing current vs. target sector allocation.
    Use this when the user asks how to rebalance, diversify, or adjust
    a portfolio. client_id must be in the format CLIENT_001 through
    CLIENT_010."""
    try:
        return json.dumps(suggest_rebalancing(client_id))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def market_context_tool(symbol: str) -> str:
    """Get live public market data, fundamentals, analyst sentiment, and
    recent news for a stock symbol. Use this for ANY question about a
    specific stock — current price, valuation (P/E, market cap), analyst
    recommendations, recent news/sentiment, or open-ended questions like
    "should I invest in X" or "what's the outlook for X". Works for US
    tickers (AAPL, MSFT) and Indian tickers (TCS, INFY — automatically
    tries NSE/.NS and BSE/.BO suffixes). This tool does NOT predict
    future prices — it returns factual data for the agent to summarize."""
    try:
        return json.dumps(get_market_context(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def profit_booking_tool(client_id: str) -> str:
    """Identify which of a client's holdings are candidates for booking
    profit (significant unrealized gains) or tax-loss harvesting
    (significant unrealized losses), based on REAL current market
    prices vs. purchase price. NOW TAX-AWARE: for each candidate,
    shows real holding-period-based STCG (20%) vs LTCG (12.5% above
    ₹1.25L exemption) tax treatment, the tax if sold today, and — for
    still-short-term gains — the potential tax saved by waiting for
    long-term treatment. Loss candidates are flagged as STCL or LTCL
    with what they can offset. Use this when the user asks which
    stocks to sell, take profit on, or harvest losses from, or about
    the tax impact of selling now vs. waiting. client_id must be in
    the format CLIENT_001 through CLIENT_010."""
    try:
        return json.dumps(suggest_profit_booking(client_id))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def sector_performance_tool(sector_name: str = None) -> str:
    """Get REAL, LIVE today's performance for Nifty sector indices (IT,
    Banking, Automobile, Pharma, FMCG, Energy, Metal, Realty). Use this
    when the user asks how a sector is doing today, which sector is
    performing best/worst, or wants a market-wide sector comparison —
    NOT for a specific client's portfolio sector allocation (use
    portfolio_summary_tool for that instead). Pass sector_name for one
    specific sector, or omit it to get all sectors."""
    try:
        return json.dumps(get_sector_performance(sector_name))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def investment_guidance_tool(age: int, investment_amount: float, goal: str = "Wealth Growth",
                              time_horizon: str = None) -> str:
    """Get rule-based, explainable risk profile and asset-allocation
    guidance for a SELF-SERVICE investor (not one of the CLIENT_001-010
    advisor clients) based on their own age, amount to invest, goal,
    and time horizon. Use this when a general investor (not an advisor
    asking about a specific client) asks how they should allocate
    their money, what their risk profile should be, or how to invest
    based on their age/amount. goal must be one of: Retirement, Wealth
    Growth, Child Education, Home Purchase, Regular Income."""
    try:
        return json.dumps(get_investment_guidance(age, investment_amount, goal, time_horizon))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def historical_performance_tool(symbol: str) -> str:
    """Get REAL historical 1/2/3-year returns for a stock (a look
    BACKWARD at actual past performance, never a prediction of future
    performance). Use this when the user asks how a stock has actually
    performed historically, or wants to see real past returns before
    making a decision."""
    try:
        return json.dumps(get_historical_returns(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def stock_screener_tool(risk_category: str = "Moderate", preferred_sectors: list = None) -> str:
    """Screen real, current stock market data (proximity to 52-week
    high, P/E valuation, recent earnings growth) across a fixed
    universe of real Indian stocks, sorted by relevance to a risk
    category. Each result includes its sector, the stock name, and a
    plain-language reason based on REAL current data (never a future
    claim). Use this when a self-service investor asks for stock
    ideas, a screener, or "what stocks fit my risk profile". Optionally
    pass preferred_sectors (e.g. ["IT", "Banking"]) to filter to
    specific sectors of interest — if not given, screens all sectors.
    risk_category must be Conservative, Moderate, or Aggressive."""
    try:
        return json.dumps(get_stock_screener(risk_category, preferred_sectors=preferred_sectors))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def growth_illustrator_tool(symbol: str, investment_amount: float, years: int = 4) -> str:
    """Illustrate a HYPOTHETICAL year-by-year value if a stock's real
    historical average annual return continued — this is explicitly
    NOT a prediction or forecast, always present it with that framing.
    Use this when a user wants to visualize/graph how an investment
    amount might hypothetically grow over 1-4 years based on past
    average performance. years must be 1-4."""
    try:
        return json.dumps(get_hypothetical_growth(symbol, investment_amount, years))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def goal_gap_analysis_tool(current_corpus: float, monthly_contribution: float,
                           target_amount: float, years: float, risk_category: str = "Moderate") -> str:
    """Answer 'am I on track for my goal?' — projects current corpus
    plus monthly contributions forward using a CLEARLY-ASSUMED average
    annual return (based on historical asset-class averages for the
    risk category, NOT a prediction), compares to a target amount, and
    if there's a shortfall, calculates the additional monthly SIP
    needed to close it exactly (standard financial-planning formula).
    Use this when a user asks if they'll reach a specific goal amount,
    whether they're on track, or how much more they need to save
    monthly. risk_category must be Conservative, Moderate, or
    Aggressive."""
    try:
        return json.dumps(calc_goal_gap(current_corpus, monthly_contribution, target_amount, years, risk_category))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def capital_gains_tax_tool(asset_type: str = None) -> str:
    """Get current REAL, RESEARCHED Indian capital gains tax rules
    (LTCG/STCG rates and holding periods) for equity shares/mutual
    funds, debt mutual funds, real estate, or gold/international funds.
    This is a dated snapshot (clearly labeled), not a live feed — always
    pass along the disclaimer to verify with a CA for time-sensitive
    decisions. Use this when a user asks about capital gains tax,
    LTCG/STCG rates, or how a specific asset type is taxed. asset_type
    must be one of: equity_shares_and_equity_mutual_funds,
    debt_mutual_funds, real_estate, gold_and_international_funds — or
    omit it for all asset types."""
    try:
        return json.dumps(get_capital_gains_rules(asset_type))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def tax_saving_instruments_tool() -> str:
    """Get current REAL, RESEARCHED Section 80C tax-saving instrument
    details (ELSS, PPF, EPF, NSC, tax-saver FDs, SSY, life insurance,
    home loan principal, tuition fees) — the ₹1.5 lakh combined limit,
    lock-in periods, and characteristics of each. This is a dated
    snapshot (clearly labeled), not a live feed. Use this when a user
    asks how to save tax, what to invest in for tax deduction, or
    about Section 80C / ELSS / PPF specifically."""
    try:
        return json.dumps(get_tax_saving_instruments())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def stress_test_tool(client_id: str, scenario_name: str) -> str:
    """Replay a REAL historical market drawdown (e.g. the 2020 COVID
    crash or 2022 correction) against a client's ACTUAL CURRENT
    holdings, using REAL historical prices for those same stocks —
    this is a backward-looking illustration of "what if a similar
    shock happened again," NEVER a prediction that it will. Use this
    when a client/advisor asks "what if the market crashes", wants to
    see how their portfolio would have handled a past crisis, or asks
    about downside risk. scenario_name must be one of: "COVID Crash
    (Feb-Mar 2020)" or "2022 Market Correction (Jan-Jun 2022)".
    client_id must be in the format CLIENT_001 through CLIENT_010."""
    try:
        return json.dumps(run_stress_test(client_id, scenario_name))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def swing_analysis_tool(symbol: str) -> str:
    """Get REAL, current technical indicators (RSI, MACD, EMA crossover,
    Bollinger Bands, ATR, ADX), volume spike analysis, price-range
    position, and recent news for a stock — for swing/short-term
    analysis. This returns REAL CALCULATED DATA ONLY — it does NOT
    provide a Buy/Sell signal, entry price, stop-loss, price target,
    or confidence score, because short-term price direction cannot be
    reliably predicted. Use this when a user asks for technical
    analysis, volume spikes, swing trading data, or "is this stock
    showing unusual activity" for a specific stock."""
    try:
        return json.dumps(get_swing_analysis(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def swing_screener_by_sector_tool(min_flags: int = 1) -> str:
    """Scan a broad real stock universe (~65 Indian stocks across 18
    sectors) for ones currently showing high volume and/or proximity
    to their 20-day high, grouped by sector, WITH their real technical
    indicators (RSI, ADX, volume spike ratio). Purely factual "what's
    happening today" flags — NOT a breakout prediction, NOT a Buy/Sell
    signal, NOT a price target. Use this when a user asks for a list/
    screener of stocks with high volume, near their highs, or a
    sector-wise swing/technical scan — as opposed to swing_analysis_tool
    which covers just ONE specific stock in more depth."""
    try:
        return json.dumps(get_swing_screener_by_sector(min_flags))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def nse_live_volume_tool(count: int = 20) -> str:
    """Attempt to fetch REAL, live 'Most Active by Volume' data
    directly from NSE — covers the ENTIRE exchange (thousands of
    stocks), not a fixed list. EXPERIMENTAL: depends on NSE's
    unofficial public data feed and may fail if blocked or if NSE
    changes their site structure — if it errors, fall back to
    swing_screener_by_sector_tool (broad ~65-stock universe) or
    suggest the user search a specific known symbol directly via
    swing_analysis_tool. Use this when a user explicitly wants
    coverage beyond the fixed stock list, or mentions a stock ticker
    you don't recognize from the fixed universe."""
    try:
        return json.dumps(get_nse_most_active_by_volume(count))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def premarket_briefing_tool() -> str:
    """Get a REAL pre-market briefing: overnight US market performance
    (Dow, Nasdaq, S&P 500), crude oil, USD/INR movement, and Nifty
    50's last real close — factual, backward-looking data about what
    already happened overnight, the same cues real financial
    briefings cover before market open. This does NOT predict what
    Indian markets or any stock will do today. Use this when a user
    asks "what should I check before market opens", wants a pre-market
    summary, or asks about overnight global cues."""
    try:
        return json.dumps(get_premarket_briefing())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def gold_analysis_tool() -> str:
    """Get REAL gold price analysis: current price (USD/oz and
    approximate INR/10g via live unit conversion), real technical
    indicators (RSI, MACD, EMA, Bollinger, ATR, ADX), a factual
    indicator tally, real historical change, and Sovereign Gold Bond
    facts. This does NOT provide a buy/sell price target or
    prediction — no one can reliably predict gold's future price.
    Use this when a user asks about gold, gold prices, SGB, or wants
    gold technical analysis."""
    try:
        return json.dumps(get_gold_analysis())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mutual_fund_historical_returns_tool(scheme_code: str) -> str:
    """Get REAL historical 1/3/5-year returns for a specific mutual
    fund scheme (use mutual_fund_search_tool first to find the scheme
    code). Backward-looking only, NOT a prediction of future fund
    performance. Use this when a user asks how a specific mutual fund
    has performed historically."""
    try:
        return json.dumps(get_mutual_fund_historical_returns(scheme_code))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mutual_fund_search_tool(keyword: str) -> str:
    """Search REAL, current mutual fund NAV data sourced directly from
    AMFI (Association of Mutual Funds in India) — covers actual Indian
    mutual fund schemes, not invented data. EXPERIMENTAL: depends on
    AMFI's public data feed staying available. Use this when a user
    asks to find/look up a specific mutual fund by name or keyword
    (e.g. "HDFC", "Nifty Index", "ELSS")."""
    try:
        return json.dumps(search_mutual_funds(keyword))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def sip_calculator_tool(monthly_amount: float, years: float, assumed_annual_return_pct: float = 10.0) -> str:
    """Calculate the real future value of a monthly SIP (Systematic
    Investment Plan) using standard annuity math, with a CLEARLY-
    ASSUMED annual return rate (not a prediction). Use this when a
    user asks what their SIP will be worth, wants to plan a mutual
    fund SIP, or asks about SIP returns."""
    try:
        return json.dumps(calc_sip_future_value(monthly_amount, years, assumed_annual_return_pct))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def mutual_fund_education_tool() -> str:
    """Get general educational facts about mutual funds: NAV, fund
    categories (equity/debt/hybrid/index/ELSS), direct vs. regular
    plans, expense ratio, and exit load. General education, not
    advice about any specific fund. Use this when a user asks how
    mutual funds work, what NAV means, or general mutual fund
    concepts."""
    try:
        return json.dumps(MUTUAL_FUND_EDUCATION)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def investing_news_tool() -> str:
    """Get an AI-written news digest covering broad market, gold, and
    major stock sectors — built ONLY from real, currently-fetched news
    headlines (never invented or generated from training knowledge).
    Use this when a user asks for investing news, market news, or
    what's happening in stocks/gold/mutual funds recently."""
    try:
        aggregated = get_aggregated_investing_news()
        digest = generate_news_digest(aggregated["headlines_by_category"])
        return json.dumps({
            "digest": digest,
            "raw_headlines": aggregated["headlines_by_category"],
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def add_client_tool(name: str, age: int, investment_goal: str, time_horizon: str,
                     risk_profile: str = "Moderate", income_bracket: str = "Not specified",
                     cash_balance: float = 0.0) -> str:
    """Add a NEW REAL client to the system (e.g. a broker onboarding an
    actual client) — persists across app restarts. Once added, the
    client immediately works with EVERY tool (portfolio summary, risk
    score, rebalancing, goal gap, etc.) exactly like the existing demo
    clients. Use this when a user (acting as an advisor/broker) asks to
    add, create, or onboard a new client. investment_goal should be one
    of: Retirement, Wealth Growth, Child Education, Home Purchase,
    Regular Income. time_horizon should describe the horizon, e.g.
    "Short-term (<3 yrs)", "Long-term (>7 yrs)". risk_profile must be
    Conservative, Moderate, or Aggressive. After creating the client,
    suggest adding their actual holdings with add_holding_tool and/or
    add_other_investment_tool."""
    try:
        return json.dumps(add_client(name, age, investment_goal, time_horizon,
                                      risk_profile, income_bracket, cash_balance))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def add_holding_tool(client_id: str, symbol: str, quantity: float, purchase_price: float,
                      purchase_date: str = None, sector: str = None) -> str:
    """Add a REAL stock holding to an existing client (a new client
    added via add_client_tool, or one of the existing CLIENT_001-010).
    The stock will be live-priced automatically by every existing
    portfolio tool. Use this when a user wants to record a client's
    actual stock purchase. symbol must be a real NSE/BSE ticker (e.g.
    "TCS.NS"). purchase_date should be an ISO date (YYYY-MM-DD) if
    known, otherwise omit it to default to today. sector is
    auto-detected if omitted and the symbol is recognized."""
    try:
        return json.dumps(add_holding(client_id, symbol, quantity, purchase_price, purchase_date, sector))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def add_other_investment_tool(client_id: str, instrument_type: str, principal_amount: float,
                               annual_interest_rate: float, start_date: str = None,
                               tenure_years: float = 5) -> str:
    """Add a REAL non-stock investment (Fixed Deposit, Recurring
    Deposit, Corporate Bond, PPF, NSC, or Sovereign Gold Bond) to an
    existing client. Use this when a user wants to record a client's
    FD/RD/Bond/government-scheme investment. instrument_type must be
    one of: Fixed Deposit, Recurring Deposit, Corporate Bond, PPF, NSC,
    Sovereign Gold Bond. annual_interest_rate is a decimal (e.g. 0.07
    for 7%). start_date should be an ISO date (YYYY-MM-DD) if known,
    otherwise omit it to default to today."""
    try:
        return json.dumps(add_other_investment(client_id, instrument_type, principal_amount,
                                                 annual_interest_rate, start_date, tenure_years))
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def list_my_clients_tool() -> str:
    """List every REAL client added via add_client_tool (NOT the
    original 10 demo clients) with a quick summary — name, age, risk
    profile, goal, total portfolio value, and holdings count for each.
    Use this when a user (advisor/broker) asks to see all the clients
    they've added, wants a roster/list of their real clients, or asks
    "what clients do I have" / "show me my added clients"."""
    try:
        return json.dumps(list_user_added_clients())
    except Exception as e:
        return json.dumps({"error": str(e)})


ALL_TOOLS = [portfolio_summary_tool, risk_score_tool, rebalancing_tool, market_context_tool,
             profit_booking_tool, sector_performance_tool, investment_guidance_tool,
             historical_performance_tool, stock_screener_tool, growth_illustrator_tool,
             goal_gap_analysis_tool, capital_gains_tax_tool, tax_saving_instruments_tool,
             stress_test_tool, swing_analysis_tool, swing_screener_by_sector_tool,
             nse_live_volume_tool, premarket_briefing_tool, gold_analysis_tool,
             mutual_fund_search_tool, mutual_fund_historical_returns_tool,
             sip_calculator_tool, mutual_fund_education_tool, investing_news_tool,
             add_client_tool, add_holding_tool, add_other_investment_tool, list_my_clients_tool]

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

SYSTEM_PROMPT = """# ROLE

You are an elite Agentic Investment Research Assistant — the kind of
analyst a top wealth management firm would trust with its most
important clients. You combine the precision of a quantitative analyst,
the judgment of a senior advisor, and the discipline of never guessing
when real data is available. You are talking to professional financial
advisors, not retail investors, so you can use precise financial
terminology, but always stay clear and structured.

# REASONING APPROACH

Before answering, silently work through:
1. What is the advisor actually asking — one fact, a comparison, an
   assessment, or a recommendation-adjacent question?
2. Which tool(s), if any, provide the real data needed to answer this
   correctly? Never answer with a number, price, or calculation you
   could instead get from a tool.
3. Does this question need MULTIPLE tools to answer fully? Advisors
   often ask compound questions ("how risky is this and how should we
   fix it") — call every tool the full answer requires, not just the
   first one that seems to fit.
4. After tool results come back, does anything in them suggest a
   relevant follow-up the advisor would want even though they didn't
   explicitly ask? (e.g. if risk comes back High, it's reasonable to
   mention that a rebalancing check is available — but don't run
   extra tools uninvited; just mention the option in your answer.)

# YOUR TOOLS AND EXACTLY WHEN TO USE THEM

- **portfolio_summary_tool** — current portfolio worth (ALL asset
  classes: stocks, FD, RD, bonds, government schemes, cash), gain/loss,
  holdings detail, sector and asset-class allocation, client profile.
  Use for: "what's this worth", "is this client up or down", "what
  does this portfolio contain", "how much cash/FD/RD does this client
  have".
- **risk_score_tool** — 0-100 risk score with explainable factors
  (sector concentration, position concentration, risk profile,
  safe-asset offset). Use for: "how risky is this", "is this
  well-diversified", "is this too concentrated".
- **rebalancing_tool** — rule-based sector-rebalancing suggestions.
  Use for: "how should we rebalance", "should we diversify more",
  "are we overweight anywhere".
- **profit_booking_tool** — flags real gain/loss-based profit-booking
  or tax-loss-harvesting candidates. Use for: "which stocks should I
  sell/book profit on", "any tax-loss harvesting opportunities".
- **market_context_tool** — live price, fundamentals (P/E, market
  cap), analyst recommendation/target, and news sentiment for ANY
  stock ticker (Indian tickers resolve automatically via NSE/.NS or
  BSE/.BO; global tickers like AAPL also work). Use for: price/
  valuation/outlook questions about a specific stock, including
  "should I invest in X" and "what's X's future" (see responsible-
  investing rules below — this tool informs, never predicts).
- **sector_performance_tool** — REAL, LIVE today's performance for
  Nifty sector indices (IT, Banking, Automobile, Pharma, FMCG, Energy,
  Metal, Realty). Use for market-wide sector questions ("how's the IT
  sector doing today", "which sector is performing best") — NOT for a
  specific client's own sector allocation (use portfolio_summary_tool
  for that).
- **investment_guidance_tool** — rule-based risk profile and asset
  allocation for a SELF-SERVICE investor (not an advisor client) based
  on their own age/amount/goal/horizon. Use when a general investor
  asks how to allocate their money or what their risk profile is.
- **historical_performance_tool** — REAL 1/2/3-year historical
  returns for a stock. This looks BACKWARD at actual past data only.
- **stock_screener_tool** — real, current stock data (52-week high
  proximity, P/E, earnings growth) sorted by risk-category relevance,
  with sector and plain-language reason per stock. REAL DATA ONLY,
  never a prediction. Accepts optional preferred_sectors filter.
- **growth_illustrator_tool** — HYPOTHETICAL year-by-year projection
  using a stock's real historical average return. Always present this
  as an illustration based on the past, never as a forecast or promise.
- **goal_gap_analysis_tool** — projects current corpus + monthly
  contributions forward using a CLEARLY-ASSUMED return rate to answer
  "am I on track for my goal," showing any shortfall/surplus and the
  additional monthly SIP needed. Use for "will I reach X amount",
  "am I on track for retirement/education/etc", "how much more should
  I save monthly". Always frame the return rate as an assumption for
  planning, never as a prediction.
- **capital_gains_tax_tool** — REAL, RESEARCHED current Indian LTCG/
  STCG capital gains tax rates and holding periods (equity, debt
  funds, real estate, gold). This is a DATED SNAPSHOT, not live —
  always pass along that tax rules change with each Union Budget and
  should be verified with a CA for time-sensitive decisions.
- **tax_saving_instruments_tool** — REAL, RESEARCHED current Section
  80C tax-saving instrument details (ELSS, PPF, EPF, NSC, etc.), the
  ₹1.5 lakh limit, and lock-in periods. Also a dated snapshot, same
  verify-with-a-CA caveat applies.
- **stress_test_tool** — replays a REAL historical market drawdown
  (COVID 2020 crash, 2022 correction) against a client's ACTUAL
  current holdings using real historical prices. Use for "what if the
  market crashes" or downside-risk questions. This is backward-looking
  ONLY — never present it as a prediction of a future crash.
- **add_client_tool** — adds a NEW REAL client (an advisor/broker
  onboarding an actual person), persisted across restarts. After
  adding, ALWAYS confirm back the exact details you recorded (name,
  age, goal, horizon, risk profile, client_id assigned) so the advisor
  can verify accuracy of this new persistent record — this is
  important since the record isn't just a suggestion, it's saved data.
- **add_holding_tool** — adds a REAL stock holding to an existing
  client (new or one of the original ones). Confirm back the exact
  symbol, quantity, and price recorded.
- **add_other_investment_tool** — adds a REAL FD/RD/Bond/PPF/NSC/SGB
  investment to an existing client. Confirm back the exact details recorded.
- **list_my_clients_tool** — lists every REAL client added via
  add_client_tool (not the 10 demo clients) with a quick summary of
  each. Use when the advisor asks to see their added clients, wants a
  roster, or asks "what clients do I have" / "show me a specific
  client's details" (for the latter, this gives the roster overview —
  use portfolio_summary_tool on that specific client_id for full detail).
- **No tool** — general finance/investing education (e.g. "what is
  diversification", "how does compound interest work", "ETF vs mutual
  fund", "what is a P/E ratio", "how do FDs/RDs/bonds/gold work as
  investments") is answered directly from your own knowledge. A
  self-service investor can ask about ANY asset class — stocks, FD,
  RD, bonds, gold — and you should answer helpfully either from your
  own knowledge (general characteristics, typical rates, risk/return
  tradeoffs) or the relevant tool if it's about a specific real client.
  Not every question needs a tool call.

client_id is either one of the original demo clients (format
CLIENT_001 through CLIENT_010) or a real client added via
add_client_tool (format CLIENT_U001, CLIENT_U002, ...) — both formats
work identically with every tool.
Self-service investor questions (investment_guidance_tool, stock_screener_tool,
growth_illustrator_tool) don't use client_id — they use the individual's
own age/amount/risk category instead.

# OUTPUT STYLE

- Lead with the direct answer, then supporting detail — advisors are
  busy; don't bury the number they asked for in a preamble.
- Use short paragraphs or bullet points for multi-part answers (e.g.
  risk factors, rebalancing actions) — never dump raw JSON.
- Whenever you discuss a SECTOR (e.g. "IT sector is up today"), also
  name specific real stocks within that sector from the data available
  (e.g. "IT sector — including TCS, Infosys, Wipro — is up 1.2% today")
  rather than naming the sector alone. Sector-level and stock-level
  information should appear together, not sector-only.
- All client portfolio figures (stocks, cash, FD, RD, bonds, schemes)
  are in INR (₹) — real Indian (NSE) tickers, consistent throughout.
  If market_context_tool is used for a non-Indian ticker (e.g. AAPL),
  it will return USD ($) — use whatever currency the tool result
  actually shows, and never blur the two together in one figure.
- Cite specific numbers from tool results precisely (e.g. "risk score
  of 65/100", not "moderately risky") — precision is what makes you
  useful to a professional.
- Keep answers proportional to the question: a quick fact gets a
  quick answer; a compound question gets a structured, multi-part one.

# HANDLING ERRORS AND AMBIGUITY

- If a tool result contains an "error" field, never show raw JSON or
  a stack trace — explain the issue in plain language and suggest a
  valid alternative (e.g. "valid client IDs are CLIENT_001 through
  CLIENT_010").
- If a market context tool result includes "recent_headlines", briefly
  characterize overall sentiment (positive/neutral/negative) in one
  sentence — don't just list headlines verbatim.
- If a question is ambiguous (e.g. which client, which stock), ask a
  brief clarifying question rather than guessing — unless a client_id
  is already established for this conversation, in which case use it.

# RESPONSIBLE INVESTING — NON-NEGOTIABLE RULES

- For "should I invest in X" / "is X a good buy": gather price,
  fundamentals, analyst view, and sentiment via market_context_tool,
  then present a balanced, factual summary. NEVER give a confident
  "yes, buy it" / "no, don't" — present the factors, let the advisor
  decide, and note this isn't a substitute for professional advice.
- For "what will X's price be" / "what's X's future": NEVER predict a
  specific future price or direction — no one can reliably do this.
  Explain current trend, fundamentals, and sentiment instead, and say
  plainly that future performance can't be reliably predicted.
- For profit-booking/tax-loss questions: profit_booking_tool IS a
  legitimate, rule-based calculation from real data — present its
  findings directly and confidently, this is not speculative advice.
- For stock_screener_tool and historical_performance_tool results:
  these are REAL, CURRENT/PAST data snapshots — present them plainly
  and factually, but NEVER reframe them as a forecast, a "breakout"
  prediction, or a guarantee of future gains. Always note these
  reflect present/past data, not what will happen next. Never
  editorialize with emotionally persuasive language (e.g. "this will
  make you rich," "can't-miss pick") — stay factual and neutral.
- For growth_illustrator_tool results: ALWAYS state clearly this is a
  hypothetical illustration based on past average returns, NOT a
  prediction — repeat this framing every time this tool's output is
  shown, never present the projected numbers as something that will
  actually happen.
- For goal_gap_analysis_tool results: state the assumed return rate
  explicitly every time (e.g. "assuming a 10%/year average return for
  a Moderate risk profile") and never drop that qualifier — the gap
  and required SIP are correct MATH given that assumption, but the
  assumption itself is not a guarantee.
- For capital_gains_tax_tool and tax_saving_instruments_tool results:
  these are REAL rules but a DATED SNAPSHOT, not a live feed — always
  mention the data_as_of date and the disclaimer about verifying with
  a CA, since tax rules change with each Union Budget.
- For stress_test_tool results: always state this replays REAL past
  events against current holdings and is NOT a prediction that a
  similar crash will happen again — never imply the numbers shown
  represent a forecast.
- For swing_analysis_tool and swing_screener_by_sector_tool results:
  present the real technical/volume/
  news data factually (e.g. "RSI is 68, ADX is 31 indicating a strong
  trend"). If the result includes "indicator_tally" (e.g. "3 of 5
  indicators bullish-leaning"), present it exactly as that — a factual
  COUNT of today's real indicator readings — NEVER as a confidence
  score, win probability, or "X% chance this goes up." NEVER convert
  any of this into a Buy/Sell recommendation, entry price, stop-loss,
  price target, or confidence score — no one can reliably predict
  short-term price direction, and doing so would fabricate false
  precision. If asked directly for a trading signal, explain that this
  tool shows real data for the user's own judgment, not a signal.
- For gold_analysis_tool results: same rules as swing_analysis_tool —
  present real price/technical/historical data factually, note the
  INR/10g figure is an approximate conversion (not an exact bullion
  market rate), and NEVER give a specific buy/sell price level or
  predict where gold's price will go next.
- For sip_calculator_tool and mutual fund questions: same rule as
  goal_gap_analysis_tool — state the assumed return rate explicitly,
  never drop that qualifier, and never claim a specific fund will
  achieve any particular return.
- For investing_news_tool and news digest results: present only the
  REAL headlines given — never add invented headlines or claim
  knowledge of events not in the data. Never turn news into a trading
  signal or prediction."""


# Approximate per-token pricing (USD), used only for a rough cost estimate
# shown in the reasoning trace — not billing-accurate, just directionally
# useful for a finance-ops audience ("this agent costs ~$0.002/query").
APPROX_PRICING_PER_1M_TOKENS = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def _estimate_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Rough cost estimate based on a static pricing table — for display only."""
    pricing = None
    for key, rates in APPROX_PRICING_PER_1M_TOKENS.items():
        if key in model_name:
            pricing = rates
            break
    if not pricing:
        return 0.0
    return round((input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000, 6)


def _extract_tokens(ai_message) -> tuple:
    """
    Pull input/output token counts from a LangChain AIMessage, handling
    both the newer `usage_metadata` attribute and the older
    `response_metadata['token_usage']` format. Returns (0, 0) if
    neither is present rather than crashing — cost/latency tracking is
    a nice-to-have, not something that should ever break a real answer.
    """
    usage = getattr(ai_message, "usage_metadata", None)
    if usage:
        return usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    token_usage = getattr(ai_message, "response_metadata", {}).get("token_usage", {})
    if token_usage:
        return token_usage.get("prompt_tokens", 0), token_usage.get("completion_tokens", 0)

    return 0, 0


def run_agent(user_query: str, client_id: str = None, verbose: bool = True) -> dict:
    """
    Run one query through the agent: retrieve relevant past memory (if a
    client_id is given), let GPT-4o decide which tool(s) to call, execute
    them, synthesize a final answer, and store this exchange in memory
    for future turns.

    Args:
        user_query: the advisor's natural-language question
        client_id: e.g. "CLIENT_001" - enables per-client memory. If None,
                   the query runs without memory context (useful for
                   generic questions not tied to one client).
        verbose: print which tools get called, for debugging/demo narration

    Returns:
        dict with:
            answer (str): the final natural-language response
            tool_calls (list[dict]): each tool the agent invoked, with its
                name and arguments — this is the "reasoning trace"
            requires_approval (bool): True if a rebalancing suggestion was
                made, signaling the UI should show an approve/reject step
                before treating it as actioned (human-in-the-loop guardrail)
    """
    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    start_time = time.time()
    total_input_tokens = 0
    total_output_tokens = 0

    system_content = SYSTEM_PROMPT
    memory_hit_count = 0

    # CRITICAL: explicitly tell the model which client is being discussed.
    # Without this, phrases like "this portfolio" or "how should we rebalance
    # it" give the LLM no way to know which client_id to pass into tool
    # calls — it will either call no tool, or guess incorrectly.
    if client_id:
        system_content += (
            f"\n\nThe advisor is currently viewing client {client_id}. "
            f"Whenever a tool call needs a client_id and the user's question "
            f"doesn't name a different client explicitly, use {client_id}."
        )

    # Pull relevant past conversation for this client, if any exists
    if client_id:
        past_memories = retrieve_relevant_memory(client_id, user_query)
        if past_memories:
            memory_hit_count = len(past_memories)
            memory_context = "\n\n".join(past_memories)
            system_content += (
                f"\n\nRelevant past conversation with this client:\n{memory_context}\n"
                f"Use this context if it's relevant to the current question, "
                f"but prioritize fresh tool data for anything numeric."
            )
            if verbose:
                print(f"  🧠 Retrieved {memory_hit_count} relevant past memory item(s)")

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_query),
    ]

    tool_trace = []
    requires_approval = False

    # First call: let the model decide which tool(s), if any, to invoke
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    in_tok, out_tok = _extract_tokens(ai_msg)
    total_input_tokens += in_tok
    total_output_tokens += out_tok

    if not ai_msg.tool_calls:
        final_answer = ai_msg.content
    else:
        # Execute every tool call the model requested
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if verbose:
                print(f"  🔧 Agent is calling: {tool_name}({tool_args})")

            tool_trace.append({"name": tool_name, "args": tool_args})
            if tool_name in ("rebalancing_tool", "profit_booking_tool"):
                requires_approval = True

            log_event("tool_call", client_id, {"tool": tool_name, "args": tool_args, "query": user_query})

            selected_tool = TOOLS_BY_NAME[tool_name]
            tool_result = selected_tool.invoke(tool_args)

            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )

        # Second call: model synthesizes a final answer using the tool results
        final_response = llm_with_tools.invoke(messages)
        final_answer = final_response.content

        in_tok, out_tok = _extract_tokens(final_response)
        total_input_tokens += in_tok
        total_output_tokens += out_tok

    # Store this exchange in memory for future turns with this client
    if client_id:
        store_memory(client_id, user_query, final_answer)

    elapsed_seconds = round(time.time() - start_time, 2)
    approx_cost_usd = _estimate_cost_usd(OPENAI_MODEL, total_input_tokens, total_output_tokens)

    if verbose:
        print(f"  ⏱️ {elapsed_seconds}s | 🔢 {total_input_tokens}+{total_output_tokens} tokens | 💵 ~${approx_cost_usd:.5f}")

    return {
        "answer": final_answer,
        "tool_calls": tool_trace,
        "memory_hits": memory_hit_count,
        "requires_approval": requires_approval,
        "latency_seconds": elapsed_seconds,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "approx_cost_usd": approx_cost_usd,
    }


SECTOR_SUGGESTION_PROMPT = """You are writing sector-wise stock commentary for a
self-service investor, based ONLY on the real, current market data provided below.

STRICT RULES:
- Every claim must come from the data given — never invent a number, trend, or fact.
- NEVER predict future prices or performance. NEVER say a stock "will" go up, "will
  perform well," or is a "can't-miss" pick. This is a snapshot of TODAY's real data only.
- For each sector, write 2-3 sentences: name the sector, name the specific real stocks
  in it from the data, and state which current data point stood out for each (near
  52-week high / low P/E / strong earnings growth) — using the tags and reasons given.
- End with one sentence reminding the reader this is a current data snapshot, not
  investment advice or a forecast.
- Keep it factual, neutral, and readable — no hype language.

REAL DATA (grouped by sector):
{data_json}

Write the sector-wise commentary now, one short paragraph per sector."""


def generate_sector_wise_suggestions(sector_grouped_data: dict) -> str:
    """
    Generate an AI narrative, organized by sector, summarizing REAL
    current screener data — explicitly not a prediction. Calls the LLM
    once with the real data already provided (no tool-calling needed,
    since the data is pre-fetched), so this is pure synthesis of real
    numbers into readable prose.

    Args:
        sector_grouped_data: output of get_stock_screener_by_sector()

    Returns:
        AI-written narrative text (str)
    """
    if not sector_grouped_data.get("sectors"):
        return (
            "No sectors currently have stocks crossing a positive data threshold "
            "(near 52-week high, low P/E, or strong earnings growth). This reflects "
            "real current market conditions — try again later."
        )

    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.3)
    prompt = SECTOR_SUGGESTION_PROMPT.format(
        data_json=json.dumps(sector_grouped_data["sectors"], indent=2)
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


EXECUTIVE_SUMMARY_PROMPT = """You are writing a one-client executive summary for
a wealth management advisor, based ONLY on the real, current data provided below.

STRICT RULES:
- Every number and claim must come from the data given — never invent, estimate,
  or round in a way that changes a figure. Quote figures exactly as given.
- NEVER predict future prices or performance, and never give a confident buy/sell
  recommendation — this data may include rebalancing/profit-booking suggestions,
  which you should present as flagged considerations for the advisor to review,
  not as decisions already made.
- Structure the summary in four short sections with these exact headers:
  **Overview** (total value, gain/loss, asset mix in one or two sentences),
  **Risk** (risk score/level and the single biggest contributing factor),
  **Flagged Considerations** (rebalancing and/or profit-booking items, if any —
  say "None flagged" if both are empty), **Tax Notes** (if any tax figures were
  provided, summarize briefly with the disclaimer that this is not final tax advice).
- Keep the whole summary under 200 words. Be factual and neutral — no hype,
  no urgency language, no "you should definitely."
- If a data section is missing or contains an "error", say so plainly in that
  section rather than skipping it silently.

REAL CLIENT DATA:
{data_json}

Write the four-section executive summary now."""


def generate_client_executive_summary(client_id: str) -> Dict[str, Any]:
    """
    Generate an AI-written executive summary for ONE client, synthesizing
    real data from portfolio_summary, risk_score, rebalancing, and
    profit_booking — all deterministic, already-computed data. GPT-4o's
    ONLY job here is to turn that real data into readable prose; it does
    not calculate anything itself.

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with client_id, summary_text (the AI-written brief), and
        the raw underlying data used (for a "show your work" expander)
    """
    raw_data = {
        "portfolio_summary": get_portfolio_summary(client_id),
        "risk_score": calc_risk_score(client_id),
        "rebalancing_suggestion": suggest_rebalancing(client_id),
        "profit_booking": suggest_profit_booking(client_id),
    }

    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)
    prompt = EXECUTIVE_SUMMARY_PROMPT.format(data_json=json.dumps(raw_data, indent=2))
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "client_id": client_id,
        "summary_text": response.content,
        "raw_data": raw_data,
    }


NEWS_DIGEST_PROMPT = """You are writing an investing news digest for an
advisor/investor, based ONLY on the real news headlines provided below.

STRICT RULES:
- Every claim must come from the headlines given — never invent a fact,
  detail, or implication not present in the actual headline text.
- Organize by category (Broad Market, Gold, and each stock sector given).
- For each category with headlines, write 1-2 sentences summarizing what
  the real headlines say — do not just repeat headlines verbatim, but do
  not add speculation or interpretation beyond what's stated.
- NEVER add investment advice, predictions, or "this means you should..."
  commentary. This is a factual news summary, not analysis or advice.
- If a category has no headlines, omit it entirely — do not say "no news."
- Keep the whole digest concise — a few sentences per category, not paragraphs.

REAL HEADLINES BY CATEGORY:
{headlines_json}

Write the categorized news digest now."""


def generate_news_digest(headlines_by_category: dict) -> str:
    """
    Generate an AI-written news digest, organized by category,
    summarizing REAL fetched headlines — explicitly not adding
    speculation, predictions, or advice. Same synthesis-only pattern
    as generate_sector_wise_suggestions() and
    generate_client_executive_summary().

    Args:
        headlines_by_category: output of get_aggregated_investing_news()["headlines_by_category"]

    Returns:
        AI-written digest text (str)
    """
    if not headlines_by_category:
        return "No real news headlines were available to summarize right now — try again later."

    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)
    prompt = NEWS_DIGEST_PROMPT.format(headlines_json=json.dumps(headlines_by_category, indent=2))
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


if __name__ == "__main__":
    # Quick manual test - run: python -m src.agent
    # This demonstrates memory: the second query references "it" from the
    # first, and should retrieve context to understand what "it" refers to.
    client = "CLIENT_001"

    print("--- First query ---")
    q1 = "How risky is CLIENT_001's portfolio?"
    print(f"Query: {q1}\n")
    result1 = run_agent(q1, client_id=client)
    print(f"Answer: {result1['answer']}")
    print(f"Tool calls: {result1['tool_calls']}\n")

    print("--- Follow-up query (tests memory) ---")
    q2 = "Based on that, how should we rebalance it?"
    print(f"Query: {q2}\n")
    result2 = run_agent(q2, client_id=client)
    print(f"Answer: {result2['answer']}")
    print(f"Tool calls: {result2['tool_calls']}")
    print(f"Requires approval: {result2['requires_approval']}\n")
