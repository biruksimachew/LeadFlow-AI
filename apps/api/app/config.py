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

    communication_provider: str = "mock"
    communication_timeout_seconds: float = 15.0
    resend_api_key: str | None = None
    resend_from_email: str = (
        "NorthStar Home Services "
        "<onboarding@resend.dev>"
    )

    booking_provider: str = "configured"
    booking_base_url: str = (
        "https://cal.com/northstar-demo/service"
    )
    cal_webhook_secret: str | None = None

    dashboard_base_url: str = (
        "http://localhost:3000"
    )

    slack_hot_channel: str = "leadflow-hot"
    slack_dead_letter_channel: str = (
        "leadflow-alerts"
    )
    slack_bot_token: str | None = None
    slack_owner_user_id: str | None = None

    workflow_retry_enabled: bool = True
    workflow_retry_max_attempts: int = 3
    workflow_retry_base_delay_seconds: int = 30
    workflow_retry_max_delay_seconds: int = 300
    workflow_retry_poll_seconds: float = 2.0
    workflow_retry_batch_size: int = 10
    workflow_retry_stale_after_seconds: int = 120
    workflow_dead_letter_alert_retry_seconds: int = 60


settings = Settings()
