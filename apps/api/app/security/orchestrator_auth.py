import hmac
import os
from typing import Annotated

from fastapi import (
    Header,
    HTTPException,
    status,
)


async def require_orchestrator_token(
    token: Annotated[
        str | None,
        Header(
            alias="X-LeadFlow-Orchestrator-Token",
        ),
    ] = None,
) -> None:

    expected = os.getenv(
        "N8N_INTERNAL_API_TOKEN"
    )

    if not expected:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": (
                    "ORCHESTRATOR_AUTH_NOT_CONFIGURED"
                ),
                "message": (
                    "Internal orchestration "
                    "authentication is not configured."
                ),
            },
        )

    if (
        not token
        or not hmac.compare_digest(
            token,
            expected,
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail={
                "code": (
                    "INVALID_ORCHESTRATOR_TOKEN"
                ),
            },
        )