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

    hubspot_provider: str = "hubspot"

    hubspot_access_token: str | None = None

    hubspot_api_base_url: str = (
        "https://api.hubapi.com"
    )

    hubspot_api_version: str = "2026-03"

    hubspot_timeout_seconds: float = 15.0

    hubspot_deal_pipeline_id: str | None = None
    hubspot_deal_stage_id: str | None = None

settings = Settings()