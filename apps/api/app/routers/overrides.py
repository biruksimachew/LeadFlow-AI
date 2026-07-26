import json
import os
from typing import Literal

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
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
import logging
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
    operator: OperatorIdentity = Depends(
        require_management_operator
    ),
):
    connection = await asyncpg.connect(
        os.environ["DATABASE_URL"]
    )

    try:
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

            previous_values: dict[
                str,
                object,
            ] = {}

            new_values: dict[
                str,
                object,
            ] = {}

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
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": (
                            "NO_OVERRIDE_CHANGE"
                        ),
                        "message": (
                            "Requested values "
                            "already match the lead."
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
                            payload.reason.strip()
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
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "OVERRIDE_DATABASE_ERROR",
                "message": (
                    "Unable to persist lead override."
                ),
            },
        ) from exc

    finally:
        await connection.close()

    return {
        "success": True,
        "lead_id": lead_id,
        "override_id": str(
            override_id
        ),
        "previous_values": (
            previous_values
        ),
        "new_values": new_values,
        "actor_role": operator.role,
    }