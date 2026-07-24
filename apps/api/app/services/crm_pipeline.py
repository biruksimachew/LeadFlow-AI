import asyncpg

from app.providers.crm.base import CRMProviderError
from app.providers.crm.factory import build_crm_provider
from app.repositories.crm import (
    get_crm_sync_state,
    persist_crm_sync_failure,
    persist_crm_sync_success,
)
from app.services.crm_mapping import build_contact_properties
from app.services.deal_mapping import build_deal_properties


CRM_STATUSES = {
    "QUALIFIED_HOT",
    "QUALIFIED_WARM",
    "COLD",
}


async def run_crm_sync(
    pool,
    *,
    lead_id,
    correlation_id: str,
    lead,
    qualification: dict,
    final_status: str,
) -> None:

    # Review/disqualified leads don't enter active CRM.
    if final_status not in CRM_STATUSES:
        return

    async with pool.acquire() as connection:

        state = await get_crm_sync_state(
            connection,
            lead_id,
        )

    # Completed replay: don't call HubSpot again.
    if (
        state
        and state["crm_sync_status"] == "SUCCEEDED"
    ):
        return

    breakdown = (
        qualification.get("score_breakdown")
        or {}
    )

    service_zone = (
        breakdown
        .get("service_area", {})
        .get("zone")
    )

    provider = None

    try:

        provider = build_crm_provider()

        contact_properties = build_contact_properties(
            lead=lead,
            score=qualification["score"],
            status=final_status,
            correlation_id=correlation_id,
            service_zone=service_zone,
        )

        contact = await provider.upsert_contact(
            email=lead.email_normalized,
            phone_e164=lead.phone_e164,
            properties=contact_properties,
        )

        deal_properties = build_deal_properties(
            lead_id=str(lead_id),
            lead=lead,
            score=qualification["score"],
            status=final_status,
            correlation_id=correlation_id,
        )

        deal = await provider.upsert_deal(
            leadflow_lead_id=str(lead_id),
            properties=deal_properties,
        )

        await provider.associate_contact_with_deal(
            contact_id=contact.contact_id,
            deal_id=deal.deal_id,
        )

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_crm_sync_success(
                    connection,
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    contact_id=contact.contact_id,
                    deal_id=deal.deal_id,
                    contact_created=contact.created,
                    deal_created=deal.created,
                )

    except CRMProviderError as exc:

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_crm_sync_failure(
                    connection,
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    error_code=exc.code,
                    error_message=exc.message,
                    retryable=exc.retryable,
                )

        # CRM failure must NOT lose the lead.
        return

    except (asyncpg.PostgresError, OSError):
        raise

    except Exception as exc:

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_crm_sync_failure(
                    connection,
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    error_code="CRM_PROCESSING_ERROR",
                    error_message=str(exc),
                    retryable=False,
                )

    finally:

        if (
            provider is not None
            and hasattr(provider, "close")
        ):
            await provider.close()