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
    prices vs. purchase price. Use this when the user asks which
    stocks to sell, take profit on, or harvest losses from. client_id
    must be in the format CLIENT_001 through CLIENT_010."""
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


ALL_TOOLS = [portfolio_summary_tool, risk_score_tool, rebalancing_tool, market_context_tool,
             profit_booking_tool, sector_performance_tool, investment_guidance_tool,
             historical_performance_tool, stock_screener_tool, growth_illustrator_tool,
             goal_gap_analysis_tool, capital_gains_tax_tool, tax_saving_instruments_tool]

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
- **No tool** — general finance/investing education (e.g. "what is
  diversification", "how does compound interest work", "ETF vs mutual
  fund", "what is a P/E ratio", "how do FDs/RDs/bonds/gold work as
  investments") is answered directly from your own knowledge. A
  self-service investor can ask about ANY asset class — stocks, FD,
  RD, bonds, gold — and you should answer helpfully either from your
  own knowledge (general characteristics, typical rates, risk/return
  tradeoffs) or the relevant tool if it's about a specific real client.
  Not every question needs a tool call.

client_id must always be in the format CLIENT_001 through CLIENT_010.
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
  a CA, since tax rules change with each Union Budget."""


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
