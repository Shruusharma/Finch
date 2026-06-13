import logging
from core.llm_client import call_llm
from tools.schemas import PORTFOLIO_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a portfolio analysis agent. "
    "You have access to a search tool over the user's investment portfolio "
    "(their holdings, cost basis, and personal notes). "
    "Use it to answer questions about what the user owns, their positions, "
    "or their stated investment intentions. "
    "If the user asks something unrelated to their portfolio — such as general "
    "market questions about stocks they don't own — say that's outside your scope."
)


def handle(message: str) -> str:
    """
    Entry point for the Portfolio RAG Agent.

    Args:
        message: The user's query, e.g. "What's my NVDA position?"

    Returns:
        The agent's text response.
    """
    logger.info(f"PortfolioAgent received: {message}")

    messages = [{"role": "user", "content": message}]

    response = call_llm(
        messages,
        system=SYSTEM_PROMPT,
        tools=[PORTFOLIO_TOOLS],
    )

    return response