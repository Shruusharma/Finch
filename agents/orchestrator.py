import logging
from core.llm_client import call_llm
from tools.schemas import ORCHESTRATOR_TOOLS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Finch, an autonomous wealth assistant. "
    "You coordinate between specialist agents to answer the user's questions:\n"
    "- ask_stock_agent: for general stock market questions (prices, history, company info) "
    "about ANY stock, regardless of whether the user owns it.\n"
    "- ask_portfolio_agent: for questions about the user's OWN holdings, positions, "
    "or investment notes.\n\n"
    "Some questions require BOTH agents — for example, 'should I buy more X given my "
    "position' needs the user's current holdings (ask_portfolio_agent) AND current "
    "market data (ask_stock_agent). Call as many tools as needed, in sequence, to "
    "gather all relevant information BEFORE giving your final answer.\n\n"
    "If a question is general conversation (greetings, thanks, unrelated topics), "
    "respond directly without calling any tool. "
    "Always give the user a clear, complete answer based on all information gathered."
    "- get_latest_insight: retrieve the most recently generated weekly portfolio insight report.\n"
    "If the user asks for:\n"
    " - latest weekly insight\n"
    " - latest report\n"
    " - latest portfolio summary\n"
    " - weekly investment insight\n"
    "use get_latest_insight."
)


def handle(message: str) -> str:
    """
    Entry point for the Orchestrator Agent — routes to specialist agents
    or responds directly for general conversation.

    Args:
        message: The user's raw message

    Returns:
        The final response to send to the user
    """
    logger.info(f"Orchestrator received: {message}")

    messages = [{"role": "user", "content": message}]

    response = call_llm(
        messages,
        system=SYSTEM_PROMPT,
        tools=[ORCHESTRATOR_TOOLS],
    )

    return response