"""
DAY 1 CHECK: Run this file to confirm your OpenAI API key works.

Usage:
    python tests/test_gpt4o_connection.py

Expected output: a short reply from GPT-4o printed to the console.
"""

import sys
import os

# Allow running this script directly from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL


def test_connection():
    client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"Testing connection using model: {OPENAI_MODEL}")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a concise financial assistant."},
            {"role": "user", "content": "In one sentence, what does a portfolio risk score measure?"},
        ],
        max_tokens=100,
    )

    reply = response.choices[0].message.content
    print("\n✅ SUCCESS — GPT-4o responded:\n")
    print(reply)


if __name__ == "__main__":
    test_connection()
