import asyncio
import os
import sys

import asyncpg
import httpx

 

ALLOWED_ROLES = {
    "ADMIN",
    "OPERATIONS_MANAGER",
    "OPERATOR",
    "REVIEWER",
}


def normalize_auth_base_url(url: str) -> str:
    base_url = (
        url.rstrip("/")
        .replace(
            "http://127.0.0.1:",
            "http://host.docker.internal:",
        )
        .replace(
            "http://localhost:",
            "http://host.docker.internal:",
        )
    )

    if not base_url.endswith("/auth/v1"):
        base_url = f"{base_url}/auth/v1"

    return base_url

def extract_user_id(body: dict) -> str | None:
    direct_id = body.get("id")
    if isinstance(direct_id, str):
        return direct_id

    user = body.get("user")
    if isinstance(user, dict):
        user_id = user.get("id")
        if isinstance(user_id, str):
            return user_id

    return None


async def find_user(
    client: httpx.AsyncClient,
    *,
    auth_base_url: str,
    headers: dict[str, str],
    email: str,
) -> dict | None:
    response = await client.get(
        f"{auth_base_url}/admin/users",
        headers=headers,
        params={"page": 1, "per_page": 1000},
    )
    response.raise_for_status()

    body = response.json()
    users = body.get("users", []) if isinstance(body, dict) else []

    target = email.casefold()

    for user in users:
        if not isinstance(user, dict):
            continue

        candidate = user.get("email")
        if (
            isinstance(candidate, str)
            and candidate.casefold() == target
        ):
            return user

    return None


async def create_user(
    client: httpx.AsyncClient,
    *,
    auth_base_url: str,
    headers: dict[str, str],
    email: str,
    password: str,
    display_name: str,
) -> str:
    response = await client.post(
        f"{auth_base_url}/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "display_name": display_name,
                "leadflow_demo_user": True,
            },
        },
    )
    response.raise_for_status()

    body = response.json()

    if not isinstance(body, dict):
        raise RuntimeError(
            "Supabase Auth returned an unexpected create-user response."
        )

    user_id = extract_user_id(body)

    if not user_id:
        raise RuntimeError(
            "Supabase Auth did not return the created user ID."
        )

    return user_id



async def sync_user_credentials(
    client: httpx.AsyncClient,
    *,
    auth_base_url: str,
    admin_headers: dict[str, str],
    user_id: str,
    email: str,
    password: str,
    display_name: str,
) -> None:
    response = await client.put(
        f"{auth_base_url}/admin/users/{user_id}",
        headers=admin_headers,
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "display_name": display_name,
                "leadflow_demo_user": True,
            },
        },
    )

    response.raise_for_status()



async def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    auth_base_url = os.getenv("SUPABASE_AUTH_URL")

    service_key = (
        os.getenv("SUPABASE_SERVER_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )

    email = os.getenv(
        "DEMO_OPERATOR_EMAIL",
        "operator@northstar.local",
    ).strip()

    password = os.getenv("DEMO_OPERATOR_PASSWORD", "")

    display_name = os.getenv(
        "DEMO_OPERATOR_DISPLAY_NAME",
        "NorthStar Demo Administrator",
    ).strip()

    role = os.getenv(
        "DEMO_OPERATOR_ROLE",
        "ADMIN",
    ).strip().upper()

    if not database_url:
        print("ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    if not auth_base_url:
        print(
            "ERROR: SUPABASE_AUTH_URL is not configured.",
            file=sys.stderr,
        )
        return 2
    
    if not service_key:
        print(
            "ERROR: SUPABASE_SERVER_KEY or "
            "SUPABASE_SERVICE_ROLE_KEY is not configured.",
            file=sys.stderr,
        )
        return 2

    if not email:
        print("ERROR: DEMO_OPERATOR_EMAIL is empty.", file=sys.stderr)
        return 2

    if len(password) < 12:
        print(
            "ERROR: DEMO_OPERATOR_PASSWORD must be at least 12 characters.",
            file=sys.stderr,
        )
        return 2

    if role not in ALLOWED_ROLES:
        print(
            "ERROR: DEMO_OPERATOR_ROLE must be one of: "
            + ", ".join(sorted(ALLOWED_ROLES)),
            file=sys.stderr,
        )
        return 2

    auth_base_url = normalize_auth_base_url(
        auth_base_url,
    )

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        existing = await find_user(
            client,
            auth_base_url=auth_base_url,
            headers=headers,
            email=email,
        )

        if existing is not None:
            user_id = existing.get("id")
            if not isinstance(user_id, str):
                raise RuntimeError(
                    "Existing Supabase user has no valid ID."
                )
            created = False
        else:
            user_id = await create_user(
                client,
                auth_base_url=auth_base_url,
                headers=headers,
                email=email,
                password=password,
                display_name=display_name,
            )
            created = True

        await sync_user_credentials(
            client,
            auth_base_url=auth_base_url,
            admin_headers=headers,
            user_id=user_id,
            email=email,
            password=password,
            display_name=display_name,
        )

    connection = await asyncpg.connect(database_url)

    try:
        await connection.execute(
            """
            insert into public.operator_profiles (
                user_id,
                display_name,
                role,
                is_active,
                updated_at
            )
            values (
                $1::uuid,
                $2,
                $3,
                true,
                now()
            )
            on conflict (user_id)
            do update set
                display_name = excluded.display_name,
                role = excluded.role,
                is_active = true,
                updated_at = now();
            """,
            user_id,
            display_name,
            role,
        )
    finally:
        await connection.close()

    print("Demo operator provisioned successfully.")
    print(f" - auth user: {'created' if created else 'existing'}")
    print(f" - email: {email}")
    print(f" - role: {role}")
    print(" - operator profile: active")

    print(" - password synchronized: yes")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
