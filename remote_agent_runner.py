"""Programmatic remote/scheduled runner using the Antigravity Python SDK.

Install prerequisite:
    pip install google-antigravity

Usage:
    python remote_agent_runner.py --tickers NVDA,2330.TW
"""

import argparse
import asyncio
import sys
from google.antigravity import Agent, CapabilitiesConfig, LocalAgentConfig


SYSTEM_INSTRUCTIONS = """
You are the coordinator for the US & Taiwan multi-model stock analysis pipeline.
Follow the workspace skill `us-tw-stock-research` and invoke subagents or
`run_workflow` with `workflows/us_tw_analysis_workflow.py`, assigning:
- `flash_lite` for parallel data & sentiment gathering
- `flash` for specialist analysis (sentiment, technicals, fundamentals/chips)
- `pro` for final risk-gated judgment and conflict resolution
Never place live orders; all trade proposals require explicit human confirmation.
""".strip()


async def run(tickers: list[str]) -> None:
    config = LocalAgentConfig(
        system_instructions=SYSTEM_INSTRUCTIONS,
        capabilities=CapabilitiesConfig(),
    )

    prompt = (
        f"Run the US/TW two-stage stock research workflow for tickers: {', '.join(tickers)}. "
        f"First gather information in parallel, then perform specialist analysis, and "
        f"finally output the risk-gated decision table."
    )

    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AGY US/TW stock research agent")
    parser.add_argument(
        "--tickers",
        default="NVDA,2330.TW",
        help="Comma-separated US/TW tickers (e.g., NVDA,AAPL,2330.TW,2317.TW)",
    )
    parsed = parser.parse_args()
    tickers = [t.strip() for t in parsed.tickers.split(",") if t.strip()]
    asyncio.run(run(tickers))


if __name__ == "__main__":
    main()
