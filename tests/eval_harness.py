"""
STRETCH FEATURE: Agent Evaluation Harness

Systematically measures whether the agent calls the RIGHT tool(s) for
a fixed set of test queries, and produces a pass/fail scorecard. This
is the "LLM evals" pattern that's become the standard way to
demonstrate an agent is reliable, not just that it happened to work
in a few manual tests.

Usage:
    python tests/eval_harness.py

Outputs a pass/fail report to the console AND saves a copy to
data/eval_report.md so you have something concrete to show judges as
evidence of testing rigor.

This makes real (billed) OpenAI API calls - expect a few cents total.
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import run_agent

REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "eval_report.md")

# Each case: (client_id, query, expected_tool_names)
# expected_tool_names is a list - the agent must call AT LEAST these tools
# (it's allowed to call more; under-calling is a fail, extra calls are not
# penalized since a thorough answer calling an extra relevant tool is fine)
EVAL_CASES = [
    ("CLIENT_001", "What does this portfolio contain?", ["portfolio_summary_tool"]),
    ("CLIENT_002", "How risky is this portfolio?", ["risk_score_tool"]),
    ("CLIENT_003", "How should we rebalance this portfolio?", ["rebalancing_tool"]),
    (None, "What's the current price of AAPL?", ["market_context_tool"]),
    (None, "What's the sentiment on MSFT right now?", ["market_context_tool"]),
    ("CLIENT_004", "Give me a risk assessment and rebalancing plan", ["risk_score_tool", "rebalancing_tool"]),
    ("CLIENT_005", "What's the portfolio summary and risk score?", ["portfolio_summary_tool", "risk_score_tool"]),
    ("CLIENT_006", "Is this client's portfolio well diversified?", ["risk_score_tool"]),
    ("CLIENT_007", "What sectors is this client invested in?", ["portfolio_summary_tool"]),
    ("CLIENT_001", "Should we reduce exposure to any sector?", ["rebalancing_tool"]),
    ("CLIENT_002", "What's this portfolio worth right now?", ["portfolio_summary_tool"]),
    ("CLIENT_003", "Is this client up or down overall?", ["portfolio_summary_tool"]),
    ("CLIENT_001", "Which stocks should I book profit on?", ["profit_booking_tool"]),
    (None, "Should I invest in TCS?", ["market_context_tool"]),
    (None, "What is diversification?", []),
    (None, "How is the IT sector doing today?", ["sector_performance_tool"]),
    (None, "I'm 30 years old and want to invest ₹200000, what should my allocation be?", ["investment_guidance_tool"]),
    (None, "How has TCS performed over the last 3 years?", ["historical_performance_tool"]),
    (None, "Give me a stock screener for aggressive risk", ["stock_screener_tool"]),
]


def run_evaluation():
    results = []

    for client_id, query, expected_tools in EVAL_CASES:
        try:
            result = run_agent(query, client_id=client_id, verbose=False)
            actual_tools = set(tc["name"] for tc in result["tool_calls"])
            expected_set = set(expected_tools)

            if expected_set:
                # Normal case: agent must call at least the expected tool(s)
                passed = expected_set.issubset(actual_tools)
            else:
                # Special case: expecting NO tool calls (general knowledge
                # question) - passes only if the agent called nothing
                passed = len(actual_tools) == 0
            results.append({
                "query": query,
                "client_id": client_id,
                "expected": sorted(expected_set),
                "actual": sorted(actual_tools),
                "passed": passed,
            })
        except Exception as e:
            results.append({
                "query": query,
                "client_id": client_id,
                "expected": sorted(expected_tools),
                "actual": [f"CRASHED: {e}"],
                "passed": False,
            })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = round((passed_count / total) * 100, 1)

    # --- Console output ---
    print(f"\n{'='*70}\nAGENT EVALUATION RESULTS\n{'='*70}")
    for r in results:
        icon = "✅" if r["passed"] else "❌"
        print(f"{icon} \"{r['query']}\"")
        print(f"   Expected: {r['expected']}  |  Actual: {r['actual']}")

    print(f"\n{'='*70}")
    print(f"SCORE: {passed_count}/{total} passed ({pass_rate}%)")
    print("=" * 70)

    # --- Markdown report for judges ---
    lines = [
        f"# Agent Evaluation Report",
        f"",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"",
        f"**Score: {passed_count}/{total} passed ({pass_rate}%)**",
        f"",
        f"| Query | Client | Expected Tool(s) | Actual Tool(s) | Result |",
        f"|---|---|---|---|---|",
    ]
    for r in results:
        icon = "✅ Pass" if r["passed"] else "❌ Fail"
        lines.append(
            f"| {r['query']} | {r['client_id'] or '—'} | {', '.join(r['expected'])} "
            f"| {', '.join(r['actual'])} | {icon} |"
        )

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n📄 Report saved to {REPORT_PATH}")
    return results


if __name__ == "__main__":
    run_evaluation()
