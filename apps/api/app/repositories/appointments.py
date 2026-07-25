from datetime import datetime
import json

import asyncpg


class AppointmentLeadNotFound(RuntimeError):
    pass


def parse_iso_datetime(
    value: str,
) -> datetime:
    """
    Convert Cal.com ISO-8601 timestamps into timezone-aware
    Python datetime objects accepted by asyncpg.
    """

    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

async def process_booking_created(
    connection: asyncpg.Connection,
    *,
    external_appointment_id: str,
    attendee_email: str,
    start_at: str,
    end_at: str,
    timezone: str | None,
    provider_payload: dict,
) -> dict:

    existing = await connection.fetchrow(
        """
        select
            a.id,
            a.lead_id,
            a.correlation_id,
            a.status,
            a.external_appointment_id,
            l.hubspot_deal_id
        from public.appointments a
        join public.leads l
            on l.id = a.lead_id
        where a.external_appointment_id = $1
        for update;
        """,
        external_appointment_id,
    )

    if existing is None:

        existing = await connection.fetchrow(
            """
            select
                a.id,
                a.lead_id,
                a.correlation_id,
                a.status,
                a.external_appointment_id,
                l.hubspot_deal_id
            from public.appointments a
            join public.leads l
                on l.id = a.lead_id
            where lower(l.email_normalized) =
                lower($1)
            and a.status = 'LINK_SENT'
            order by a.created_at desc
            limit 1
            for update;
            """,
            attendee_email,
        )

    if existing is None:
        raise AppointmentLeadNotFound(
            "No pending LeadFlow appointment matches "
            "the Cal.com attendee."
        )

    replayed = (
        existing["status"] == "BOOKED"
        and existing[
            "external_appointment_id"
        ] == external_appointment_id
    )

    if replayed:

        return {
            "lead_id": existing["lead_id"],
            "correlation_id": (
                existing["correlation_id"]
            ),
            "hubspot_deal_id": (
                existing["hubspot_deal_id"]
            ),
            "replayed": True,
        }


    start_datetime = parse_iso_datetime(
        start_at
    )

    end_datetime = parse_iso_datetime(
        end_at
    )

    await connection.execute(
        """
        update public.appointments
        set
            external_appointment_id = $2,
            attendee_email = $3,
            start_at = $4::timestamptz,
            end_at = $5::timestamptz,
            timezone = $6,
            status = 'BOOKED',
            provider_payload = $7::jsonb,
            webhook_received_at = now(),
            updated_at = now()
        where id = $1;
        """,
        existing["id"],
        external_appointment_id,
        attendee_email,
        start_datetime,
        end_datetime,
        timezone,
        json.dumps(provider_payload),
    )

    await connection.execute(
        """
        update public.leads
        set
            status = 'APPOINTMENT_BOOKED',
            appointment_status = 'booked'
        where id = $1;
        """,
        existing["lead_id"],
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
            $1,
            $2,
            'APPOINTMENT_BOOKED',
            'provider',
            'cal.com',
            'succeeded',
            $3::jsonb
        );
        """,
        existing["lead_id"],
        existing["correlation_id"],
        json.dumps({
            "external_appointment_id": (
                external_appointment_id
            ),
            "start_at": start_at,
            "end_at": end_at,
            "timezone": timezone,
        }),
    )

    return {
        "lead_id": existing["lead_id"],
        "correlation_id": (
            existing["correlation_id"]
        ),
        "hubspot_deal_id": (
            existing["hubspot_deal_id"]
        ),
        "replayed": False,
    }