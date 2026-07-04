"""
DAY 4/5 CHECK: Test the full agent end-to-end with real GPT-4o calls.

Usage:
    python tests/test_agent.py

This uses your real OpenAI API key and will make actual billed calls
(a few cents at most for this whole test run).
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import run_agent

# A spread of queries designed to test different tool-routing behavior:
TEST_QUERIES = [
    "What does CLIENT_001's portfolio look like?",
    "How risky is CLIENT_003's portfolio?",
    "How should CLIENT_001 rebalance their portfolio?",
    "What's the current price of AAPL?",
    "Give me a full risk assessment and rebalancing plan for CLIENT_005",  # tests multi-tool call in one query
]


def run_all():
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print("=" * 60)
        try:
            answer = run_agent(query)
            print(f"\nAgent's answer:\n{answer}")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")

    print(f"\n{'='*60}")
    print("Day 4/5 test complete. Review above:")
    print("- Did each query trigger the RIGHT tool(s)?")
    print("- Did test 5 correctly call multiple tools (risk + rebalancing)?")
    print("- Are the final answers clear and advisor-friendly (not raw JSON)?")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
