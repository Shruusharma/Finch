import logging
from core.llm_client import call_llm
from tools.schemas import STOCK_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a stock market analyst agent. "
    "You have access to tools for current prices, historical performance, "
    "and company information. "
    "Use the most relevant tool(s) to answer the user's question accurately. "
    "If the user asks something unrelated to stocks or markets, say so clearly "
    "and do not attempt to answer outside your domain."
)


def handle(message: str) -> str:
    """
    Entry point for the Stock Market Agent.

    Args:
        message: The user's query, e.g. "How has AAPL done this month?"

    Returns:
        The agent's text response.
    """
    logger.info(f"StockAgent received: {message}")

    messages = [{"role": "user", "content": message}]

    response = call_llm(
        messages,
        system=SYSTEM_PROMPT,
        tools=[STOCK_TOOLS],
    )

    return response