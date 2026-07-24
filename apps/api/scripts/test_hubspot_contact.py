import asyncio

from app.providers.crm.factory import build_crm_provider


async def main() -> None:

    provider = build_crm_provider()

    try:

        result = await provider.upsert_contact(
            email=(
                "hubspot.test@example.com"
            ),
            phone_e164="+12025550991",
            properties={
                "email": (
                    "hubspot.test@example.com"
                ),
                "firstname": "HubSpot",
                "lastname": "Test",
                "phone": "+12025550991",
                "leadflow_phone_e164": (
                    "+12025550991"
                ),
                "leadflow_score": "72",
                "leadflow_source": "website",
                "leadflow_service_type": (
                    "plumbing"
                ),
                "leadflow_urgency": (
                    "within_24_hours"
                ),
                "leadflow_service_zone": (
                    "north"
                ),
                "leadflow_automation_status": (
                    "QUALIFIED_WARM"
                ),
                "leadflow_correlation_id": (
                    "hubspot-contact-test-001"
                ),
            },
        )

        print(
            "HubSpot contact:",
            result.contact_id,
            "created:",
            result.created,
        )

    finally:

        if hasattr(provider, "close"):
            await provider.close()


if __name__ == "__main__":
    asyncio.run(main())