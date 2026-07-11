"""
Shared yfinance session — browser-impersonating fix for cloud deployment.

WHY THIS EXISTS: Yahoo Finance (which yfinance scrapes) increasingly
blocks or rate-limits requests coming from cloud-hosting data-center IP
ranges (AWS, GCP, Azure — which is what Streamlit Community Cloud runs
on), even for completely valid, liquid tickers like TCS.NS. This works
fine from a home/office network but can fail once deployed to the
cloud. Using a curl_cffi session that impersonates a real Chrome
browser's TLS fingerprint is the fix recommended by yfinance's own
maintainers for exactly this "works locally, fails on cloud" symptom.

If curl_cffi isn't installed for any reason, falls back to yfinance's
default session behavior rather than crashing.
"""

try:
    from curl_cffi import requests as curl_requests
    _session = curl_requests.Session(impersonate="chrome")
except ImportError:
    _session = None


def get_yf_session():
    """Return the shared browser-impersonating session, or None to let
    yfinance use its own default session if curl_cffi isn't available."""
    return _session
