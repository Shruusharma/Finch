from unittest.mock import MagicMock
from agents import orchestrator


def test_general_chat_does_not_call_tools(mocker):
    """If the LLM responds with plain text (no tool call), orchestrator returns it directly."""
    mock_llm = mocker.patch("agents.orchestrator.call_llm")
    mock_llm.return_value = "Hi! I can help with stocks and your portfolio."

    result = orchestrator.handle("Hi, what can you do?")

    assert "help" in result.lower()
    mock_llm.assert_called_once()


def test_orchestrator_tools_include_both_agents(mocker):
    """Verify the orchestrator is configured with both routing tools."""
    mock_llm = mocker.patch("agents.orchestrator.call_llm")
    mock_llm.return_value = "response"

    orchestrator.handle("any message")

    _, kwargs = mock_llm.call_args
    tool_names = [
        decl["name"]
        for decl in kwargs["tools"][0]["function_declarations"]
    ]
    assert "ask_stock_agent" in tool_names
    assert "ask_portfolio_agent" in tool_names