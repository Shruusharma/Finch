import logging
from tools.market_tools import get_stock_price, get_stock_history, get_company_info
from tools.portfolio_tools import search_portfolio
from agents.agent_tools import ask_stock_agent, ask_portfolio_agent

logger = logging.getLogger(__name__)

TOOL_REGISTRY = {
    "get_stock_price": get_stock_price,
    "get_stock_history": get_stock_history,
    "get_company_info": get_company_info,
    "search_portfolio": search_portfolio,
    "ask_stock_agent": ask_stock_agent,
    "ask_portfolio_agent": ask_portfolio_agent,
}


def execute_tool(name: str, args: dict) -> dict:
    """Executes a tool by name with given arguments."""
    logger.info(f"Executing tool: {name} with args: {args}")

    if name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {name}"}

    func = TOOL_REGISTRY[name]
    return func(**args)