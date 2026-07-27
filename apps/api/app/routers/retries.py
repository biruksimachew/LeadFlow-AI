import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from pydantic import BaseModel, Field

from app.repositories.workflow_errors import (
    get_workflow_error,
    mark_workflow_retry_started,
)
from app.security.operator_auth import (
    OperatorIdentity,
    require_admin_operator,
)
from app.services.continuation import (
    run_lead_continuation,
)


router = APIRouter(
    prefix="/api/v1/workflow-errors",
    tags=["workflow-errors"],
)


class WorkflowRetryRequest(BaseModel):
    reason: str = Field(
        min_length=10,
        max_length=1000,
    )


@router.post(
    "/{error_id}/retry",
)
async def retry_workflow_error(
    error_id: str,
    payload: WorkflowRetryRequest,
    request: Request,
    operator: OperatorIdentity = Depends(
        require_admin_operator
    ),
):
    pool = request.app.state.db_pool

    async with pool.acquire() as connection:

        workflow_error = (
            await get_workflow_error(
                connection,
                error_id,
            )
        )

    if workflow_error is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": (
                    "WORKFLOW_ERROR_NOT_FOUND"
                ),
            },
        )

    if (
        workflow_error["status"]
        == "RESOLVED"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail={
                "code": (
                    "WORKFLOW_ERROR_RESOLVED"
                ),
                "message": (
                    "This workflow error has "
                    "already been resolved."
                ),
            },
        )

    if (
        workflow_error["failed_action"]
        != "lead_continuation"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail={
                "code": (
                    "UNSUPPORTED_RETRY_ACTION"
                ),
            },
        )

    reason = payload.reason.strip()

    async with pool.acquire() as connection:

        async with connection.transaction():

            retry_state = (
                await mark_workflow_retry_started(
                    connection,
                    error_id=error_id,
                    actor_id=(
                        operator.user_id
                    ),
                    reason=reason,
                )
            )

            await connection.execute(
                """
                insert into public.workflow_events (
                    lead_id,
                    correlation_id,
                    event_type,
                    actor_type,
                    actor_id,
                    result,
                    details
                )
                values (
                    $1::uuid,
                    $2,
                    'WORKFLOW_RETRY_REQUESTED',
                    'operator',
                    $3,
                    'succeeded',
                    $4::jsonb
                );
                """,
                workflow_error[
                    "lead_id"
                ],
                workflow_error[
                    "correlation_id"
                ],
                operator.user_id,
                json.dumps({
                    "workflow_error_id": (
                        error_id
                    ),
                    "retry_count": (
                        retry_state[
                            "retry_count"
                        ]
                    ),
                    "reason": reason,
                    "actor_role": (
                        operator.role
                    ),
                }),
            )

    continuation = (
        await run_lead_continuation(
            pool,
            lead_id=str(
                workflow_error[
                    "lead_id"
                ]
            ),
            trigger="MANUAL_RETRY",
            initiated_by=(
                operator.user_id
            ),
            force_crm_sync=False,
        )
    )

    event_type = (
        "WORKFLOW_RETRY_SUCCEEDED"
        if continuation.status
        == "SUCCEEDED"
        else "WORKFLOW_RETRY_FAILED"
    )

    event_result = (
        "succeeded"
        if continuation.status
        == "SUCCEEDED"
        else "failed"
    )

    async with pool.acquire() as connection:

        await connection.execute(
            """
            insert into public.workflow_events (
                lead_id,
                correlation_id,
                event_type,
                actor_type,
                actor_id,
                result,
                details,
                error_code
            )
            values (
                $1::uuid,
                $2,
                $3,
                'operator',
                $4,
                $5,
                $6::jsonb,
                $7
            );
            """,
            workflow_error["lead_id"],
            workflow_error[
                "correlation_id"
            ],
            event_type,
            operator.user_id,
            event_result,
            json.dumps({
                "workflow_error_id": (
                    error_id
                ),
                "retry_count": (
                    retry_state[
                        "retry_count"
                    ]
                ),
                "reason": reason,
            }),
            continuation.error_code,
        )

    return {
        "success": (
            continuation.status
            == "SUCCEEDED"
        ),
        "workflow_error_id": error_id,
        "lead_id": str(
            workflow_error["lead_id"]
        ),
        "retry_count": (
            retry_state["retry_count"]
        ),
        "retry_status": (
            continuation.status
        ),
        "error_code": (
            continuation.error_code
        ),
    }