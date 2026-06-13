class FinchError(Exception):
    """Base exception for all Finch application errors."""
    status_code = 500
    message = "An unexpected error occurred."

    def __init__(self, detail: str = None):
        self.detail = detail or self.message
        super().__init__(self.detail)


class AgentError(FinchError):
    """Raised when an agent fails to process a request."""
    status_code = 502  # Bad Gateway — upstream (LLM) dependency failed
    message = "The assistant encountered an error processing your request."


class LLMQuotaError(FinchError):
    """Raised when the LLM API quota is exhausted."""
    status_code = 429
    message = "The assistant is temporarily unavailable due to rate limits. Please try again shortly."


class InsightNotFoundError(FinchError):
    """Raised when no insight report has been generated yet."""
    status_code = 404
    message = "No insight report has been generated yet."