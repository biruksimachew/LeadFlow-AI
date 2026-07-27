from dataclasses import dataclass
import os

import asyncpg
import httpx
from fastapi import Header, HTTPException, status
from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)

@dataclass(frozen=True)
class OperatorIdentity:
    user_id: str
    email: str | None
    role: str


MANAGEMENT_ROLES = {
    "ADMIN",
    "OPERATIONS_MANAGER",
}


async def require_management_operator(
    authorization: str | None = Header(
        default=None,
    ),
) -> OperatorIdentity:
    if (
        not authorization
        or not authorization.startswith(
            "Bearer "
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_REQUIRED",
                "message": (
                    "A valid operator session "
                    "is required."
                ),
            },
        )

    token = authorization.removeprefix(
        "Bearer "
    ).strip()

    supabase_url = os.environ[
        "SUPABASE_AUTH_URL"
    ].rstrip("/")

    publishable_key = os.environ[
        "SUPABASE_PUBLISHABLE_KEY"
    ]

    try:
        async with httpx.AsyncClient(
            timeout=10.0,
        ) as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "apikey": (
                        publishable_key
                    ),
                    "Authorization": (
                        f"Bearer {token}"
                    ),
                },
            )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": (
                    "AUTH_PROVIDER_UNAVAILABLE"
                ),
                "message": (
                    "Unable to validate "
                    "operator session."
                ),
            },
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_SESSION",
                "message": (
                    "Operator session is "
                    "invalid or expired."
                ),
            },
        )

    user = response.json()

    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_SESSION",
            },
        )

    connection = await asyncpg.connect(
        os.environ["DATABASE_URL"]
    )

    try:
        operator = await connection.fetchrow(
            """
            select
                role,
                is_active
            from public.operator_profiles
            where user_id = $1::uuid;
            """,
            user_id,
        )
    finally:
        await connection.close()

    if (
        operator is None
        or not operator["is_active"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": (
                    "OPERATOR_ACCESS_REQUIRED"
                ),
            },
        )

    role = operator["role"]

    if role not in MANAGEMENT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": (
                    "MANAGEMENT_PERMISSION_REQUIRED"
                ),
                "message": (
                    "This operation requires "
                    "management permission."
                ),
            },
        )





    return OperatorIdentity(
        user_id=user_id,
        email=user.get("email"),
        role=role,
    )

async def require_admin_operator(
    operator: OperatorIdentity = Depends(
        require_management_operator
    ),
) -> OperatorIdentity:

    if operator.role != "ADMIN":
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail={
                "code": (
                    "ADMIN_PERMISSION_REQUIRED"
                ),
                "message": (
                    "Workflow retries require "
                    "Administrator permission."
                ),
            },
        )

    return operator