import json
from dataclasses import dataclass

import asyncpg

from app.models.lead import (
    NormalizedLead,
)
from app.repositories.qualification import (
    get_existing_qualification,
)


@dataclass
class OrchestrationContext:
    lead_id: str
    correlation_id: str

    status: str
    score: int | None

    assigned_owner_id: str | None
    assigned_queue: str | None

    crm_sync_status: str | None

    lead: NormalizedLead

    qualification: dict | None


async def load_orchestration_context(
    connection: asyncpg.Connection,
    *,
    lead_id: str,
) -> OrchestrationContext:

    lead_row = await connection.fetchrow(
        """
        select
            id,
            correlation_id,
            status,
            score,
            assigned_owner_id,
            assigned_queue,
            crm_sync_status
        from public.leads
        where id = $1::uuid;
        """,
        lead_id,
    )

    if lead_row is None:
        raise LookupError(
            "Lead does not exist."
        )

    source_row = await connection.fetchrow(
        """
        select
            normalized_payload
        from public.lead_source_events
        where lead_id = $1::uuid
          and ingestion_status = 'PROCESSED'
        limit 1;
        """,
        lead_id,
    )

    if source_row is None:
        raise RuntimeError(
            "Canonical normalized lead payload "
            "does not exist."
        )

    normalized_payload = (
        source_row[
            "normalized_payload"
        ]
    )

    if isinstance(
        normalized_payload,
        str,
    ):
        normalized_payload = (
            json.loads(
                normalized_payload
            )
        )

    normalized_lead = (
        NormalizedLead.model_validate(
            normalized_payload
        )
    )

    qualification = (
        await get_existing_qualification(
            connection,
            lead_id,
        )
    )

    return OrchestrationContext(
        lead_id=str(
            lead_row["id"]
        ),
        correlation_id=(
            lead_row[
                "correlation_id"
            ]
        ),
        status=lead_row["status"],
        score=lead_row["score"],
        assigned_owner_id=(
            lead_row[
                "assigned_owner_id"
            ]
        ),
        assigned_queue=(
            lead_row[
                "assigned_queue"
            ]
        ),
        crm_sync_status=(
            lead_row[
                "crm_sync_status"
            ]
        ),
        lead=normalized_lead,
        qualification=qualification,
    )