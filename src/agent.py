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
from src.memory import store_memory, retrieve_relevant_memory


# ---------------------------------------------------------------------------
# Wrap each existing tool function with LangChain's @tool decorator.
# The docstring here is what GPT-4o reads to decide WHEN to call each tool,
# so keep them clear and specific.
# ---------------------------------------------------------------------------

@tool
def portfolio_summary_tool(client_id: str) -> str:
    """Get a summary of a client's portfolio: total value, holdings, and
    sector allocation. Use this when the user asks what a portfolio
    contains, its total value, or how it's allocated across sectors.
    client_id must be in the format CLIENT_001 through CLIENT_010."""
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
    """Get live public market data AND recent news headlines for a stock
    symbol: current price, today's % change, 52-week range, and up to 3
    recent headlines. Use this when the user asks about current market
    conditions, price, performance, or recent news/sentiment for a
    specific stock ticker (e.g. AAPL, MSFT)."""
    try:
        return json.dumps(get_market_context(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)})


ALL_TOOLS = [portfolio_summary_tool, risk_score_tool, rebalancing_tool, market_context_tool]

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

SYSTEM_PROMPT = """You are an Agentic Investment Research Assistant for
wealth management advisors. You have access to tools that pull real
portfolio data, calculate risk scores, suggest rebalancing, and fetch
live market data.

Always use the appropriate tool(s) to answer questions about specific
clients or stocks rather than guessing. You can call multiple tools in
sequence if a question requires it (e.g. risk score AND rebalancing
suggestions). After getting tool results, synthesize a clear, concise,
advisor-friendly answer — don't just dump raw JSON at the user.

If a tool result contains an "error" field, don't show raw JSON or a
stack trace to the user — explain the issue in plain language (e.g. an
invalid client ID) and suggest a valid alternative (valid client IDs
are CLIENT_001 through CLIENT_010).

If a market context tool result includes "recent_headlines", briefly
characterize the overall sentiment (positive, neutral, or negative)
those headlines suggest for that stock, in one sentence — don't just
list the headlines verbatim."""


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
            if tool_name == "rebalancing_tool":
                requires_approval = True

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
