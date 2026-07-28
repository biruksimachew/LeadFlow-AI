import asyncio
import os
import sys

import asyncpg


async def main() -> int:
    database_url = os.getenv("DATABASE_URL")

    email = os.getenv(
        "DEMO_OPERATOR_EMAIL",
        "operator@northstar.local",
    ).strip()

    expected_role = os.getenv(
        "DEMO_OPERATOR_ROLE",
        "ADMIN",
    ).strip().upper()

    if not database_url:
        print("ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    connection = await asyncpg.connect(database_url)

    try:
        row = await connection.fetchrow(
            """
            select
                u.id,
                u.email,
                p.display_name,
                p.role,
                p.is_active
            from auth.users u
            join public.operator_profiles p
              on p.user_id = u.id
            where lower(u.email) = lower($1)
            limit 1;
            """,
            email,
        )
    finally:
        await connection.close()

    if row is None:
        print(
            "Demo operator check FAILED: auth user/profile not found."
        )
        return 1

    if not row["is_active"]:
        print(
            "Demo operator check FAILED: operator profile is inactive."
        )
        return 1

    if row["role"] != expected_role:
        print(
            "Demo operator check FAILED: "
            f"expected role {expected_role}, found {row['role']}."
        )
        return 1

    print("Demo operator check PASSED.")
    print(f" - email: {row['email']}")
    print(f" - role: {row['role']}")
    print(" - active: true")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
