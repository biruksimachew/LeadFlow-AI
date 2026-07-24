from app.config import settings
from app.providers.ai.base import (
    AIProvider,
    AIProviderError,
)
from app.providers.ai.mock import MockAIProvider
from app.providers.ai.openai_provider import (
    OpenAIAssessmentProvider,
)


def build_ai_provider() -> AIProvider:

    provider = settings.ai_provider.lower()

    if provider == "mock":
        return MockAIProvider()

    if provider == "openai":
        return OpenAIAssessmentProvider()

    raise AIProviderError(
        "UNKNOWN_AI_PROVIDER",
        f"Unsupported AI provider: {provider}",
    )