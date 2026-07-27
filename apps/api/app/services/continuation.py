import json
import logging
from dataclasses import asdict, dataclass

from app.models.lead import NormalizedLead
from app.repositories.qualification import (
    get_existing_qualification,
)
from app.services.action_pipeline import (
    run_post_qualification_actions,
)
from app.services.crm_pipeline import run_crm_sync
from app.services.routing import route_lead
from app.repositories.workflow_errors import (
    resolve_workflow_error_for_action,
    upsert_workflow_error,
)

logger = logging.getLogger(__name__)


ACTIONABLE_STATUSES = {
    "QUALIFIED_HOT",
    "QUALIFIED_WARM",
    "COLD",
}


@dataclass(slots=True)
class ContinuationResult:
    status: str
    final_status: str | None = None
    owner_id: str | None = None
    crm_sync_status: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


async def _record_event(
    pool,
    *,
    lead_id,
    correlation_id: str,
    event_type: str,
    result: str,
    details: dict,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    async with pool.acquire() as connection:
        await connection.execute(
            """
            insert into public.workflow_events (
                lead_id,
                correlation_id,
                event_type,
                actor_type,
                actor_id,
                provider,
                result,
                details,
                error_code,
                error_message
            )
            values (
                $1::uuid,
                $2,
                $3,
                'workflow',
                null,
                null,
                $4,
                $5::jsonb,
                $6,
                $7
            );
            """,
            lead_id,
            correlation_id,
            event_type,
            result,
            json.dumps(details),
            error_code,
            error_message,
        )


async def _load_continuation_context(
    pool,
    *,
    lead_id,
) -> tuple[
    dict,
    NormalizedLead,
    dict,
]:
    async with pool.acquire() as connection:

        lead_row = await connection.fetchrow(
            """
            select
                id,
                correlation_id,
                status,
                score,
                assigned_owner_id,
                crm_sync_status
            from public.leads
            where id = $1::uuid;
            """,
            lead_id,
        )

        if lead_row is None:
            raise RuntimeError(
                "Lead does not exist."
            )

        source_row = await connection.fetchrow(
            """
            select
                normalized_payload
            from public.lead_source_events
            where lead_id = $1::uuid
            order by
                case
                    when ingestion_status = 'PROCESSED'
                    then 0
                    else 1
                end
            limit 1;
            """,
            lead_id,
        )

        if source_row is None:
            raise RuntimeError(
                "Normalized lead payload is missing."
            )

        normalized_payload = (
            source_row["normalized_payload"]
        )

        if isinstance(
            normalized_payload,
            str,
        ):
            normalized_payload = json.loads(
                normalized_payload
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

        if qualification is None:
            raise RuntimeError(
                "Qualification record is missing."
            )

    return (
        dict(lead_row),
        normalized_lead,
        qualification,
    )



def _get_failure_metadata(
    exc: Exception,
) -> tuple[
    str,
    str,
    bool,
    str | None,
]:

    error_code = getattr(
        exc,
        "code",
        "LEAD_CONTINUATION_FAILED",
    )

    error_message = getattr(
        exc,
        "message",
        str(exc),
    )

    retryable = bool(
        getattr(
            exc,
            "retryable",
            False,
        )
    )

    provider = None

    upper_code = str(
        error_code
    ).upper()

    if upper_code.startswith(
        "RESEND_"
    ):
        provider = "resend"

    elif upper_code.startswith(
        "SLACK_"
    ):
        provider = "slack"

    elif upper_code.startswith(
        "TWILIO_"
    ):
        provider = "twilio"

    elif upper_code.startswith(
        "HUBSPOT_"
    ):
        provider = "hubspot"

    return (
        str(error_code),
        str(error_message),
        retryable,
        provider,
    )

async def run_lead_continuation(
    pool,
    *,
    lead_id,
    trigger: str,
    initiated_by: str | None = None,
    force_crm_sync: bool = False,
) -> ContinuationResult:

    correlation_id: str | None = None

    try:
        (
            lead_row,
            lead,
            qualification,
        ) = await _load_continuation_context(
            pool,
            lead_id=lead_id,
        )

        correlation_id = lead_row[
            "correlation_id"
        ]

        final_status = lead_row["status"]

        # A human may override the canonical score.
        # Preserve the original qualification record,
        # but use the canonical score downstream.
        effective_qualification = dict(
            qualification
        )

        effective_qualification["score"] = (
            lead_row["score"]
        )

        await _record_event(
            pool,
            lead_id=lead_id,
            correlation_id=correlation_id,
            event_type=(
                "WORKFLOW_CONTINUATION_STARTED"
            ),
            result="succeeded",
            details={
                "trigger": trigger,
                "initiated_by": initiated_by,
                "final_status": final_status,
            },
        )

        # ----------------------------------------------------
        # Nothing further should happen for review/disqualified
        # states.
        # ----------------------------------------------------

        if (
            final_status
            not in ACTIONABLE_STATUSES
        ):
            await _record_event(
                pool,
                lead_id=lead_id,
                correlation_id=correlation_id,
                event_type=(
                    "WORKFLOW_CONTINUATION_SKIPPED"
                ),
                result="succeeded",
                details={
                    "trigger": trigger,
                    "final_status": final_status,
                    "reason": (
                        "Final status has no "
                        "downstream actions."
                    ),
                },
            )

            return ContinuationResult(
                status="SKIPPED",
                final_status=final_status,
            )

        # ----------------------------------------------------
        # Routing
        # ----------------------------------------------------

        breakdown = (
            effective_qualification.get(
                "score_breakdown"
            )
            or {}
        )

        service_zone = (
            breakdown
            .get("service_area", {})
            .get("zone")
        )

        async with (
            pool.acquire()
            as connection
        ):
            async with (
                connection.transaction()
            ):
                routing_result = (
                    await route_lead(
                        connection,
                        lead_id=lead_id,
                        correlation_id=(
                            correlation_id
                        ),
                        service_type=(
                            lead.service_type.value
                        ),
                        service_zone=(
                            service_zone
                        ),
                    )
                )

        owner_id = routing_result.owner_id

        # ----------------------------------------------------
        # CRM
        # ----------------------------------------------------

        await run_crm_sync(
            pool,
            lead_id=lead_id,
            correlation_id=correlation_id,
            lead=lead,
            qualification=(
                effective_qualification
            ),
            final_status=final_status,
            owner_id=owner_id,
            force=force_crm_sync,
        )

        async with (
            pool.acquire()
            as connection
        ):
            crm_state = (
                await connection.fetchrow(
                    """
                    select
                        crm_sync_status,
                        last_error_code
                    from public.leads
                    where id = $1::uuid;
                    """,
                    lead_id,
                )
            )

        crm_sync_status = (
            crm_state["crm_sync_status"]
            if crm_state
            else None
        )

        if crm_sync_status != "SUCCEEDED":
            error_code = (
                crm_state[
                    "last_error_code"
                ]
                if crm_state
                else None
            )

            raise RuntimeError(
                "CRM synchronization did not "
                f"succeed. State="
                f"{crm_sync_status}, "
                f"error={error_code}"
            )

        # ----------------------------------------------------
        # Communication / booking / Slack
        # ----------------------------------------------------

        await run_post_qualification_actions(
            pool,
            lead_id=lead_id,
            correlation_id=correlation_id,
            lead=lead,
            score=effective_qualification[
                "score"
            ],
            final_status=final_status,
            owner_id=owner_id,
        )

        await _record_event(
            pool,
            lead_id=lead_id,
            correlation_id=correlation_id,
            event_type=(
                "WORKFLOW_CONTINUATION_SUCCEEDED"
            ),
            result="succeeded",
            details={
                "trigger": trigger,
                "initiated_by": initiated_by,
                "final_status": final_status,
                "owner_id": owner_id,
                "crm_sync_status": (
                    crm_sync_status
                ),
            },
        )

        async with pool.acquire() as connection:

            async with connection.transaction():

                await resolve_workflow_error_for_action(
                    connection,
                    lead_id=lead_id,
                    failed_action="lead_continuation",
                    resolution_notes=(
                        "Workflow continuation "
                        "completed successfully."
                    ),
                )

        return ContinuationResult(
            status="SUCCEEDED",
            final_status=final_status,
            owner_id=owner_id,
            crm_sync_status=(
                crm_sync_status
            ),
        )

    except Exception as exc:
        logger.exception(
            "Lead continuation failed. "
            "lead_id=%s trigger=%s",
            lead_id,
            trigger,
        )
        (
            error_code,
            error_message,
            retryable,
            provider,
        ) = _get_failure_metadata(
            exc
        )

        if correlation_id is not None:

            try:
                async with (
                    pool.acquire()
                    as connection
                ):
                    async with (
                        connection.transaction()
                    ):
                        await upsert_workflow_error(
                            connection,
                            lead_id=lead_id,
                            correlation_id=(
                                correlation_id
                            ),
                            failed_action=(
                                "lead_continuation"
                            ),
                            provider=provider,
                            error_code=(
                                error_code
                            ),
                            error_message=(
                                error_message[
                                    :1000
                                ]
                            ),
                            retryable=retryable,
                        )

            except Exception:
                logger.exception(
                    "Unable to persist "
                    "workflow error."
                )

        if correlation_id is not None:
            try:
                await _record_event(
                    pool,
                    lead_id=lead_id,
                    correlation_id=(
                        correlation_id
                    ),
                    event_type=(
                        "WORKFLOW_CONTINUATION_FAILED"
                    ),
                    result="failed",
                    details={
                        "trigger": trigger,
                        "initiated_by": (
                            initiated_by
                        ),
                    },
                    error_code=error_code,
                    error_message=(
                        error_message[:1000]
                    ),
                )
            except Exception:
                logger.exception(
                    "Unable to persist "
                    "continuation failure event."
                )

        return ContinuationResult(
            status="FAILED",
            error_code=error_code,
        )