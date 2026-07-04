"""
Central config: loads API key + model name from .env
Every other file should import from here instead of calling os.getenv directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Copy .env.example to .env and add your key."
    )
