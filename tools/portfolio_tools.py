import logging
from memory.vector_store import query_portfolio

logger = logging.getLogger(__name__)


def search_portfolio(query: str, top_k: int = 3) -> dict:
    """
    Searches the user's portfolio for positions relevant to the query.

    Args:
        query: natural language search query (can be reformulated by the LLM)
        top_k: number of results to retrieve

    Returns:
        dict with a list of matching positions, or an error dict
    """
    top_k = int(round(float(top_k)))  # defensive: LLM may send floats (Phase 4 lesson)
    logger.info(f"Searching portfolio for: '{query}' (top_k={top_k})")

    try:
        results = query_portfolio(query, top_k=top_k)

        if not results:
            return {"error": "No portfolio data found."}

        return {
            "matches": [
                {
                    "text": r["text"],
                    "ticker": r["metadata"].get("ticker"),
                    "shares": r["metadata"].get("shares"),
                    "cost_basis": r["metadata"].get("cost_basis"),
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Portfolio search error: {e}")
        return {"error": f"Failed to search portfolio: {str(e)}"}