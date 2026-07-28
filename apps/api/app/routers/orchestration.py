from typing import Annotated
from uuid import uuid4

import asyncpg

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)

from app.models.lead import (
    LeadIntakeRequest,
)

from app.repositories.leads import (
    DuplicateIdentityConflict,
    persist_received_lead,
)

from app.repositories.qualification import (
    get_existing_qualification,
    persist_qualification_failure,
    persist_qualification_result,
)

from app.security.orchestrator_auth import (
    require_orchestrator_token,
)

from app.services.ai_pipeline import (
    run_ai_assessment,
)

from app.services.action_pipeline import (
    run_post_qualification_actions,
)

from app.services.crm_pipeline import (
    run_crm_sync,
)

from app.services.normalization import (
    normalize_lead,
)

from app.services.orchestration_context import (
    load_orchestration_context,
)

from app.services.qualification import (
    qualify_lead,
)

from app.services.routing import (
    route_lead,
)
from app.services.workflow_failure import (
    WorkflowStageError,
    classify_retryable_code,
    record_workflow_failure,
)


router = APIRouter(
    prefix="/api/v1/orchestration",
    tags=["Orchestration"],
    dependencies=[
        Depends(
            require_orchestrator_token
        )
    ],
)


ACTIONABLE_STATUSES = {
    "QUALIFIED_HOT",
    "QUALIFIED_WARM",
    "COLD",
}


def generate_identifier(
    prefix: str,
) -> str:

    return (
        f"{prefix}_{uuid4().hex}"
    )


# =========================================================
# 1. INTAKE / NORMALIZATION / DEDUPE / PERSISTENCE
# =========================================================

@router.post(
    "/intake",
    status_code=(
        status.HTTP_202_ACCEPTED
    ),
)
async def orchestration_intake(
    lead: LeadIntakeRequest,
    request: Request,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key"
        ),
    ] = None,
):

    intake_id = (
        generate_identifier("lf")
    )

    correlation_id = (
        generate_identifier("corr")
    )

    effective_key = (
        idempotency_key
        or generate_identifier(
            "idem"
        )
    )

    normalized_lead = (
        normalize_lead(lead)
    )

    try:

        result = (
            await persist_received_lead(
                request.app.state.db_pool,
                request_lead=lead,
                normalized_lead=(
                    normalized_lead
                ),
                intake_id=intake_id,
                correlation_id=(
                    correlation_id
                ),
                idempotency_key=(
                    effective_key
                ),
            )
        )

    except DuplicateIdentityConflict as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail={
                "code": (
                    "IDENTITY_CONFLICT"
                ),
                "correlation_id": (
                    correlation_id
                ),
                "message": (
                    "Email and phone match "
                    "different existing leads."
                ),
            },
        ) from exc

    return {
        "success": True,

        "stage": "INTAKE",

        "lead_id":
            result["lead_id"],

        "intake_id":
            result["intake_id"],

        "correlation_id":
            result[
                "correlation_id"
            ],

        "status":
            result["status"],

        "duplicate":
            result["duplicate"],

        "replayed":
            result["replayed"],

        "duplicate_match_fields":
            result[
                "duplicate_match_fields"
            ],

        "continue_processing": (
            not result["duplicate"]
        ),
    }


# =========================================================
# 2. DETERMINISTIC QUALIFICATION + AI
# =========================================================

@router.post(
    "/leads/{lead_id}/qualify",
)
async def orchestration_qualify(
    lead_id: str,
    request: Request,
):

    pool = (
        request.app.state.db_pool
    )

    try:

        async with (
            pool.acquire()
            as connection
        ):

            context = (
                await load_orchestration_context(
                    connection,
                    lead_id=lead_id,
                )
            )

            qualification_record = (
                context.qualification
            )

            if (
                qualification_record
                is None
            ):

                try:

                    qualification = (
                        await qualify_lead(
                            connection,
                            context.lead,
                        )
                    )

                    async with (
                        connection.transaction()
                    ):

                        await (
                            persist_qualification_result(
                                connection,
                                lead_id=(
                                    lead_id
                                ),
                                correlation_id=(
                                    context
                                    .correlation_id
                                ),
                                result=(
                                    qualification
                                ),
                            )
                        )

                    qualification_record = (
                        await get_existing_qualification(
                            connection,
                            lead_id,
                        )
                    )

                except Exception as exc:

                    async with (
                        connection.transaction()
                    ):

                        await (
                            persist_qualification_failure(
                                connection,
                                lead_id=lead_id,
                                correlation_id=(
                                    context
                                    .correlation_id
                                ),
                                error_code=(
                                    "QUALIFICATION_PROCESSING_ERROR"
                                ),
                                error_message=(
                                    str(exc)
                                ),
                            )
                        )

                    return {
                        "success": True,
                        "stage": (
                            "QUALIFICATION"
                        ),

                        "lead_id":
                            lead_id,

                        "correlation_id": (
                            context
                            .correlation_id
                        ),

                        "status": (
                            "REVIEW_REQUIRED"
                        ),

                        "score": None,

                        "continue_processing":
                            False,

                        "review_required":
                            True,

                        "error_code": (
                            "QUALIFICATION_PROCESSING_ERROR"
                        ),
                    }

            if (
                qualification_record
                is None
            ):
                raise RuntimeError(
                    "Qualification result "
                    "was not persisted."
                )

            final_status = (
                qualification_record[
                    "final_status"
                ]
            )

            # AI remains advisory.
            # Deterministic rules were already
            # persisted before AI runs.
            final_status = (
                await run_ai_assessment(
                    pool,
                    lead_id=lead_id,
                    correlation_id=(
                        context
                        .correlation_id
                    ),
                    lead=context.lead,
                    qualification=(
                        qualification_record
                    ),
                )
            )

            breakdown = (
                qualification_record
                .get(
                    "score_breakdown"
                )
                or {}
            )

            service_zone = (
                breakdown
                .get(
                    "service_area",
                    {},
                )
                .get("zone")
            )

            return {
                "success": True,
                "stage": (
                    "QUALIFICATION"
                ),

                "lead_id":
                    lead_id,

                "correlation_id": (
                    context
                    .correlation_id
                ),

                "status":
                    final_status,

                "score": (
                    qualification_record[
                        "score"
                    ]
                ),

                "service_zone":
                    service_zone,

                "review_required": (
                    final_status
                    == "REVIEW_REQUIRED"
                ),

                "continue_processing": (
                    final_status
                    in ACTIONABLE_STATUSES
                ),
            }

    except LookupError as exc:

        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "LEAD_NOT_FOUND",
            },
        ) from exc

    except (
        asyncpg.PostgresError,
        OSError,
    ) as exc:

        raise HTTPException(
            status_code=503,
            detail={
                "code": (
                    "QUALIFICATION_DATABASE_UNAVAILABLE"
                ),
                "message": str(exc),
            },
        ) from exc


# =========================================================
# 3. ROUTING
# =========================================================

@router.post(
    "/leads/{lead_id}/route",
)
async def orchestration_route(
    lead_id: str,
    request: Request,
):

    pool = (
        request.app.state.db_pool
    )

    async with (
        pool.acquire()
        as connection
    ):

        try:

            context = (
                await load_orchestration_context(
                    connection,
                    lead_id=lead_id,
                )
            )

        except LookupError as exc:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "LEAD_NOT_FOUND",
                },
            ) from exc

        if (
            context.status
            not in ACTIONABLE_STATUSES
        ):
            return {
                "success": True,
                "stage": "ROUTING",

                "lead_id":
                    lead_id,

                "status":
                    context.status,

                "skipped": True,

                "reason": (
                    "Lead status does not "
                    "require routing."
                ),
            }

        if (
            context.qualification
            is None
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": (
                        "QUALIFICATION_REQUIRED"
                    ),
                },
            )

        breakdown = (
            context.qualification
            .get(
                "score_breakdown"
            )
            or {}
        )

        service_zone = (
            breakdown
            .get(
                "service_area",
                {},
            )
            .get("zone")
        )

        async with (
            connection.transaction()
        ):

            routing_result = (
                await route_lead(
                    connection,
                    lead_id=lead_id,
                    correlation_id=(
                        context
                        .correlation_id
                    ),
                    service_type=(
                        context
                        .lead
                        .service_type
                        .value
                    ),
                    service_zone=(
                        service_zone
                    ),
                )
            )

    return {
        "success": True,
        "stage": "ROUTING",

        "lead_id":
            lead_id,

        "status":
            context.status,

        "owner_id":
            routing_result.owner_id,

        "queue":
            routing_result.queue,

        "routing_rule_id": (
            str(
                routing_result
                .routing_rule_id
            )
            if (
                routing_result
                .routing_rule_id
            )
            else None
        ),

        "fallback":
            routing_result.fallback,

        "skipped": False,
    }


# =========================================================
# 4. CRM
# =========================================================

@router.post(
    "/leads/{lead_id}/crm",
)
async def orchestration_crm(
    lead_id: str,
    request: Request,
):

    pool = (
        request.app.state.db_pool
    )

    async with (
        pool.acquire()
        as connection
    ):

        try:

            context = (
                await load_orchestration_context(
                    connection,
                    lead_id=lead_id,
                )
            )

        except LookupError as exc:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "LEAD_NOT_FOUND",
                },
            ) from exc

    if (
        context.status
        not in ACTIONABLE_STATUSES
    ):
        return {
            "success": True,
            "stage": "CRM",

            "lead_id":
                lead_id,

            "skipped": True,

            "reason": (
                "Lead status does not "
                "require CRM synchronization."
            ),
        }

    if (
        context.qualification
        is None
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "QUALIFICATION_REQUIRED",
            },
        )

    await run_crm_sync(
        pool,
        lead_id=lead_id,
        correlation_id=(
            context.correlation_id
        ),
        lead=context.lead,
        qualification=(
            context.qualification
        ),
        final_status=(
            context.status
        ),
        owner_id=(
            context
            .assigned_owner_id
        ),
        force=False,
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
                    hubspot_contact_id,
                    hubspot_deal_id,
                    last_error_code
                from public.leads
                where id = $1::uuid;
                """,
                lead_id,
            )
        )

    crm_status = (
        crm_state[
            "crm_sync_status"
        ]
        if crm_state
        else None
    )

    if (
        crm_status
        != "SUCCEEDED"
    ):
        error_code = (
            crm_state["last_error_code"]
            if crm_state
            else None
        ) or "CRM_SYNC_FAILED"

        failure = WorkflowStageError(
            code=error_code,
            message=(
                "CRM synchronization did not "
                f"succeed. State={crm_status}."
            ),
            retryable=(
                classify_retryable_code(
                    error_code
                )
            ),
            provider="hubspot",
        )

        await record_workflow_failure(
            pool,
            lead_id=lead_id,
            correlation_id=(
                context.correlation_id
            ),
            failed_action=(
                "lead_continuation"
            ),
            exc=failure,
            trigger="N8N_CRM_STAGE",
        )

        raise HTTPException(
            status_code=502,
            detail={
                "code": error_code,
                "lead_id": lead_id,
                "crm_sync_status":
                    crm_status,
            },
        )

    return {
        "success": True,
        "stage": "CRM",

        "lead_id":
            lead_id,

        "crm_sync_status":
            crm_status,

        "hubspot_contact_id": (
            crm_state[
                "hubspot_contact_id"
            ]
        ),

        "hubspot_deal_id": (
            crm_state[
                "hubspot_deal_id"
            ]
        ),

        "skipped": False,
    }


# =========================================================
# 5. CUSTOMER / STAFF ACTIONS
# =========================================================

@router.post(
    "/leads/{lead_id}/actions",
)
async def orchestration_actions(
    lead_id: str,
    request: Request,
):

    pool = (
        request.app.state.db_pool
    )

    async with (
        pool.acquire()
        as connection
    ):

        try:

            context = (
                await load_orchestration_context(
                    connection,
                    lead_id=lead_id,
                )
            )

        except LookupError as exc:

            raise HTTPException(
                status_code=404,
                detail={
                    "code":
                        "LEAD_NOT_FOUND",
                },
            ) from exc

    if (
        context.status
        not in ACTIONABLE_STATUSES
    ):
        return {
            "success": True,
            "stage": "ACTIONS",

            "lead_id":
                lead_id,

            "skipped": True,

            "reason": (
                "Lead status does not "
                "require automated actions."
            ),
        }

    if (
        context.qualification
        is None
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "QUALIFICATION_REQUIRED",
            },
        )

    effective_score = (
        context.score
        if context.score is not None
        else context.qualification[
            "score"
        ]
    )

    try:
        await (
            run_post_qualification_actions(
                pool,
                lead_id=lead_id,
                correlation_id=(
                    context.correlation_id
                ),
                lead=context.lead,
                score=effective_score,
                final_status=(
                    context.status
                ),
                owner_id=(
                    context
                    .assigned_owner_id
                ),
            )
        )
    except Exception as exc:
        await record_workflow_failure(
            pool,
            lead_id=lead_id,
            correlation_id=(
                context.correlation_id
            ),
            failed_action=(
                "lead_continuation"
            ),
            exc=exc,
            trigger="N8N_ACTIONS_STAGE",
        )
        raise

    return {
        "success": True,
        "stage": "ACTIONS",

        "lead_id":
            lead_id,

        "status":
            context.status,

        "score":
            effective_score,

        "owner_id": (
            context
            .assigned_owner_id
        ),

        "completed": True,
        "skipped": False,
    }
