# Agentic Investment Research Assistant

TVS Next InnovAIte 2026 — Hackathon Project

An AI agent that routes natural-language financial queries to
specialized tools (portfolio summary, risk scoring, rebalancing,
market context) using GPT-4o, with persistent per-client memory via
ChromaDB.

## Day 1 Setup

1. **Clone this repo / unzip the project**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your real OpenAI API key in place of
   `sk-your-key-here`. Get a key at https://platform.openai.com/api-keys
   (requires a funded OpenAI account — a few dollars is plenty for
   this whole project).

5. **Test the connection**
   ```bash
   python tests/test_gpt4o_connection.py
   ```
   You should see a short GPT-4o response printed to your terminal.
   If this works, Day 1 is done.

## Project Structure

```
agentic-investment-assistant/
├── README.md
├── requirements.txt
├── .env.example          # copy to .env, never commit .env
├── .gitignore
├── src/
│   ├── config.py         # loads API key + model name
│   └── tools/
│       ├── portfolio_summary.py   # Tool 1 (stub — Day 3)
│       ├── risk_score.py          # Tool 2 (stub — Day 3)
│       ├── rebalancing.py         # Tool 3 (stub — Day 3)
│       └── market_context.py      # Tool 4 (stub — Day 3)
├── data/                 # synthetic dataset goes here (Day 2)
└── tests/
    └── test_gpt4o_connection.py   # Day 1 connectivity check
```

## Roadmap

| Day | Milestone |
|---|---|
| 1 | API key working, tool signatures defined, repo initialized ✅ (this step) |
| 2 | Synthetic portfolio dataset |
| 3 | Implement the 4 tool functions |
| 4 | LangChain agent + GPT-4o function-calling wired up |
| 5 | Agent tested end-to-end on sample queries |
| 6 | ChromaDB memory added |
| 7 | Streamlit chat UI |
| 8 | Dashboard view |
| 9 | Full run-through + bug fixes |
| 10 | Polish + demo rehearsal |
