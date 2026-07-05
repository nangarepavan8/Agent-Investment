# Demo Script & Rehearsal Guide

TVS Next InnovAIte 2026 — Agentic Investment Research Assistant

---

## Before you walk in (do this the night before AND morning of)

- [ ] `git pull` on the demo machine, confirm it's the latest code
- [ ] Confirm `.env` has a valid, funded OpenAI API key
- [ ] Run `python tests/test_day9_full_runthrough.py` once, fresh, to catch anything broken
- [ ] Pre-warm the app: run `streamlit run app.py`, ask 2-3 questions yourself BEFORE judges arrive (first API call is often slower — don't let that first-call lag happen live)
- [ ] Confirm venue wifi works, or have a personal hotspot ready as backup
- [ ] Have a **screen recording** of a successful full run saved locally, in case live wifi/API fails during the actual demo
- [ ] Close unrelated tabs/apps — only `localhost:8501` and your terminal should be visible

---

## The 5-minute demo flow

### 1. Open with the problem (30 seconds)
> "Advisors today manually cross-reference portfolio holdings, calculate risk, and research rebalancing across separate tools. We built an agent that does this through one natural-language conversation."

### 2. Show the architecture, briefly (30 seconds)
Click the **"ℹ️ How this works"** expander in the app itself — it's already written out. Point at it, don't read it word for word:
> "The agent reasons about which of 4 tools to call, executes them against portfolio data, and remembers context via vector memory — that's the agentic part, not just a chatbot wrapper."

### 3. Live demo — the core flow (3 minutes)

**Start with the "🔔 Portfolio Alerts" tab** — click "Run Portfolio Scan"
and narrate:
> "Before anyone even asks a question, the agent can proactively scan every client and flag who needs attention right now — this is the difference between a chatbot and a proactive agent."

Then pick one flagged client (e.g. CLIENT_001) and switch to Chat for this sequence:

| Step | You ask | What it demonstrates |
|---|---|---|
| 1 | *"What does this portfolio look like?"* | Tool routing — calls `portfolio_summary_tool` |
| 2 | *"How risky is it?"* | Routing again — calls `risk_score_tool`, and note "it" already resolves correctly |
| 3 | *"How should we rebalance it?"* | **Memory** — uses the risk context from step 2 without you repeating anything. Note the ✅/❌ approval buttons that appear — click "Approve" and narrate: "this is a deliberate guardrail — the agent proposes, the advisor decides." |
| 4 | *"What's the current sentiment on AAPL?"* | Real, live public market data **plus** recent news headlines — the agent characterizes sentiment, not just price |

On any answer, click **"🧠 Agent's reasoning"** at least once during the demo to show the tool-call trace — this makes the routing decision visible rather than a black box, which judges specifically respond well to.

While it's "thinking," narrate what's happening rather than sitting in silence:
> "It's deciding which tool applies right now, then it'll pull the real numbers from the synthetic dataset."

### 4. Show the Dashboard tab (1 minute)
Switch tabs. Point out:
- The metrics update instantly when you change clients (no LLM call — deterministic, free)
- The sector allocation chart and risk factors match exactly what the chat just said — consistency between the two matters

### 5. Close with the roadmap (30 seconds)
> "This runs entirely on GPT-4o today — a few dollars for the whole build. The documented next step is Azure OpenAI, Microsoft Fabric, and Azure hosting for a production, multi-user version."

---

## Anticipated judge questions (rehearse your answers out loud)

**"Why GPT-4o instead of a local/open-source model?"**
> We evaluated a fully offline Ollama setup first, but smaller local models were unreliable at structured tool-calling, which is core to this project. GPT-4o's native function-calling gave us reliability and speed at minimal cost — a few dollars for the entire hackathon.

**"How does the agent decide which tool to call?"**
> Each tool has a clear docstring describing what it does and when to use it. GPT-4o reads the user's question against those descriptions and picks the matching tool — that's native OpenAI function-calling, not custom logic we wrote.

**"Is this using real financial data?"**
> No — client names and portfolios are fully synthetic, generated locally. The only real data is live public stock prices via yfinance, which is public market data, not private client information.

**"How does the memory work?"**
> Every question and answer gets stored in ChromaDB, tagged by client. When a new question comes in, we retrieve the most relevant past exchanges for that same client and give GPT-4o that context — so follow-up questions don't need the client re-specified every time.

**"What would it take to make this production-ready?"**
> Swap GPT-4o for Azure OpenAI for enterprise compliance and SLAs, move the data layer to Microsoft Fabric for real client data, and host on Azure for multi-user access. That's documented as our future roadmap — deliberately not attempted during the hackathon since it needs real infrastructure and data governance.

**"What happens if the agent picks the wrong tool?"**
> During testing we hardened this — each tool independently validates its input and returns a clear error message rather than crashing, so even an edge case degrades gracefully instead of breaking the whole response.

**"Is this only reactive, or does it do anything proactively?"**
> The Portfolio Alerts tab scans every client's risk profile without being asked and flags anything needing attention — that's the proactive half of "proactive and adaptive" agentic AI, not just a chatbot answering questions on demand.

---

## If something breaks live

- **Agent errors on a question:** Stay calm, say "Let's try that differently" and rephrase — the error handling means it won't crash, just may answer imperfectly.
- **Wifi/API totally down:** Switch to your backup screen recording immediately, explain briefly, keep the demo moving.
- **Dashboard doesn't update:** Refresh the browser tab (`F5`) — Streamlit occasionally needs a manual refresh after long idle periods.

---

## Final reminder

Judges are evaluating the **agentic reasoning pattern** (plan → select tool → execute → remember), not a production financial model. Keep steering the narrative back to that whenever you can — it's the actual point of the whole build.
