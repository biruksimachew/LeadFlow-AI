import json

import asyncpg


async def get_existing_assignment(
    connection: asyncpg.Connection,
    lead_id,
) -> dict | None:

    row = await connection.fetchrow(
        """
        select
            assigned_owner_id,
            assigned_queue,
            routing_rule_id,
            routed_at
        from public.leads
        where id = $1;
        """,
        lead_id,
    )

    if (
        row is None
        or row["assigned_owner_id"] is None
    ):
        return None

    return dict(row)


async def load_routing_rules(
    connection: asyncpg.Connection,
) -> list[dict]:

    rows = await connection.fetch(
        """
        select *
        from public.routing_rules
        where active = true
        and available = true
        order by priority desc;
        """
    )

    return [dict(row) for row in rows]


async def load_fallback(
    connection: asyncpg.Connection,
) -> dict:

    row = await connection.fetchrow(
        """
        select *
        from public.routing_config
        where config_key = 'default';
        """
    )

    if row is None:
        raise RuntimeError(
            "Default routing configuration missing."
        )

    return dict(row)


async def persist_assignment(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    owner_id: str,
    queue: str | None,
    routing_rule_id,
    fallback: bool,
) -> None:

    await connection.execute(
        """
        update public.leads
        set
            assigned_owner_id = $2,
            assigned_queue = $3,
            routing_rule_id = $4,
            routed_at = now()
        where id = $1;
        """,
        lead_id,
        owner_id,
        queue,
        routing_rule_id,
    )

    details = json.dumps({
        "owner_id": owner_id,
        "queue": queue,
        "routing_rule_id": (
            str(routing_rule_id)
            if routing_rule_id
            else None
        ),
        "fallback": fallback,
    })

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            result,
            details
        )
        values (
            $1,
            $2,
            'OWNER_ASSIGNED',
            'system',
            'succeeded',
            $3::jsonb
        );
        """,
        lead_id,
        correlation_id,
        details,
    )