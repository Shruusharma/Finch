import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def get_stock_price(ticker: str) -> dict:
    """Fetches the current price and basic info for a stock ticker."""
    logger.info(f"Fetching price for {ticker}")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is None:
            return {"error": f"No price data found for ticker '{ticker}'"}

        return {
            "ticker": ticker.upper(),
            "price": price,
            "currency": info.get("currency", "USD"),
            "company_name": info.get("longName", ticker.upper()),
        }
    except Exception as e:
        logger.error(f"yfinance error for {ticker}: {e}")
        return {"error": f"Failed to fetch data for '{ticker}': {str(e)}"}


from datetime import datetime, timedelta

def get_stock_history(ticker: str, days: int = 30) -> dict:
    """
    Fetches historical price data for a stock over a given number of days.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL"
        days: Number of days of history to retrieve (default 30)

    Returns:
        dict with start price, end price, percent change, and high/low
    """
    days = int(round(float(days)))  # Gemini sends numbers as floats — normalize to int
    logger.info(f"Fetching {days}-day history for {ticker}")

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            return {"error": f"No historical data found for '{ticker}'"}

        start_price = round(float(hist["Close"].iloc[0]), 2)
        end_price = round(float(hist["Close"].iloc[-1]), 2)
        pct_change = round(((end_price - start_price) / start_price) * 100, 2)

        return {
            "ticker": ticker.upper(),
            "period_days": days,
            "start_price": start_price,
            "end_price": end_price,
            "percent_change": pct_change,
            "high": round(float(hist["High"].max()), 2),
            "low": round(float(hist["Low"].min()), 2),
        }
    except Exception as e:
        logger.error(f"yfinance history error for {ticker}: {e}")
        return {"error": f"Failed to fetch history for '{ticker}': {str(e)}"}

def get_company_info(ticker: str) -> dict:
    """
    Fetches general company information for a stock ticker.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL"

    Returns:
        dict with sector, industry, market cap, and business summary
    """
    logger.info(f"Fetching company info for {ticker}")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "longName" not in info:
            return {"error": f"No company info found for '{ticker}'"}

        return {
            "ticker": ticker.upper(),
            "company_name": info.get("longName", ticker.upper()),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", "Unknown"),
            "summary": info.get("longBusinessSummary", "No summary available")[:500],
        }
    except Exception as e:
        logger.error(f"yfinance company info error for {ticker}: {e}")
        return {"error": f"Failed to fetch company info for '{ticker}': {str(e)}"}