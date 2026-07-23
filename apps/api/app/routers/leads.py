from typing import Annotated
from uuid import uuid4

import asyncpg
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
    status,
)

from app.models.lead import (
    LeadIntakeRequest,
    LeadIntakeResponse,
    NormalizedLead,
)
from app.repositories.leads import (
    DuplicateIdentityConflict,
    persist_received_lead,
)
from app.services.normalization import normalize_lead


router = APIRouter(
    prefix="/api/v1/leads",
    tags=["Leads"],
)


def generate_identifier(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@router.post(
    "/intake",
    response_model=LeadIntakeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def intake_lead(
    lead: LeadIntakeRequest,
    request: Request,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key"),
    ] = None,
) -> LeadIntakeResponse:

    intake_id = generate_identifier("lf")
    correlation_id = generate_identifier("corr")

    effective_idempotency_key = (
        idempotency_key
        or generate_identifier("idem")
    )

    normalized_lead = normalize_lead(lead)

    try:
        result = await persist_received_lead(
            request.app.state.db_pool,
            request_lead=lead,
            normalized_lead=normalized_lead,
            intake_id=intake_id,
            correlation_id=correlation_id,
            idempotency_key=effective_idempotency_key,
        )



    except DuplicateIdentityConflict as exc:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IDENTITY_CONFLICT",
                "correlation_id": correlation_id,
                "message": (
                    "Email and phone match different existing "
                    "leads. Human review is required."
                ),
            },
        ) from exc

    

    except (
        asyncpg.PostgresError,
        OSError,
    ) as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "correlation_id": correlation_id,
                "message": (
                    "Lead intake could not be durably stored. "
                    "Please retry."
                ),
            },
        ) from exc

    persisted_normalized_lead = NormalizedLead.model_validate(
        result["normalized_payload"]
    )

    if result["replayed"]:
        response_message = "Existing intake returned."

    elif result["duplicate"]:
        response_message = (
            "Duplicate lead detected and linked "
            "to existing canonical lead."
        )

    else:
        response_message = (
            "Lead received and durably stored."
        )

    return LeadIntakeResponse(
        success=True,
        intake_id=result["intake_id"],
        correlation_id=result["correlation_id"],
        status=result["status"],
        normalized_lead=persisted_normalized_lead,
        replayed=result["replayed"],
        duplicate=result["duplicate"],
        duplicate_match_fields=result[
            "duplicate_match_fields"
        ],
        message=response_message,
    )