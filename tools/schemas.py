STOCK_PRICE_TOOL = {
    "name": "get_stock_price",
    "description": "Get the current stock price and company info for a given ticker symbol.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol, e.g. AAPL, TSLA, MSFT"
            }
        },
        "required": ["ticker"]
    }
}

STOCK_HISTORY_TOOL = {
    "name": "get_stock_history",
    "description": "Get historical price performance for a stock over a number of days, including percent change, high, and low.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol, e.g. AAPL, TSLA, MSFT"
            },
            "days": {
                "type": "integer",
                "description": "Number of days of history to retrieve, default 30"
            }
        },
        "required": ["ticker"]
    }
}

COMPANY_INFO_TOOL = {
    "name": "get_company_info",
    "description": "Get general company information including sector, industry, market cap, and business summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol, e.g. AAPL, TSLA, MSFT"
            }
        },
        "required": ["ticker"]
    }
}

STOCK_TOOLS = {
    "function_declarations": [
        STOCK_PRICE_TOOL,
        STOCK_HISTORY_TOOL,
        COMPANY_INFO_TOOL,
    ]
}

SEARCH_PORTFOLIO_TOOL = {
    "name": "search_portfolio",
    "description": (
        "Search the user's investment portfolio for positions relevant to a query. "
        "Use this for any question about the user's holdings, positions, cost basis, "
        "or personal notes on investments. Rephrase the user's question into clear "
        "search terms if needed (e.g. 'my chip stocks' -> 'semiconductor AI chip positions')."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query describing what portfolio information is needed"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of matching positions to retrieve, default 3"
            }
        },
        "required": ["query"]
    }
}

PORTFOLIO_TOOLS = {
    "function_declarations": [
        SEARCH_PORTFOLIO_TOOL,
    ]
}

ASK_STOCK_AGENT_TOOL = {
    "name": "ask_stock_agent",
    "description": (
        "Ask the Stock Market Agent about current prices, historical performance, "
        "or company information for ANY publicly traded stock (whether or not the "
        "user owns it). Use for general market questions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question to send to the stock market agent"
            }
        },
        "required": ["query"]
    }
}

ASK_PORTFOLIO_AGENT_TOOL = {
    "name": "ask_portfolio_agent",
    "description": (
        "Ask the Portfolio Agent about the user's OWN holdings, positions, "
        "cost basis, or personal investment notes. Use for questions about "
        "what the user owns or their stated intentions about their own portfolio."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question to send to the portfolio agent"
            }
        },
        "required": ["query"]
    }
}

ORCHESTRATOR_TOOLS = {
    "function_declarations": [
        ASK_STOCK_AGENT_TOOL,
        ASK_PORTFOLIO_AGENT_TOOL,
    ]
}