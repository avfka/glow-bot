import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str
    openai_api_key: str
    database_url: str
    webhook_url: str = ""
    port: int = 8000

    # Which analyzer to use: "openai" | "ml_engine"
    skin_analyzer_backend: str = "openai"

    openai_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
