# Agent Evaluation Report

Generated: 2026-07-15T15:44:56

**Score: 27/32 passed (84.4%)**

| Query | Client | Expected Tool(s) | Actual Tool(s) | Result |
|---|---|---|---|---|
| What does this portfolio contain? | CLIENT_001 | portfolio_summary_tool | portfolio_summary_tool | ✅ Pass |
| How risky is this portfolio? | CLIENT_002 | risk_score_tool | risk_score_tool | ✅ Pass |
| How should we rebalance this portfolio? | CLIENT_003 | rebalancing_tool | rebalancing_tool | ✅ Pass |
| What's the current price of AAPL? | — | market_context_tool | market_context_tool | ✅ Pass |
| What's the sentiment on MSFT right now? | — | market_context_tool | market_context_tool | ✅ Pass |
| Give me a risk assessment and rebalancing plan | CLIENT_004 | rebalancing_tool, risk_score_tool | rebalancing_tool, risk_score_tool | ✅ Pass |
| What's the portfolio summary and risk score? | CLIENT_005 | portfolio_summary_tool, risk_score_tool | portfolio_summary_tool, risk_score_tool | ✅ Pass |
| Is this client's portfolio well diversified? | CLIENT_006 | risk_score_tool | portfolio_summary_tool | ❌ Fail |
| What sectors is this client invested in? | CLIENT_007 | portfolio_summary_tool |  | ❌ Fail |
| Should we reduce exposure to any sector? | CLIENT_001 | rebalancing_tool | rebalancing_tool, risk_score_tool | ✅ Pass |
| What's this portfolio worth right now? | CLIENT_002 | portfolio_summary_tool | portfolio_summary_tool | ✅ Pass |
| Is this client up or down overall? | CLIENT_003 | portfolio_summary_tool | portfolio_summary_tool | ✅ Pass |
| Which stocks should I book profit on? | CLIENT_001 | profit_booking_tool | profit_booking_tool | ✅ Pass |
| Should I invest in TCS? | — | market_context_tool | market_context_tool | ✅ Pass |
| What is diversification? | — |  |  | ✅ Pass |
| How is the IT sector doing today? | — | sector_performance_tool | sector_performance_tool | ✅ Pass |
| I'm 30 years old and want to invest ₹200000, what should my allocation be? | — | investment_guidance_tool |  | ❌ Fail |
| How has TCS performed over the last 3 years? | — | historical_performance_tool | historical_performance_tool | ✅ Pass |
| Give me a stock screener for aggressive risk | — | stock_screener_tool | stock_screener_tool | ✅ Pass |
| Show me a hypothetical growth illustration for TCS | — | growth_illustrator_tool | growth_illustrator_tool | ✅ Pass |
| I have ₹5 lakhs saved and want ₹50 lakhs in 15 years, am I on track? | — | goal_gap_analysis_tool | goal_gap_analysis_tool | ✅ Pass |
| What's the LTCG tax rate on equity mutual funds? | — | capital_gains_tax_tool | capital_gains_tax_tool | ✅ Pass |
| What are my Section 80C tax saving options? | — | tax_saving_instruments_tool | tax_saving_instruments_tool | ✅ Pass |
| What if the market crashes like COVID? How would my portfolio do? | CLIENT_001 | stress_test_tool |  | ❌ Fail |
| Show me the technical indicators and volume for TCS | — | swing_analysis_tool | swing_analysis_tool | ✅ Pass |
| Give me a list of stocks with high volume near their highs, sector wise | — | swing_screener_by_sector_tool | swing_screener_by_sector_tool | ✅ Pass |
| What should I check before market opens today? | — | premarket_briefing_tool | premarket_briefing_tool | ✅ Pass |
| Is gold overbought right now? What's the current price? | — | gold_analysis_tool | gold_analysis_tool, market_context_tool | ✅ Pass |
| What SIP amount do I need monthly to reach 50 lakhs in 10 years? | — | sip_calculator_tool |  | ❌ Fail |
| What is NAV and how do mutual fund categories work? | — | mutual_fund_education_tool | mutual_fund_education_tool | ✅ Pass |
| How has scheme code 119551 performed over the past 3 years? | — | mutual_fund_historical_returns_tool | mutual_fund_historical_returns_tool | ✅ Pass |
| What's the latest investing news today? | — | investing_news_tool | investing_news_tool | ✅ Pass |