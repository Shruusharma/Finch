import logging


logger = logging.getLogger(__name__)


def ask_stock_agent(query: str) -> dict:
    """
    Routes a query to the Stock Market Agent.

    Args:
        query: the user's question, rephrased if helpful for the stock agent

    Returns:
        dict with the stock agent's response
    """
    from agents import stock_agent
    
    logger.info(f"Routing to StockAgent: {query}")
    result = stock_agent.handle(query)
    return {"response": result}


def ask_portfolio_agent(query: str) -> dict:
    """
    Routes a query to the Portfolio RAG Agent.

    Args:
        query: the user's question, rephrased if helpful for the portfolio agent

    Returns:
        dict with the portfolio agent's response
    """
    from agents import portfolio_agent
    
    logger.info(f"Routing to PortfolioAgent: {query}")
    result = portfolio_agent.handle(query)
    return {"response": result}


def get_latest_insight_tool() -> dict:
    """
    Retrieves the most recently generated weekly insight report.
    """
    from memory.insight_store import get_latest_insight

    insight = get_latest_insight()

    if insight is None:
        return {
            "response": "No weekly insight report has been generated yet."
        }

    return {
        "generated_at": insight.get("generated_at"),
        "report": insight.get("report"),
    }