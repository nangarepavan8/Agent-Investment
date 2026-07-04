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
    return json.dumps(get_portfolio_summary(client_id))


@tool
def risk_score_tool(client_id: str) -> str:
    """Calculate a 0-100 risk score for a client's portfolio, including
    the risk level (Low/Medium/High) and the specific factors driving
    that score. Use this when the user asks how risky a portfolio is
    or wants a risk assessment. client_id must be in the format
    CLIENT_001 through CLIENT_010."""
    return json.dumps(calc_risk_score(client_id))


@tool
def rebalancing_tool(client_id: str) -> str:
    """Suggest specific portfolio rebalancing actions to reduce
    concentration risk, comparing current vs. target sector allocation.
    Use this when the user asks how to rebalance, diversify, or adjust
    a portfolio. client_id must be in the format CLIENT_001 through
    CLIENT_010."""
    return json.dumps(suggest_rebalancing(client_id))


@tool
def market_context_tool(symbol: str) -> str:
    """Get live public market data for a stock symbol: current price,
    today's % change, and 52-week range. Use this when the user asks
    about current market conditions, price, or performance of a
    specific stock ticker (e.g. AAPL, MSFT)."""
    return json.dumps(get_market_context(symbol))


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
advisor-friendly answer — don't just dump raw JSON at the user."""


def run_agent(user_query: str, verbose: bool = True) -> str:
    """
    Run one query through the agent: GPT-4o decides which tool(s) to call,
    the tools execute, and GPT-4o synthesizes a final natural-language answer.
    """
    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query),
    ]

    # First call: let the model decide which tool(s), if any, to invoke
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if not ai_msg.tool_calls:
        # Model answered directly without needing a tool
        return ai_msg.content

    # Execute every tool call the model requested
    for tool_call in ai_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if verbose:
            print(f"  🔧 Agent is calling: {tool_name}({tool_args})")

        selected_tool = TOOLS_BY_NAME[tool_name]
        tool_result = selected_tool.invoke(tool_args)

        messages.append(
            ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
        )

    # Second call: model synthesizes a final answer using the tool results
    final_response = llm_with_tools.invoke(messages)
    return final_response.content


if __name__ == "__main__":
    # Quick manual test - run: python -m src.agent
    test_query = "How risky is CLIENT_001's portfolio and how should we rebalance it?"
    print(f"Query: {test_query}\n")
    answer = run_agent(test_query)
    print(f"\nFinal Answer:\n{answer}")
