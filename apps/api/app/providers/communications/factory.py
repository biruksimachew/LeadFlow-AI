from app.config import settings

from app.providers.communications.base import (
    CommunicationProvider,
    CommunicationProviderError,
)

from app.providers.communications.mock import (
    MockCommunicationProvider,
)


def build_communication_provider(
) -> CommunicationProvider:

    provider = (
        settings.communication_provider
        .lower()
    )

    if provider == "mock":
        return MockCommunicationProvider()

    raise CommunicationProviderError(
        "UNKNOWN_COMMUNICATION_PROVIDER",
        f"Unsupported communication provider: {provider}",
    )