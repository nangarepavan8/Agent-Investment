"""
STRETCH FEATURE: N8N Automation Endpoint

Exposes the portfolio scan (and daily snapshot) as HTTP endpoints so
N8N (the hackathon's approved automation tool) can trigger them on a
schedule — e.g. "run this every morning at 8am" — instead of
requiring an advisor to manually click a button in Streamlit.

This directly matches your hackathon poster's "Process automation
opportunities" judging category.

SECURITY: every endpoint except the root health-check requires an
API key header. Even with synthetic data, an unauthenticated finance
API is a real governance gap — this is a genuine access control, not
security theater: a request without the correct key gets rejected
with a 401.

Run this alongside (not instead of) the Streamlit app:
    python api_server.py

Then in N8N, use an HTTP Request node on a Schedule Trigger, pointing
at: http://localhost:8000/scan (or your deployed URL), with header:
    X-API-Key: <your key from .env, see API_SERVER_KEY>

See README "N8N Automation" section for the exact N8N workflow steps.
"""

from fastapi import FastAPI, Header, HTTPException, Depends
from src.monitoring import scan_all_clients
from scripts.daily_valuation_snapshot import build_snapshot, OUTPUT_PATH
from src.config import API_SERVER_KEY

app = FastAPI(title="Agentic Investment Assistant - Automation API")


def require_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    FastAPI dependency: every protected route declares this via
    `Depends(require_api_key)`. A request without the correct
    X-API-Key header is rejected with 401 before the route body runs.
    """
    if not x_api_key or x_api_key != API_SERVER_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header.")


@app.get("/")
def root():
    """Unauthenticated health check only — reveals no client data."""
    return {"status": "ok", "message": "Agentic Investment Assistant automation API is running."}


@app.get("/scan", dependencies=[Depends(require_api_key)])
def run_scan():
    """
    Trigger a full portfolio risk scan across all clients.
    Requires a valid X-API-Key header. Designed to be called by N8N
    on a schedule (e.g. daily).

    Returns:
        JSON with alert_count and the list of alerts (if any).
    """
    alerts = scan_all_clients()
    return {
        "alert_count": len(alerts),
        "alerts": alerts,
    }


@app.get("/snapshot", dependencies=[Depends(require_api_key)])
def run_snapshot():
    """
    Regenerate the daily Excel valuation snapshot (all clients, all
    asset classes, at today's real market prices/valuations).
    Requires a valid X-API-Key header.

    Returns:
        JSON confirming the snapshot was written, with its file path.
    """
    build_snapshot()
    return {
        "status": "ok",
        "message": "Daily valuation snapshot regenerated.",
        "file_path": OUTPUT_PATH,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
