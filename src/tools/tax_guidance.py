"""
NEW: Taxation & Tax-Saving Guidance (India)

Real, current Indian capital gains tax rules and Section 80C tax-saving
instruments — researched and cited, NOT invented or guessed. Tax rules
genuinely change with each Union Budget, so this is explicitly dated
("as of" a specific research date) with a clear instruction to verify
with a CA or the official Income Tax Department for anything time-
sensitive, consistent with this project's honesty-first philosophy.

DATA SOURCED: July 2026, from multiple cross-verified tax-advisory
sources (Cleartax, Bajaj Finserv, IndMoney, TaxTMI, and others),
reflecting Finance (No. 2) Act 2024 rules confirmed unchanged through
Union Budget 2025 and Union Budget 2026 (presented Feb 1, 2026).

NOTE ON LIVE UPDATES: this data is a point-in-time snapshot, not a
live feed. The underlying app (deployed via OpenAI's API directly)
does not have live web search built in — adding that would require a
separate search API (e.g. Tavily, SerpAPI, Bing Search) as a new
dependency. This snapshot approach avoids that cost/complexity while
still being accurate and clearly dated, and is easy to refresh
periodically by re-running research and updating this file.
"""

from typing import Dict, Any

DATA_AS_OF = "July 2026 (reflects Finance (No. 2) Act 2024 rules, confirmed unchanged through Union Budget 2026)"

CAPITAL_GAINS_RULES = {
    "equity_shares_and_equity_mutual_funds": {
        "short_term_stcg": {
            "holding_period": "12 months or less",
            "tax_rate": "20% flat (Section 111A), provided Securities Transaction Tax (STT) is paid",
        },
        "long_term_ltcg": {
            "holding_period": "more than 12 months",
            "tax_rate": "12.5% (Section 112A), no indexation benefit",
            "annual_exemption": "₹1.25 lakh per financial year on equity LTCG (raised from ₹1 lakh in Budget 2024)",
        },
        "note": "Equity mutual funds with ≥65% equity allocation are taxed identically to listed shares.",
    },
    "debt_mutual_funds": {
        "note": (
            "Units purchased on/after 1 April 2023 are taxed at the investor's income tax "
            "slab rate regardless of holding period (Section 50AA) — no LTCG/STCG "
            "distinction and no indexation benefit for these units."
        ),
    },
    "real_estate": {
        "short_term_stcg": {
            "holding_period": "24 months or less",
            "tax_rate": "taxed at the investor's income tax slab rate",
        },
        "long_term_ltcg": {
            "holding_period": "more than 24 months",
            "tax_rate": (
                "12.5% without indexation (properties bought on/after 23 July 2024), OR a choice "
                "between 12.5% without indexation vs. 20% with indexation for properties bought before that date"
            ),
        },
    },
    "gold_and_international_funds": {
        "note": "From FY 2025-26, taxed similarly to other non-equity assets: 12.5% LTCG after the long-term holding threshold, but WITHOUT the ₹1.25 lakh exemption that applies to equity.",
    },
}

SECTION_80C_INSTRUMENTS = {
    "overall_limit": "₹1.5 lakh per financial year (combined across all instruments below; unchanged since FY 2014-15)",
    "available_only_under": "Old Tax Regime (NOT available under the New Tax Regime)",
    "instruments": [
        {"name": "ELSS (Equity Linked Savings Scheme)", "lock_in": "3 years (shortest of all 80C options)",
         "character": "Market-linked equity fund; gains taxed as equity LTCG (12.5% above ₹1.25 lakh)"},
        {"name": "PPF (Public Provident Fund)", "lock_in": "15 years",
         "character": "Government-backed, tax-free interest (EEE status); ~7.1%/year"},
        {"name": "EPF (Employee Provident Fund)", "lock_in": "Until retirement (payroll-driven)",
         "character": "Automatic for salaried employees; ~8.25%/year, tax-free"},
        {"name": "NSC (National Savings Certificate)", "lock_in": "5 years",
         "character": "Government-backed fixed return"},
        {"name": "Tax-Saver Fixed Deposit", "lock_in": "5 years",
         "character": "Bank FD; interest earned is taxable"},
        {"name": "Sukanya Samriddhi Yojana (SSY)", "lock_in": "Until girl child turns 21 (partial withdrawal allowed earlier)",
         "character": "For a girl child; ~8.2%/year, tax-free"},
        {"name": "Life insurance premiums", "lock_in": "Policy term",
         "character": "Premium must be ≤10% of sum assured for the tax benefit to apply"},
        {"name": "Home loan principal repayment", "lock_in": "N/A",
         "character": "Principal component only, not interest"},
        {"name": "Children's tuition fees", "lock_in": "N/A",
         "character": "For up to 2 children"},
    ],
    "additional_deduction": {
        "section": "80CCD(1B)",
        "amount": "Additional ₹50,000 for NPS (National Pension System) contributions, OVER AND ABOVE the ₹1.5 lakh 80C limit",
    },
}


def get_capital_gains_rules(asset_type: str = None) -> Dict[str, Any]:
    """
    Return current Indian capital gains tax rules, for one asset type
    or all of them.

    Args:
        asset_type: one of "equity_shares_and_equity_mutual_funds",
                     "debt_mutual_funds", "real_estate",
                     "gold_and_international_funds" — or None for all

    Returns:
        dict with the rules requested, data_as_of date, and a
        disclaimer to verify with a professional for anything
        time-sensitive
    """
    if asset_type and asset_type in CAPITAL_GAINS_RULES:
        rules = {asset_type: CAPITAL_GAINS_RULES[asset_type]}
    else:
        rules = CAPITAL_GAINS_RULES

    return {
        "rules": rules,
        "data_as_of": DATA_AS_OF,
        "disclaimer": (
            "This reflects real, researched tax rules as of the date above, NOT a live feed. "
            "Tax rules can change with each Union Budget — verify current rules with a "
            "Chartered Accountant or the official Income Tax Department (incometax.gov.in) "
            "before making decisions based on this."
        ),
    }


def get_tax_saving_instruments() -> Dict[str, Any]:
    """
    Return current Section 80C tax-saving instrument details.

    Returns:
        dict with the 80C instrument list, data_as_of date, and disclaimer
    """
    return {
        "section_80c": SECTION_80C_INSTRUMENTS,
        "data_as_of": DATA_AS_OF,
        "disclaimer": (
            "This reflects real, researched tax-saving rules as of the date above, NOT a "
            "live feed. Section 80C is available ONLY under the Old Tax Regime. Verify "
            "current rules with a Chartered Accountant or the official Income Tax "
            "Department (incometax.gov.in) before making decisions based on this."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_capital_gains_rules("equity_shares_and_equity_mutual_funds"), indent=2))
    print()
    print(json.dumps(get_tax_saving_instruments(), indent=2))
