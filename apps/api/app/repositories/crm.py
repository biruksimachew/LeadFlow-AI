import json

import asyncpg


async def get_crm_sync_state(
    connection: asyncpg.Connection,
    lead_id,
) -> dict | None:

    row = await connection.fetchrow(
        """
        select
            crm_sync_status,
            hubspot_contact_id,
            hubspot_deal_id,
            crm_last_error_code
        from public.leads
        where id = $1;
        """,
        lead_id,
    )

    return dict(row) if row else None


async def persist_crm_sync_success(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    contact_id: str,
    deal_id: str,
    contact_created: bool,
    deal_created: bool,
) -> None:

    await connection.execute(
        """
        update public.leads
        set
            hubspot_contact_id = $2,
            hubspot_deal_id = $3,
            crm_sync_status = 'SUCCEEDED',
            crm_last_synced_at = now(),
            crm_last_error_code = null
        where id = $1;
        """,
        lead_id,
        contact_id,
        deal_id,
    )

    details = json.dumps({
        "contact_id": contact_id,
        "deal_id": deal_id,
        "contact_created": contact_created,
        "deal_created": deal_created,
    })

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            provider,
            result,
            details
        )
        values (
            $1,
            $2,
            'CRM_SYNC_COMPLETED',
            'provider',
            'hubspot',
            'succeeded',
            $3::jsonb
        );
        """,
        lead_id,
        correlation_id,
        details,
    )


async def persist_crm_sync_failure(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    error_code: str,
    error_message: str,
    retryable: bool,
) -> None:

    await connection.execute(
        """
        update public.leads
        set
            crm_sync_status = 'FAILED',
            crm_last_error_code = $2
        where id = $1;
        """,
        lead_id,
        error_code,
    )

    details = json.dumps({
        "retryable": retryable,
        "error_code": error_code,
    })

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            provider,
            result,
            details,
            error_code,
            error_message
        )
        values (
            $1,
            $2,
            'CRM_SYNC_FAILED',
            'provider',
            'hubspot',
            'failed',
            $3::jsonb,
            $4,
            $5
        );
        """,
        lead_id,
        correlation_id,
        details,
        error_code,
        error_message[:1000],
    )