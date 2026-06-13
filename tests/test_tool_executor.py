from core.tool_executor import execute_tool


def test_unknown_tool_returns_error():
    result = execute_tool("nonexistent_tool", {})
    assert "error" in result
    assert "nonexistent_tool" in result["error"]


def test_get_stock_price_unknown_ticker():
    # Real yfinance call — but a guaranteed-invalid ticker fails fast,
    # no LLM involved, so no quota risk.
    result = execute_tool("get_stock_price", {"ticker": "ZZZZINVALID"})
    assert "error" in result


def test_search_portfolio_handles_float_top_k():
    # Regression test for the days=7.0 / top_k=3.0 bug class (Phase 4 & 6)
    result = execute_tool("search_portfolio", {"query": "NVDA", "top_k": 3.0})
    assert "error" not in result or "matches" in result