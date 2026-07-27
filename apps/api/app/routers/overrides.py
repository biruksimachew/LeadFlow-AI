import json
import logging
from typing import Literal

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

from app.security.operator_auth import (
    OperatorIdentity,
    require_management_operator,
)
from app.services.continuation import (
    run_lead_continuation,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/leads",
    tags=["lead-overrides"],
)


OverrideStatus = Literal[
    "QUALIFIED_HOT",
    "QUALIFIED_WARM",
    "COLD",
    "DISQUALIFIED",
    "REVIEW_REQUIRED",
]


class LeadOverrideRequest(BaseModel):
    status: OverrideStatus | None = None

    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    owner_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    reason: str = Field(
        min_length=10,
        max_length=1000,
    )

    @model_validator(
        mode="after",
    )
    def validate_change(
        self,
    ) -> "LeadOverrideRequest":
        if (
            self.status is None
            and self.score is None
            and self.owner_id is None
        ):
            raise ValueError(
                "At least one override "
                "field is required."
            )

        return self


@router.post(
    "/{lead_id}/override",
)
async def override_lead(
    lead_id: str,
    payload: LeadOverrideRequest,
    request: Request,
    operator: OperatorIdentity = Depends(
        require_management_operator
    ),
):
    previous_values: dict[
        str,
        object,
    ] = {}

    new_values: dict[
        str,
        object,
    ] = {}

    override_id = None

    try:
        async with (
            request.app.state.db_pool.acquire()
            as connection
        ):
            async with connection.transaction():

                lead = await connection.fetchrow(
                    """
                    select
                        id,
                        correlation_id,
                        status,
                        score,
                        assigned_owner_id
                    from public.leads
                    where id = $1::uuid
                    for update;
                    """,
                    lead_id,
                )

                if lead is None:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "code": (
                                "LEAD_NOT_FOUND"
                            ),
                        },
                    )

                if (
                    payload.status
                    is not None
                    and payload.status
                    != lead["status"]
                ):
                    previous_values[
                        "status"
                    ] = lead["status"]

                    new_values[
                        "status"
                    ] = payload.status

                if (
                    payload.score
                    is not None
                    and payload.score
                    != lead["score"]
                ):
                    previous_values[
                        "score"
                    ] = lead["score"]

                    new_values[
                        "score"
                    ] = payload.score

                if (
                    payload.owner_id
                    is not None
                    and payload.owner_id
                    != lead[
                        "assigned_owner_id"
                    ]
                ):
                    previous_values[
                        "assigned_owner_id"
                    ] = lead[
                        "assigned_owner_id"
                    ]

                    new_values[
                        "assigned_owner_id"
                    ] = payload.owner_id

                if not new_values:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_409_CONFLICT
                        ),
                        detail={
                            "code": (
                                "NO_OVERRIDE_CHANGE"
                            ),
                            "message": (
                                "Requested values "
                                "already match "
                                "the lead."
                            ),
                        },
                    )

                new_status = (
                    payload.status
                    if payload.status
                    is not None
                    else lead["status"]
                )

                new_score = (
                    payload.score
                    if payload.score
                    is not None
                    else lead["score"]
                )

                new_owner = (
                    payload.owner_id
                    if payload.owner_id
                    is not None
                    else lead[
                        "assigned_owner_id"
                    ]
                )

                await connection.execute(
                    """
                    update public.leads
                    set
                        status = $2,
                        score = $3,
                        assigned_owner_id = $4,
                        updated_at = now()
                    where id = $1::uuid;
                    """,
                    lead_id,
                    new_status,
                    new_score,
                    new_owner,
                )

                override_id = (
                    await connection.fetchval(
                        """
                        insert into
                            public.lead_overrides (
                                lead_id,
                                actor_user_id,
                                actor_email,
                                actor_role,
                                previous_values,
                                new_values,
                                reason
                            )
                        values (
                            $1::uuid,
                            $2::uuid,
                            $3,
                            $4,
                            $5::jsonb,
                            $6::jsonb,
                            $7
                        )
                        returning id;
                        """,
                        lead_id,
                        operator.user_id,
                        operator.email,
                        operator.role,
                        json.dumps(
                            previous_values
                        ),
                        json.dumps(
                            new_values
                        ),
                        payload.reason.strip(),
                    )
                )

                await connection.execute(
                    """
                    insert into
                        public.workflow_events (
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
                        'HUMAN_OVERRIDE',
                        'operator',
                        $3,
                        null,
                        'succeeded',
                        $4::jsonb,
                        null,
                        null
                    );
                    """,
                    lead_id,
                    lead["correlation_id"],
                    operator.user_id,
                    json.dumps(
                        {
                            "override_id": str(
                                override_id
                            ),
                            "previous_values": (
                                previous_values
                            ),
                            "new_values": (
                                new_values
                            ),
                            "reason": (
                                payload.reason
                                .strip()
                            ),
                            "actor_role": (
                                operator.role
                            ),
                        }
                    ),
                )

    except asyncpg.PostgresError as exc:
        logger.exception(
            "Lead override database failure. "
            "lead_id=%s operator=%s role=%s",
            lead_id,
            operator.user_id,
            operator.role,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "OVERRIDE_DATABASE_ERROR"
                ),
                "message": (
                    "Unable to persist "
                    "lead override."
                ),
            },
        ) from exc

    # ========================================================
    # Human decision is already committed here.
    #
    # External systems are intentionally resumed AFTER the
    # override transaction. A HubSpot/email/Slack failure must
    # never roll back a legitimate human decision.
    # ========================================================

    continuation = await run_lead_continuation(
        request.app.state.db_pool,
        lead_id=lead_id,
        trigger="HUMAN_OVERRIDE",
        initiated_by=operator.user_id,
        force_crm_sync=True,
    )

    return {
        "success": True,
        "lead_id": lead_id,
        "override_id": str(
            override_id
        ),
        "previous_values": (
            previous_values
        ),
        "new_values": (
            new_values
        ),
        "actor_role": operator.role,
        "continuation": (
            continuation.to_dict()
        ),
    }