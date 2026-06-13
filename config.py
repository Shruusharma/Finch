from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "Finch"
    app_env: str = "production"
    gemini_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

if not settings.gemini_api_key:
    import logging
    logging.getLogger(__name__).warning(
        "GEMINI_API_KEY is not set — LLM calls will fail. "
        "Set this environment variable before starting the server."
    )