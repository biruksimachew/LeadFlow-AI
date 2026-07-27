import json

import asyncpg


async def get_template(
    connection: asyncpg.Connection,
    template_key: str,
) -> dict:

    row = await connection.fetchrow(
        """
        select
            template_key,
            channel,
            subject_template,
            body_template
        from public.message_templates
        where template_key = $1
        and active = true;
        """,
        template_key,
    )

    if row is None:
        raise RuntimeError(
            f"Message template missing: {template_key}"
        )

    return dict(row)


async def communication_completed(
    connection: asyncpg.Connection,
    *,
    lead_id,
    channel: str,
    template_key: str,
) -> bool:

    row = await connection.fetchrow(
        """
        select status
        from public.communications
        where lead_id = $1
        and channel = $2
        and template_key = $3;
        """,
        lead_id,
        channel,
        template_key,
    )

    return bool(
        row
        and row["status"] in {
            "SENT",
            "SKIPPED",
        }
    )


async def persist_communication_sent(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    channel: str,
    template_key: str,
    recipient: str | None,
    provider: str,
    provider_message_id: str,
    payload: dict,
    consent_basis: str,
) -> None:

    await connection.execute(
        """
        insert into public.communications (
            lead_id,
            correlation_id,
            channel,
            template_key,
            recipient,
            provider,
            provider_message_id,
            status,
            consent_basis,
            payload,
            sent_at
        )
        values (
            $1,$2,$3,$4,$5,$6,$7,
            'SENT',$8,$9::jsonb,now()
        )
        on conflict (
            lead_id,
            channel,
            template_key
        )
        do update set
            recipient = excluded.recipient,
            provider = excluded.provider,
            provider_message_id =
                excluded.provider_message_id,
            status = 'SENT',
            consent_basis = excluded.consent_basis,
            payload = excluded.payload,
            error_code = null,
            error_message = null,
            sent_at = now();
        """,
        lead_id,
        correlation_id,
        channel,
        template_key,
        recipient,
        provider,
        provider_message_id,
        consent_basis,
        json.dumps(payload),
    )

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
            $1,$2,'COMMUNICATION_SENT',
            'provider',$3,'succeeded',$4::jsonb
        );
        """,
        lead_id,
        correlation_id,
        provider,
        json.dumps({
            "channel": channel,
            "template_key": template_key,
        }),
    )


async def persist_communication_failed(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    channel: str,
    template_key: str,
    recipient: str | None,
    provider: str,
    error_code: str,
    error_message: str,
    retryable: bool,
    consent_basis: str,
) -> None:

    payload = {
        "retryable": retryable,
    }

    await connection.execute(
        """
        insert into public.communications (
            lead_id,
            correlation_id,
            channel,
            template_key,
            recipient,
            provider,
            status,
            consent_basis,
            payload,
            error_code,
            error_message
        )
        values (
            $1,$2,$3,$4,$5,$6,
            'FAILED',$7,$8::jsonb,$9,$10
        )
        on conflict (
            lead_id,
            channel,
            template_key
        )
        do update set
            recipient = excluded.recipient,
            provider = excluded.provider,
            status = 'FAILED',
            consent_basis = excluded.consent_basis,
            payload = excluded.payload,
            error_code = excluded.error_code,
            error_message = excluded.error_message,
            provider_message_id = null,
            sent_at = null;
        """,
        lead_id,
        correlation_id,
        channel,
        template_key,
        recipient,
        provider,
        consent_basis,
        json.dumps(payload),
        error_code,
        error_message,
    )

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
            'COMMUNICATION_FAILED',
            'provider',
            $3,
            'failed',
            $4::jsonb,
            $5,
            $6
        );
        """,
        lead_id,
        correlation_id,
        provider,
        json.dumps({
            "channel": channel,
            "template_key": template_key,
            "recipient": recipient,
            "retryable": retryable,
        }),
        error_code,
        error_message,
    )


async def persist_communication_skipped(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    channel: str,
    template_key: str,
    reason: str,
) -> None:

    await connection.execute(
        """
        insert into public.communications (
            lead_id,
            correlation_id,
            channel,
            template_key,
            provider,
            status,
            consent_basis,
            payload
        )
        values (
            $1,$2,$3,$4,
            'system','SKIPPED',$5,$6::jsonb
        )
        on conflict (
            lead_id,
            channel,
            template_key
        )
        do nothing;
        """,
        lead_id,
        correlation_id,
        channel,
        template_key,
        reason,
        json.dumps({
            "reason": reason,
        }),
    )


async def get_or_create_booking_link(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    booking_url: str,
) -> str:

    existing = await connection.fetchrow(
        """
        select booking_url
        from public.appointments
        where lead_id = $1;
        """,
        lead_id,
    )

    if existing:
        return existing["booking_url"]

    await connection.execute(
        """
        insert into public.appointments (
            lead_id,
            correlation_id,
            provider,
            booking_url,
            status
        )
        values (
            $1,$2,'configured',$3,'LINK_SENT'
        );
        """,
        lead_id,
        correlation_id,
        booking_url,
    )

    await connection.execute(
        """
        update public.leads
        set appointment_status = 'link_sent'
        where id = $1;
        """,
        lead_id,
    )

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            result,
            details
        )
        values (
            $1,$2,'BOOKING_LINK_CREATED',
            'system','succeeded',$3::jsonb
        );
        """,
        lead_id,
        correlation_id,
        json.dumps({
            "provider": "configured",
        }),
    )

    return booking_url