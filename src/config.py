"""
Central config: loads API key + model name from .env
Every other file should import from here instead of calling os.getenv directly.
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Copy .env.example to .env and add your key."
    )

# Shared secret for api_server.py's endpoints (N8N automation). If not set
# in .env, a random key is generated each run — meaning the API is still
# protected by default, just with a key you'd need to read from the logs
# (fine for local testing; set API_SERVER_KEY explicitly in .env for any
# real/persistent deployment so N8N's saved key doesn't go stale).
API_SERVER_KEY = os.getenv("API_SERVER_KEY")
if not API_SERVER_KEY:
    API_SERVER_KEY = secrets.token_urlsafe(24)
    print(f"⚠️  API_SERVER_KEY not set in .env — generated a temporary one for this run: {API_SERVER_KEY}")
    print("   Set API_SERVER_KEY in .env for a stable key across restarts (needed for N8N).")
