SAMPLE_PORTFOLIO = [
    {
        "ticker": "NVDA",
        "shares": 50,
        "cost_basis": 120.00,
        "sector": "Technology",
        "industry": "Semiconductors, AI chips, GPUs",
        "notes": "Bought during the AI chip rally, holding long-term for the data center growth thesis."
    },
    {
        "ticker": "AAPL",
        "shares": 30,
        "cost_basis": 175.00,
        "sector": "Technology",
        "industry": "Consumer electronics, smartphones, hardware",
        "notes": "Core long-term holding, dividend reinvestment enabled."
    },
    {
        "ticker": "TSLA",
        "shares": 15,
        "cost_basis": 250.00,
        "sector": "Automotive",
        "industry": "Electric vehicles, energy storage",
        "notes": "Speculative position, considering trimming if it rallies above 300."
    },
]


def portfolio_to_chunks(portfolio: list[dict]) -> list[dict]:
    """
    Converts portfolio positions into chunks suitable for the vector store.
    One chunk per position. Includes sector/industry to improve semantic
    retrieval for queries like "my chip stock" or "my EV position."
    """
    chunks = []
    for position in portfolio:
        text = (
            f"{position['ticker']}: {position['shares']} shares, "
            f"cost basis ${position['cost_basis']:.2f} per share. "
            f"Sector: {position['sector']}. Industry: {position['industry']}. "
            f"Notes: {position['notes']}"
        )
        chunks.append({
            "id": f"position-{position['ticker']}",
            "text": text,
            "metadata": {
                "ticker": position["ticker"],
                "shares": position["shares"],
                "cost_basis": position["cost_basis"],
                "sector": position["sector"],
            },
        })
    return chunks