import logging
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from core.exceptions import LLMQuotaError
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt
from config import settings
from core.tool_executor import execute_tool

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

MODEL = "gemini-2.5-flash"

MAX_TOOL_ITERATIONS = 5


@retry(
    retry=retry_if_exception_type(ClientError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _generate(contents, config):
    return client.models.generate_content(model=MODEL, contents=contents, config=config)


def call_llm(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 1024,
    tools: list[dict] = None,
) -> str:
    logger.info(f"Calling LLM with {len(messages)} messages, tools={'yes' if tools else 'no'}")

    contents = _convert_messages(messages)

    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        tools=tools,
    )

    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            response = _generate(contents, config)
        except ClientError as e:
            if e.code == 429:
                logger.error("LLM quota exhausted after retries")
                raise LLMQuotaError() from e
            raise

        part = response.candidates[0].content.parts[0]

        if not (part.function_call and part.function_call.name):
        # No tool requested — this is the final answer
            return response.text

        fn_call = part.function_call
        fn_name = fn_call.name
        fn_args = dict(fn_call.args)

        logger.info(f"[iter {iteration + 1}] LLM requested tool call: {fn_name}({fn_args})")

        tool_result = execute_tool(fn_name, fn_args)

        contents.append(response.candidates[0].content)
        
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=fn_name,
                        response=tool_result,
                    )
                ],
            )
        )
    # Safety net: hit max iterations without a final text answer
    logger.warning(f"Hit MAX_TOOL_ITERATIONS ({MAX_TOOL_ITERATIONS}) without final response")
    return "I gathered some information but wasn't able to fully complete the analysis. Please try rephrasing your question."


def _convert_messages(messages: list[dict]) -> list[dict]:
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map[msg["role"]], "parts": [{"text": msg["content"]}]}
        for msg in messages
    ]