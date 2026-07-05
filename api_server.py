"""
STRETCH FEATURE: N8N Automation Endpoint

Exposes the portfolio scan as a simple HTTP endpoint so N8N (the
hackathon's approved automation tool) can trigger it on a schedule —
e.g. "run this every morning at 8am" — instead of requiring an
advisor to manually click a button in Streamlit.

This directly matches your hackathon poster's "Process automation
opportunities" judging category, using an approved tool (N8N) that
nothing else in this project currently touches.

Run this alongside (not instead of) the Streamlit app:
    python api_server.py

Then in N8N, use an HTTP Request node on a Schedule Trigger, pointing
at: http://localhost:8000/scan (or your deployed URL)

See README "N8N Automation" section for the exact N8N workflow steps.
"""

from fastapi import FastAPI
from src.monitoring import scan_all_clients
from scripts.daily_valuation_snapshot import build_snapshot, OUTPUT_PATH

app = FastAPI(title="Agentic Investment Assistant - Automation API")


@app.get("/")
def root():
    return {"status": "ok", "message": "Agentic Investment Assistant automation API is running."}


@app.get("/scan")
def run_scan():
    """
    Trigger a full portfolio risk scan across all clients.
    Designed to be called by N8N on a schedule (e.g. daily).

    Returns:
        JSON with alert_count and the list of alerts (if any).
    """
    alerts = scan_all_clients()
    return {
        "alert_count": len(alerts),
        "alerts": alerts,
    }


@app.get("/snapshot")
def run_snapshot():
    """
    Regenerate the daily Excel valuation snapshot (all clients, all
    asset classes, at today's real market prices/valuations).
    Designed to be called by N8N on a schedule (e.g. daily at market
    close) so the spreadsheet is always fresh without manual effort.

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
