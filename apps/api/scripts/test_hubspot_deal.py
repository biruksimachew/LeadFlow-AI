import asyncio

from app.providers.crm.factory import (
    build_crm_provider,
)

from app.services.deal_mapping import (
    build_deal_properties,
)

from app.models.lead import (
    LeadSource,
    NormalizedLead,
    PreferredContact,
    ServiceType,
    Urgency,
)


TEST_LEAD_ID = (
    "00000000-0000-0000-0000-000000000901"
)


async def main() -> None:

    provider = build_crm_provider()

    try:

        lead = NormalizedLead(
            full_name="HubSpot Deal Test",
            email_raw="hubspot.deal@example.com",
            email_normalized=(
                "hubspot.deal@example.com"
            ),
            phone_raw="+1 202 555 0992",
            phone_e164="+12025550992",
            service_type=ServiceType.PLUMBING,
            location_raw=(
                "North District, 10021"
            ),
            urgency=Urgency.WITHIN_24_HOURS,
            message=(
                "Synthetic HubSpot deal test."
            ),
            source=LeadSource.WEBSITE,
            preferred_contact=(
                PreferredContact.EMAIL
            ),
            consent_marketing=False,
        )

        contact = await provider.upsert_contact(
            email=lead.email_normalized,
            phone_e164=lead.phone_e164,
            properties={
                "email": lead.email_normalized,
                "firstname": "HubSpot",
                "lastname": "Deal Test",
                "phone": lead.phone_e164,
                "leadflow_phone_e164": (
                    lead.phone_e164
                ),
                "leadflow_score": "72",
                "leadflow_source": "website",
                "leadflow_service_type": (
                    "plumbing"
                ),
                "leadflow_urgency": (
                    "within_24_hours"
                ),
                "leadflow_service_zone": "north",
                "leadflow_automation_status": (
                    "QUALIFIED_WARM"
                ),
                "leadflow_correlation_id": (
                    "hubspot-deal-test-001"
                ),
            },
        )

        properties = build_deal_properties(
            lead_id=TEST_LEAD_ID,
            lead=lead,
            score=72,
            status="QUALIFIED_WARM",
            correlation_id=(
                "hubspot-deal-test-001"
            ),
        )

        deal = await provider.upsert_deal(
            leadflow_lead_id=TEST_LEAD_ID,
            properties=properties,
        )

        await provider.associate_contact_with_deal(
            contact_id=contact.contact_id,
            deal_id=deal.deal_id,
        )

        print(
            "Contact:",
            contact.contact_id,
        )

        print(
            "Deal:",
            deal.deal_id,
            "created:",
            deal.created,
        )

        print(
            "Association: OK"
        )

    finally:

        if hasattr(provider, "close"):
            await provider.close()


if __name__ == "__main__":
    asyncio.run(main())