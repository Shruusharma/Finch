import logging
from core.llm_client import call_llm
from tools.schemas import ORCHESTRATOR_TOOLS
from memory.insight_store import save_insight
from memory.portfolio_data import SAMPLE_PORTFOLIO

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Finch's weekly insight generator. "
    "You produce a concise weekly portfolio summary for the user. "
    "Use ask_portfolio_agent to retrieve the user's current holdings, "
    "and ask_stock_agent to check recent performance (last 7 days) for "
    "each holding. "
    "Structure your report as:\n"
    "1. Overall summary (1-2 sentences)\n"
    "2. Per-holding performance (price change, % change)\n"
    "3. Notable observations or things the user may want to consider\n\n"
    "Be factual and concise. Do not give direct buy/sell instructions — "
    "highlight information for the user to consider."
)


def generate_weekly_insight() -> str:
    """
    Generates a weekly portfolio insight report and persists it.

    This is the autonomous entry point — no user message involved.
    The agent constructs its own prompt and uses the same tool-calling
    loop as every other agent.

    Returns:
        The generated report text.
    """
    logger.info("Generating weekly insight report")

    tickers = [p["ticker"] for p in SAMPLE_PORTFOLIO]

    prompt = (
        f"Generate this week's portfolio insight report. "
        f"The user's portfolio includes: {', '.join(tickers)}. "
        f"Check the portfolio details and recent (7-day) performance "
        f"for each holding, then produce the report per your instructions."
    )

    messages = [{"role": "user", "content": prompt}]

    report = call_llm(
        messages,
        system=SYSTEM_PROMPT,
        tools=[ORCHESTRATOR_TOOLS],
        max_tokens=1500,
    )

    save_insight(report)
    return report