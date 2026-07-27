import asyncpg


async def upsert_workflow_error(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    failed_action: str,
    provider: str | None,
    error_code: str,
    error_message: str | None,
    retryable: bool,
) -> dict:

    row = await connection.fetchrow(
        """
        insert into public.workflow_errors (
            lead_id,
            correlation_id,
            failed_action,
            provider,
            error_code,
            error_message,
            retryable,
            status
        )
        values (
            $1::uuid,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            'OPEN'
        )
        on conflict (
            lead_id,
            failed_action
        )
        do update set
            correlation_id =
                excluded.correlation_id,
            provider =
                excluded.provider,
            error_code =
                excluded.error_code,
            error_message =
                excluded.error_message,
            retryable =
                excluded.retryable,
            status = 'OPEN',
            next_retry_at = null,
            resolution_notes = null,
            resolved_at = null,
            updated_at = now()
        returning *;
        """,
        lead_id,
        correlation_id,
        failed_action,
        provider,
        error_code,
        error_message,
        retryable,
    )

    await connection.execute(
        """
        update public.leads
        set
            last_error_code = $2,
            updated_at = now()
        where id = $1::uuid;
        """,
        lead_id,
        error_code,
    )

    return dict(row)


async def get_workflow_error(
    connection: asyncpg.Connection,
    error_id,
) -> dict | None:

    row = await connection.fetchrow(
        """
        select *
        from public.workflow_errors
        where id = $1::uuid;
        """,
        error_id,
    )

    return (
        dict(row)
        if row
        else None
    )


async def mark_workflow_retry_started(
    connection: asyncpg.Connection,
    *,
    error_id,
    actor_id: str,
    reason: str,
) -> dict:

    row = await connection.fetchrow(
        """
        update public.workflow_errors
        set
            status = 'RETRYING',
            retry_count =
                retry_count + 1,
            last_retry_actor_id =
                $2::uuid,
            last_retry_reason = $3,
            updated_at = now()
        where id = $1::uuid
        returning *;
        """,
        error_id,
        actor_id,
        reason,
    )

    if row is None:
        raise RuntimeError(
            "Workflow error does not exist."
        )

    return dict(row)


async def resolve_workflow_error_for_action(
    connection: asyncpg.Connection,
    *,
    lead_id,
    failed_action: str,
    resolution_notes: str,
) -> None:

    row = await connection.fetchrow(
        """
        update public.workflow_errors
        set
            status = 'RESOLVED',
            resolution_notes = $3,
            resolved_at = now(),
            next_retry_at = null,
            updated_at = now()
        where lead_id = $1::uuid
        and failed_action = $2
        and status != 'RESOLVED'
        returning
            lead_id,
            error_code;
        """,
        lead_id,
        failed_action,
        resolution_notes,
    )

    if row is None:
        return

    await connection.execute(
        """
        update public.leads
        set
            last_error_code = null,
            updated_at = now()
        where id = $1::uuid
        and last_error_code = $2;
        """,
        row["lead_id"],
        row["error_code"],
    )