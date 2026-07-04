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

## Day 2: Synthetic Dataset

Run the generator once to create your data files:
```bash
python data/generate_data.py
```

This creates:
- `data/clients.csv` — 10 fictional clients: `client_id`, `name`, `risk_profile` (Conservative/Moderate/Aggressive)
- `data/holdings.csv` — each client's stock holdings: `client_id`, `symbol`, `sector`, `quantity`, `purchase_price`

Uses real public stock tickers (AAPL, MSFT, JPM, etc.) so the market
context tool can pull live prices via yfinance later — but all client
names and account data are 100% fictional, generated locally.

Re-run the script anytime to regenerate (fixed random seed = same data every time).

## Day 3: Tool Implementation

All 4 tools are now fully implemented against the synthetic dataset:

- `get_portfolio_summary(client_id)` — total value, holdings, sector allocation
- `calc_risk_score(client_id)` — 0-100 score based on sector concentration, single-position concentration, and stated risk profile
- `suggest_rebalancing(client_id)` — rule-based rebalancing suggestions vs. equal-weight target
- `get_market_context(symbol)` — live public price data via yfinance (requires internet)

Test everything at once:
```bash
python tests/test_all_tools.py
```

Or test one tool individually:
```bash
python -m src.tools.portfolio_summary
python -m src.tools.risk_score
python -m src.tools.rebalancing
python -m src.tools.market_context
```

Valid client IDs are `CLIENT_001` through `CLIENT_010` (see `data/clients.csv`).

## Day 4: The Agent (LangChain + GPT-4o Function-Calling)

`src/agent.py` is the core of the project. It wraps all 4 tools with
LangChain's `@tool` decorator and lets GPT-4o decide which tool(s) to
call based on the user's natural-language query — this is the actual
"agentic" behavior the hackathon is judging.

How it works:
1. User asks a question in plain English
2. GPT-4o reads the question + each tool's docstring, decides which
   tool(s) apply
3. The agent executes those tools against your real synthetic data
4. GPT-4o synthesizes the tool output into a clear, advisor-friendly answer

Test it:
```bash
python tests/test_agent.py
```

This runs 5 sample queries, including one that should trigger **two
tools in a single query** (risk score + rebalancing) — that's the
clearest way to demonstrate multi-step agentic reasoning to judges.

Quick single-query test:
```bash
python -m src.agent
```

**What to check when you run it:**
- Does each query call the tool you'd expect? (printed as `🔧 Agent is calling: ...`)
- Does the multi-tool query (test 5) call both `risk_score_tool` AND `rebalancing_tool`?
- Is the final answer readable prose, not raw JSON dumped at you?

If a query calls the wrong tool, the fix is almost always to make that
tool's docstring in `src/agent.py` more specific — GPT-4o routes based
on those descriptions.

## Day 6: Vector Memory (ChromaDB)

`src/memory.py` adds persistent, per-client memory so the agent
remembers past exchanges instead of treating every question as brand
new. This is what makes follow-up questions work — e.g. "how should
we rebalance **it**?" after a risk question, without re-specifying
the client.

How it's wired into the agent (`src/agent.py`):
1. Before answering, the agent retrieves relevant past exchanges for
   that specific `client_id`
2. That context gets added to the system prompt so GPT-4o can use it
3. After answering, the new exchange gets stored for future turns

**⚠️ Test this today, not on demo day:** ChromaDB downloads a small
embedding model (~80MB) from `huggingface.co` the first time it runs.
If your company network blocks that domain, the download will fail.
Run the test below now — if it fails, try once from home wifi or a
personal hotspot to let it download and cache (only needs to happen
once; it's cached locally after that).

Test memory in isolation (no OpenAI calls, no cost):
```bash
python tests/test_memory.py
```

Test memory working inside a real conversation (uses your API key):
```bash
python -m src.agent
```
This runs two queries back-to-back — the second one ("rebalance **it**")
should correctly understand "it" refers to CLIENT_001's portfolio from
the first query, using retrieved memory context.

## Day 7: Streamlit Chat UI

`app.py` is the demo-facing front end. Run it with:
```bash
streamlit run app.py
```
It should open automatically in your browser at `http://localhost:8501`.

**What it does:**
- Sidebar lets you pick which synthetic client you're asking about (CLIENT_001-010)
- Main area is a chat interface — type a question, the agent responds
- Suggested example questions are listed in the sidebar for quick demo use
- "Clear conversation" button resets the visible chat (note: ChromaDB
  memory persists in the background regardless — this button only
  clears what's shown on screen)

**Try this flow to test memory + multi-tool routing together:**
1. Pick a client (e.g. CLIENT_001)
2. Ask: "How risky is this portfolio?"
3. Ask: "How should we rebalance it?" — should correctly use "it" =
   the same portfolio, and pull the risk context from memory
4. Ask: "What's the current price of AAPL?" — tests the market-data tool

If anything errors in the chat, the app will show it inline (⚠️) rather
than crashing — check your `.env` API key and internet connection first.

## Roadmap

| Day | Milestone |
|---|---|
| 1 | API key working, tool signatures defined, repo initialized ✅ |
| 2 | Synthetic portfolio dataset ✅ |
| 3 | Implement the 4 tool functions ✅ |
| 4 | LangChain agent + GPT-4o function-calling wired up ✅ |
| 5 | Agent tested end-to-end on sample queries ✅ |
| 6 | ChromaDB memory added ✅ |
| 7 | Streamlit chat UI ✅ |
| 8 | Dashboard view |
| 9 | Full run-through + bug fixes |
| 10 | Polish + demo rehearsal |
