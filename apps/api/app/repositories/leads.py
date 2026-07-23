import json
from typing import Any

import asyncpg

from app.models.lead import LeadIntakeRequest, NormalizedLead


class DuplicateIdentityConflict(Exception):
    """
    Raised when email and phone match different canonical leads.

    Example:
    email -> Lead A
    phone -> Lead B

    LeadFlow must not automatically choose one.
    """
    pass


async def _get_existing_intake(
    connection: asyncpg.Connection,
    idempotency_key: str,
) -> dict[str, Any] | None:
    """
    Return a previously stored intake when the same external
    event is replayed.
    """
    row = await connection.fetchrow(
        """
        select
            se.lead_id,
            se.intake_id,
            se.correlation_id,
            se.ingestion_status,
            se.normalized_payload,
            l.status
        from public.lead_source_events se
        left join public.leads l
            on l.id = se.lead_id
        where se.idempotency_key = $1
        limit 1;
        """,
        idempotency_key,
    )

    if row is None:
        return None

    normalized_payload = row["normalized_payload"]

    if isinstance(normalized_payload, str):
        normalized_payload = json.loads(normalized_payload)

    return {
        "lead_id": (
            str(row["lead_id"])
            if row["lead_id"]
            else None
        ),
        "intake_id": row["intake_id"],
        "correlation_id": row["correlation_id"],
        "status": row["status"] or "RECEIVED",
        "ingestion_status": row["ingestion_status"],
        "normalized_payload": normalized_payload,
        "replayed": True,
        "duplicate": (
            row["ingestion_status"] == "DUPLICATE"
        ),
        "duplicate_match_fields": [],
    }



async def _find_duplicate_lead(
    connection: asyncpg.Connection,
    email_normalized: str | None,
    phone_e164: str | None,
) -> dict[str, Any] | None:
    """
    Search canonical leads using normalized email and phone.

    Returns one canonical lead when there is an unambiguous match.

    Raises DuplicateIdentityConflict if email and phone point
    to different canonical leads.
    """

    if email_normalized is None and phone_e164 is None:
        return None

    rows = await connection.fetch(
        """
        select
            id,
            email_normalized,
            phone_e164,
            status
        from public.leads
        where
            (
                $1::text is not null
                and email_normalized = $1
            )
            or
            (
                $2::text is not null
                and phone_e164 = $2
            )
        order by created_at asc;
        """,
        email_normalized,
        phone_e164,
    )

    if not rows:
        return None

    matches_by_lead: dict[str, set[str]] = {}

    for row in rows:
        lead_id = str(row["id"])

        matches_by_lead.setdefault(
            lead_id,
            set(),
        )

        if (
            email_normalized is not None
            and row["email_normalized"] == email_normalized
        ):
            matches_by_lead[lead_id].add("email")

        if (
            phone_e164 is not None
            and row["phone_e164"] == phone_e164
        ):
            matches_by_lead[lead_id].add("phone")

    if len(matches_by_lead) > 1:
        raise DuplicateIdentityConflict(
            "Email and phone match different canonical leads."
        )

    matched_lead_id = next(iter(matches_by_lead))

    matched_fields = sorted(
        matches_by_lead[matched_lead_id]
    )

    matched_row = next(
        row
        for row in rows
        if str(row["id"]) == matched_lead_id
    )

    return {
        "lead_id": matched_row["id"],
        "status": matched_row["status"],
        "match_fields": matched_fields,
    }


async def _persist_duplicate_event(
    connection: asyncpg.Connection,
    *,
    existing_lead_id,
    request_lead: LeadIntakeRequest,
    normalized_lead: NormalizedLead,
    intake_id: str,
    correlation_id: str,
    idempotency_key: str,
    match_fields: list[str],
) -> None:

    raw_payload = json.dumps(
        request_lead.model_dump(mode="json")
    )

    normalized_payload = json.dumps(
        normalized_lead.model_dump(mode="json")
    )

    await connection.execute(
        """
        insert into public.lead_source_events (
            lead_id,
            intake_id,
            correlation_id,
            source,
            idempotency_key,
            ingestion_status,
            raw_payload,
            normalized_payload
        )
        values (
            $1,
            $2,
            $3,
            $4,
            $5,
            'DUPLICATE',
            $6::jsonb,
            $7::jsonb
        );
        """,
        existing_lead_id,
        intake_id,
        correlation_id,
        normalized_lead.source.value,
        idempotency_key,
        raw_payload,
        normalized_payload,
    )

    duplicate_details = json.dumps(
        {
            "match_fields": match_fields,
            "action": "linked_to_existing_lead",
        }
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
            $1,
            $2,
            'DUPLICATE_DETECTED',
            'system',
            'succeeded',
            $3::jsonb
        );
        """,
        existing_lead_id,
        correlation_id,
        duplicate_details,
    )

async def persist_received_lead(
    pool: asyncpg.Pool,
    *,
    request_lead: LeadIntakeRequest,
    normalized_lead: NormalizedLead,
    intake_id: str,
    correlation_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """
    Persist the canonical lead, source event and initial workflow
    event in one database transaction.

    Either all records are committed or none are.
    """

    raw_payload = json.dumps(
        request_lead.model_dump(mode="json")
    )

    normalized_payload = json.dumps(
        normalized_lead.model_dump(mode="json")
    )

    workflow_details = json.dumps(
        {
            "source": request_lead.source.value,
            "lead_status": "RECEIVED",
        }
    )

    async with pool.acquire() as connection:

        existing = await _get_existing_intake(
            connection,
            idempotency_key,
        )

        if existing is not None:
            return existing




        duplicate = await _find_duplicate_lead(
            connection,
            normalized_lead.email_normalized,
            normalized_lead.phone_e164,
        )

        if duplicate is not None:

            async with connection.transaction():

                await _persist_duplicate_event(
                    connection,
                    existing_lead_id=duplicate["lead_id"],
                    request_lead=request_lead,
                    normalized_lead=normalized_lead,
                    intake_id=intake_id,
                    correlation_id=correlation_id,
                    idempotency_key=idempotency_key,
                    match_fields=duplicate["match_fields"],
                )

            return {
                "lead_id": str(duplicate["lead_id"]),
                "intake_id": intake_id,
                "correlation_id": correlation_id,
                "status": "DUPLICATE",
                "ingestion_status": "DUPLICATE",
                "normalized_payload": normalized_lead.model_dump(
                    mode="json"
                ),
                "replayed": False,
                "duplicate": True,
                "duplicate_match_fields": duplicate[
                    "match_fields"
                ],
            }

        try:
            async with connection.transaction():

                lead_id = await connection.fetchval(
                    """
                    insert into public.leads (
                        correlation_id,
                        source,
                        full_name,
                        email_normalized,
                        phone_e164,
                        service_type,
                        location_text,
                        urgency,
                        message,
                        consent_marketing,
                        preferred_contact,
                        status
                    )
                    values (
                        $1, $2, $3, $4, $5, $6,
                        $7, $8, $9, $10, $11, 'RECEIVED'
                    )
                    returning id;
                    """,
                    correlation_id,
                    normalized_lead.source.value,
                    normalized_lead.full_name,
                    normalized_lead.email_normalized,
                    normalized_lead.phone_e164,
                    normalized_lead.service_type.value,
                    normalized_lead.location_raw,
                    normalized_lead.urgency.value,
                    normalized_lead.message,
                    normalized_lead.consent_marketing,
                    normalized_lead.preferred_contact.value,
                )

                await connection.execute(
                    """
                    insert into public.lead_source_events (
                        lead_id,
                        intake_id,
                        correlation_id,
                        source,
                        idempotency_key,
                        ingestion_status,
                        raw_payload,
                        normalized_payload
                    )
                    values (
                        $1, $2, $3, $4, $5,
                        'PROCESSED',
                        $6::jsonb,
                        $7::jsonb
                    );
                    """,
                    lead_id,
                    intake_id,
                    correlation_id,
                    normalized_lead.source.value,
                    idempotency_key,
                    raw_payload,
                    normalized_payload,
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
                        $1,
                        $2,
                        'LEAD_RECEIVED',
                        'system',
                        'succeeded',
                        $3::jsonb
                    );
                    """,
                    lead_id,
                    correlation_id,
                    workflow_details,
                )

        except asyncpg.UniqueViolationError:
            # Handles simultaneous retries using the same
            # idempotency key.
            existing = await _get_existing_intake(
                connection,
                idempotency_key,
            )

            if existing is not None:
                return existing

            raise

    return {
        "lead_id": str(lead_id),
        "intake_id": intake_id,
        "correlation_id": correlation_id,
        "status": "RECEIVED",
        "ingestion_status": "PROCESSED",
        "normalized_payload": normalized_lead.model_dump(
            mode="json"
        ),
        "replayed": False,
        "duplicate": False,
        "duplicate_match_fields": [],
    }