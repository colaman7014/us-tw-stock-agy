"""AGY run_workflow orchestration script for US & Taiwan stock analysis.

Combines the two-stage pattern:
  Phase 1 (flash_lite): Parallel information gathering (sentiment + market data)
  Phase 2 (flash):      Specialized parallel analysis (sentiment, technical, fundamental/chips)
  Phase 3 (pro):        Risk-gated synthesis & final decision report (human-in-the-loop)

Expected `args` dict passed via `run_workflow(Args=...)`:
  {
      "tickers": ["NVDA", "2330.TW"],
      "risk_budget_pct": 1.0,
      "min_rr_ratio": 2.0
  }
"""

import json

GATHER_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "market": {"type": "string", "enum": ["US", "TW"]},
        "summary_points": {"type": "array", "items": {"type": "string"}},
        "raw_metrics": {"type": "object"},
    },
    "required": ["ticker", "market", "summary_points"],
}

SPECIALIST_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        "bias": {"type": "string", "enum": ["bullish", "neutral", "bearish"]},
        "confidence": {"type": "number"},
        "key_findings": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["role", "bias", "confidence", "key_findings", "risks"],
}

FINAL_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "market": {"type": "string"},
        "action": {"type": "string", "enum": ["WATCH", "PAPER_LONG", "PAPER_SHORT", "AVOID"]},
        "entry_zone": {"type": "string"},
        "stop_loss": {"type": "string"},
        "target_price": {"type": "string"},
        "reward_risk_ratio": {"type": "number"},
        "risk_gate_passed": {"type": "boolean"},
        "conflicts_resolved": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": [
        "ticker",
        "market",
        "action",
        "stop_loss",
        "reward_risk_ratio",
        "risk_gate_passed",
        "rationale",
    ],
}


def detect_market(ticker: str) -> str:
    clean = ticker.strip().upper()
    if clean.endswith(".TW") or clean.endswith(".TWO") or clean.isdigit():
        return "TW"
    return "US"


async def analyze_single_ticker(ticker: str, risk_budget_pct: float, min_rr_ratio: float) -> dict:
    market = detect_market(ticker)
    market_notes = (
        "Taiwan stock (TWSE/TPEX): include 3 institutional investors (外資/投信/自營商), "
        "monthly revenue YoY, and 10% daily price limit context."
        if market == "TW"
        else "US stock: include pre-market/intraday volume, SEC filings/insider or congressional "
        "disclosures if any, and unrestrained volatility."
    )

    # ------------------------------------------------------------------
    # Phase 1: Parallel Information Gathering (flash_lite)
    # ------------------------------------------------------------------
    phase(f"Phase 1: Gather Info ({ticker} / {market})")

    sentiment_gather = agent(
        role=f"Social & News Scraper ({ticker})",
        model="flash_lite",
        prompt=(
            f"Gather the last 30 days of public discourse, key news catalysts, and market "
            f"sentiment for {ticker} ({market} market). {market_notes} "
            f"Deduplicate repeated headlines and rank by engagement/impact."
        ),
        schema=GATHER_SCHEMA,
    )

    market_gather = agent(
        role=f"Market Data Collector ({ticker})",
        model="flash_lite",
        prompt=(
            f"Collect latest price action, 20MA/60MA trend, volume ratio, support/resistance "
            f"levels, and key fundamental/chip metrics for {ticker} ({market} market). {market_notes}"
        ),
        schema=GATHER_SCHEMA,
    )

    sentiment_raw, market_raw = await parallel(
        [sentiment_gather, market_gather],
        lambda a: a(),
    )

    context_blob = json.dumps(
        {"sentiment_data": sentiment_raw, "market_data": market_raw},
        ensure_ascii=False,
        indent=2,
    )

    # ------------------------------------------------------------------
    # Phase 2: Specialized Parallel Analysis (flash)
    # ------------------------------------------------------------------
    phase(f"Phase 2: Specialist Analysis ({ticker})")

    specialist_specs = [
        (
            "Sentiment & Catalyst Analyst",
            "Evaluate whether community narrative is backed by real catalysts or pure FOMO.",
        ),
        (
            "Technical & Entry/Exit Analyst",
            "Evaluate trend structure, breakout/pullback setups, exact stop-loss and target levels.",
        ),
        (
            "Fundamental & Chip Analyst",
            "Evaluate valuation, earnings/revenue momentum, and institutional/insider positioning.",
        ),
    ]

    specialist_results = await parallel(
        specialist_specs,
        lambda spec: agent(
            role=f"{spec[0]} ({ticker})",
            model="flash",
            prompt=(
                f"You are the {spec[0]} for {ticker} ({market}). {spec[1]}\n\n"
                f"Base your analysis strictly on this gathered context:\n{context_blob}"
            ),
            schema=SPECIALIST_SCHEMA,
        )(),
    )

    # ------------------------------------------------------------------
    # Phase 3: Risk-Gated Final Judgment (pro)
    # ------------------------------------------------------------------
    phase(f"Phase 3: Portfolio & Risk Judge ({ticker})")

    judge_prompt = (
        f"You are the Portfolio & Risk Judge for {ticker} ({market}).\n"
        f"Enforce strict risk rules:\n"
        f"1. Every actionable setup MUST have a concrete stop_loss.\n"
        f"2. Reward-to-risk ratio MUST be >= {min_rr_ratio}; otherwise set action='WATCH' or 'AVOID' and risk_gate_passed=false.\n"
        f"3. Max risk per trade budget is {risk_budget_pct}% of capital.\n"
        f"4. Never auto-execute; outputs are Paper/Watch proposals requiring explicit human confirmation.\n\n"
        f"Specialist Reports:\n{json.dumps(specialist_results, ensure_ascii=False, indent=2)}"
    )

    decision = await agent(
        role=f"Portfolio & Risk Judge ({ticker})",
        model="pro",
        prompt=judge_prompt,
        schema=FINAL_DECISION_SCHEMA,
    )()

    log(f"[{ticker}] action={decision['action']} risk_gate={decision['risk_gate_passed']}")
    return decision


async def main():
    tickers = (args or {}).get("tickers", ["NVDA", "2330.TW"])
    risk_budget_pct = float((args or {}).get("risk_budget_pct", 1.0))
    min_rr_ratio = float((args or {}).get("min_rr_ratio", 2.0))

    results = await parallel(
        tickers,
        lambda t: analyze_single_ticker(t, risk_budget_pct, min_rr_ratio),
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


await main()
