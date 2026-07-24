from app.config import settings
from app.providers.crm.base import (
    CRMProvider,
    CRMProviderError,
)
from app.providers.crm.hubspot import (
    HubSpotProvider,
)


def build_crm_provider() -> CRMProvider:

    provider = (
        settings.hubspot_provider.lower()
    )

    if provider == "hubspot":
        return HubSpotProvider()

    raise CRMProviderError(
        "UNKNOWN_CRM_PROVIDER",
        (
            f"Unsupported CRM provider: "
            f"{provider}"
        ),
    )