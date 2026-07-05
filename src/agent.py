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
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.tools.rebalancing import suggest_rebalancing
from src.tools.market_context import get_market_context
from src.tools.profit_booking import suggest_profit_booking
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


ALL_TOOLS = [portfolio_summary_tool, risk_score_tool, rebalancing_tool, market_context_tool, profit_booking_tool]

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
  stock ticker (US or Indian — Indian tickers resolve automatically).
  Use for: price/valuation/outlook questions about a specific stock,
  including "should I invest in X" and "what's X's future" (see
  responsible-investing rules below — this tool informs, never predicts).
- **No tool** — general finance/investing education (e.g. "what is
  diversification", "how does compound interest work", "ETF vs mutual
  fund", "what is a P/E ratio") is answered directly from your own
  knowledge. Not every question needs a tool call.

client_id must always be in the format CLIENT_001 through CLIENT_010.

# OUTPUT STYLE

- Lead with the direct answer, then supporting detail — advisors are
  busy; don't bury the number they asked for in a preamble.
- Use short paragraphs or bullet points for multi-part answers (e.g.
  risk factors, rebalancing actions) — never dump raw JSON.
- Always use the correct currency symbol from the data: $ for
  stock/USD figures, ₹ for cash/FD/RD/bond/scheme/INR figures. Never
  mix them or imply a false equivalence without noting the conversion.
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
  findings directly and confidently, this is not speculative advice."""


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

    # Store this exchange in memory for future turns with this client
    if client_id:
        store_memory(client_id, user_query, final_answer)

    return {
        "answer": final_answer,
        "tool_calls": tool_trace,
        "memory_hits": memory_hit_count,
        "requires_approval": requires_approval,
    }


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
