from app.config import settings

from app.providers.communications.base import (
    CommunicationProvider,
    CommunicationProviderError,
)

from app.providers.communications.live import (
    LiveCommunicationProvider,
)

from app.providers.communications.mock import (
    MockCommunicationProvider,
)


def build_communication_provider(
) -> CommunicationProvider:

    provider = (
        settings.communication_provider
        .strip()
        .lower()
    )

    if provider == "mock":
        return MockCommunicationProvider()

    if provider == "live":
        return LiveCommunicationProvider()

    raise CommunicationProviderError(
        "UNKNOWN_COMMUNICATION_PROVIDER",
        (
            "Unsupported communication provider: "
            f"{provider}"
        ),
    )