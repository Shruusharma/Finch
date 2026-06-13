from agents import stock_agent


def test_handle_returns_llm_response(mocker):
    mock_llm = mocker.patch("agents.stock_agent.call_llm")
    mock_llm.return_value = "AAPL is currently at $229.50"

    result = stock_agent.handle("What's AAPL trading at?")

    assert result == "AAPL is currently at $229.50"


def test_handle_passes_correct_tools(mocker):
    mock_llm = mocker.patch("agents.stock_agent.call_llm")
    mock_llm.return_value = "some response"

    stock_agent.handle("What's AAPL trading at?")

    # Inspect what stock_agent actually passed to call_llm
    _, kwargs = mock_llm.call_args
    assert "tools" in kwargs
    tool_names = [
        decl["name"]
        for decl in kwargs["tools"][0]["function_declarations"]
    ]
    assert "get_stock_price" in tool_names
    assert "get_stock_history" in tool_names
    assert "get_company_info" in tool_names


def test_handle_passes_system_prompt(mocker):
    mock_llm = mocker.patch("agents.stock_agent.call_llm")
    mock_llm.return_value = "some response"

    stock_agent.handle("What's AAPL trading at?")

    _, kwargs = mock_llm.call_args
    assert "stock market analyst" in kwargs["system"].lower()