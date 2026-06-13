from unittest.mock import MagicMock
from core.llm_client import call_llm


def _make_text_response(text):
    """Builds a fake Gemini response object with no function call, just text."""
    response = MagicMock()
    part = MagicMock()
    part.function_call = None
    part.text = text
    response.candidates[0].content.parts = [part]
    response.text = text
    return response


def _make_function_call_response(name, args):
    """Builds a fake Gemini response object requesting a tool call."""
    response = MagicMock()
    part = MagicMock()
    fc = MagicMock()
    fc.name = name
    fc.args = args
    part.function_call = fc
    response.candidates[0].content.parts = [part]
    return response


def test_no_tool_call_returns_immediately(mocker):
    mock_generate = mocker.patch("core.llm_client._generate")
    mock_generate.return_value = _make_text_response("Hello there")

    result = call_llm([{"role": "user", "content": "hi"}], tools=None)

    assert result == "Hello there"
    assert mock_generate.call_count == 1  # exactly one LLM call


def test_single_tool_call_then_final_answer(mocker):
    mock_generate = mocker.patch("core.llm_client._generate")
    mock_execute = mocker.patch("core.llm_client.execute_tool")
    mock_execute.return_value = {"price": 229.50}

    # First call: requests a tool. Second call: final text.
    mock_generate.side_effect = [
        _make_function_call_response("get_stock_price", {"ticker": "AAPL"}),
        _make_text_response("AAPL is at $229.50"),
    ]

    result = call_llm([{"role": "user", "content": "AAPL price?"}], tools=[{}])

    assert result == "AAPL is at $229.50"
    assert mock_generate.call_count == 2
    mock_execute.assert_called_once_with("get_stock_price", {"ticker": "AAPL"})


def test_hits_max_iterations_returns_fallback(mocker):
    mock_generate = mocker.patch("core.llm_client._generate")
    mocker.patch("core.llm_client.execute_tool", return_value={"data": "..."})

    # LLM ALWAYS requests a tool — never produces final text
    mock_generate.return_value = _make_function_call_response("get_stock_price", {"ticker": "AAPL"})

    result = call_llm([{"role": "user", "content": "test"}], tools=[{}])

    assert "wasn't able to fully complete" in result
    assert mock_generate.call_count == 5  # MAX_TOOL_ITERATIONS