from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    ai_provider: str = "mock"

    openai_api_key: str | None = None

    openai_model: str = "gpt-5.6-luna"

    ai_prompt_version: str = "lead-assessment-v1"

    ai_timeout_seconds: float = 20.0

settings = Settings()