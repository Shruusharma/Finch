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