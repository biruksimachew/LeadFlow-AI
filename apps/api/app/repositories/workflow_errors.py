from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg


def calculate_retry_delay_seconds(
    *,
    retry_count: int,
    base_delay_seconds: int,
    max_delay_seconds: int,
) -> int:
    exponent = max(retry_count, 0)
    delay = base_delay_seconds * (2 ** exponent)

    return min(
        max(delay, 0),
        max(max_delay_seconds, 0),
    )


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
    max_attempts: int,
    base_delay_seconds: int,
    max_delay_seconds: int,
) -> dict[str, Any]:
    existing = await connection.fetchrow(
        """
        select
            status,
            retry_count,
            dead_letter_alerted_at
        from public.workflow_errors
        where lead_id = $1::uuid
          and failed_action = $2
        for update;
        """,
        lead_id,
        failed_action,
    )

    previous_status = (
        existing["status"]
        if existing
        else None
    )
    retry_count = (
        int(existing["retry_count"])
        if existing
        else 0
    )

    exhausted = retry_count >= max_attempts

    if not retryable or exhausted:
        error_status = "DEAD_LETTER"
        retry_delay_seconds = None
    else:
        error_status = "OPEN"
        retry_delay_seconds = (
            calculate_retry_delay_seconds(
                retry_count=retry_count,
                base_delay_seconds=(
                    base_delay_seconds
                ),
                max_delay_seconds=(
                    max_delay_seconds
                ),
            )
        )

    became_dead_letter = (
        error_status == "DEAD_LETTER"
        and previous_status != "DEAD_LETTER"
    )

    row = await connection.fetchrow(
        """
        insert into public.workflow_errors as current_error (
            lead_id,
            correlation_id,
            failed_action,
            provider,
            error_code,
            error_message,
            retryable,
            retry_count,
            status,
            next_retry_at,
            retry_started_at,
            retry_worker_id,
            dead_letter_alerted_at,
            dead_letter_alert_error,
            dead_letter_alert_attempt_count,
            dead_letter_alert_next_at
        )
        values (
            $1::uuid,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            case
                when $10::integer is null
                then null
                else (
                    now()
                    + (
                        $10
                        * interval '1 second'
                    )
                )
            end,
            null,
            null,
            null,
            null,
            0,
            case
                when $9 = 'DEAD_LETTER'
                then now()
                else null
            end
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
            status =
                excluded.status,
            next_retry_at =
                excluded.next_retry_at,
            retry_started_at = null,
            retry_worker_id = null,
            resolution_notes = null,
            resolved_at = null,
            dead_letter_alerted_at = (
                case
                    when excluded.status = 'DEAD_LETTER'
                     and current_error.status
                         != 'DEAD_LETTER'
                    then null
                    else current_error.dead_letter_alerted_at
                end
            ),
            dead_letter_alert_error = (
                case
                    when excluded.status = 'DEAD_LETTER'
                     and current_error.status
                         != 'DEAD_LETTER'
                    then null
                    else current_error.dead_letter_alert_error
                end
            ),
            dead_letter_alert_attempt_count = (
                case
                    when excluded.status = 'DEAD_LETTER'
                     and current_error.status
                         != 'DEAD_LETTER'
                    then 0
                    else current_error.dead_letter_alert_attempt_count
                end
            ),
            dead_letter_alert_next_at = (
                case
                    when excluded.status = 'DEAD_LETTER'
                     and current_error.status
                         != 'DEAD_LETTER'
                    then now()
                    when excluded.status != 'DEAD_LETTER'
                    then null
                    else current_error.dead_letter_alert_next_at
                end
            ),
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
        retry_count,
        error_status,
        retry_delay_seconds,
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

    result = dict(row)
    result["became_dead_letter"] = (
        became_dead_letter
    )

    return result


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

    return dict(row) if row else None


async def get_workflow_error_for_action(
    connection: asyncpg.Connection,
    *,
    lead_id,
    failed_action: str,
) -> dict | None:
    row = await connection.fetchrow(
        """
        select *
        from public.workflow_errors
        where lead_id = $1::uuid
          and failed_action = $2;
        """,
        lead_id,
        failed_action,
    )

    return dict(row) if row else None


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
            retry_count = retry_count + 1,
            last_retry_actor_id = $2::uuid,
            last_retry_reason = $3,
            next_retry_at = null,
            retry_started_at = now(),
            retry_worker_id = null,
            updated_at = now()
        where id = $1::uuid
          and status in (
              'OPEN',
              'DEAD_LETTER'
          )
        returning *;
        """,
        error_id,
        actor_id,
        reason,
    )

    if row is None:
        raise RuntimeError(
            "Workflow error is not available "
            "for manual retry."
        )

    return dict(row)


async def claim_due_workflow_errors(
    connection: asyncpg.Connection,
    *,
    worker_id: str,
    max_attempts: int,
    batch_size: int,
    stale_after_seconds: int,
) -> list[dict]:
    rows = await connection.fetch(
        """
        with candidates as (
            select id
            from public.workflow_errors
            where retryable = true
              and retry_count < $2
              and (
                  (
                      status = 'OPEN'
                      and next_retry_at <= now()
                  )
                  or
                  (
                      status = 'RETRYING'
                      and retry_started_at
                          <= (
                              now()
                              - (
                                  $4
                                  * interval '1 second'
                              )
                          )
                  )
              )
            order by
                coalesce(
                    next_retry_at,
                    retry_started_at,
                    created_at
                ),
                created_at
            for update skip locked
            limit $3
        )
        update public.workflow_errors error
        set
            status = 'RETRYING',
            retry_count =
                error.retry_count + 1,
            next_retry_at = null,
            retry_started_at = now(),
            retry_worker_id = $1,
            last_retry_actor_id = null,
            last_retry_reason = (
                'Automatic retry worker'
            ),
            updated_at = now()
        from candidates
        where error.id = candidates.id
        returning error.*;
        """,
        worker_id,
        max_attempts,
        batch_size,
        stale_after_seconds,
    )

    return [dict(row) for row in rows]


async def claim_workflow_error_by_id(
    connection: asyncpg.Connection,
    *,
    error_id,
    worker_id: str,
    max_attempts: int,
) -> dict | None:
    row = await connection.fetchrow(
        """
        update public.workflow_errors
        set
            status = 'RETRYING',
            retry_count = retry_count + 1,
            next_retry_at = null,
            retry_started_at = now(),
            retry_worker_id = $2,
            last_retry_actor_id = null,
            last_retry_reason = (
                'Explicit automatic retry execution'
            ),
            updated_at = now()
        where id = $1::uuid
          and status = 'OPEN'
          and retryable = true
          and retry_count < $3
        returning *;
        """,
        error_id,
        worker_id,
        max_attempts,
    )

    return dict(row) if row else None


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
            retry_started_at = null,
            retry_worker_id = null,
            dead_letter_alert_next_at = null,
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


async def claim_due_dead_letter_alerts(
    connection: asyncpg.Connection,
    *,
    batch_size: int,
    lease_seconds: int,
) -> list[dict]:
    rows = await connection.fetch(
        """
        with candidates as (
            select id
            from public.workflow_errors
            where status = 'DEAD_LETTER'
              and dead_letter_alerted_at is null
              and (
                  dead_letter_alert_next_at is null
                  or dead_letter_alert_next_at <= now()
              )
            order by created_at
            for update skip locked
            limit $1
        )
        update public.workflow_errors error
        set
            dead_letter_alert_attempt_count =
                error.dead_letter_alert_attempt_count
                + 1,
            dead_letter_alert_next_at = (
                now()
                + (
                    $2
                    * interval '1 second'
                )
            ),
            updated_at = now()
        from candidates
        where error.id = candidates.id
        returning error.*;
        """,
        batch_size,
        lease_seconds,
    )

    return [dict(row) for row in rows]


async def claim_dead_letter_alert_by_id(
    connection: asyncpg.Connection,
    *,
    error_id,
    lease_seconds: int,
) -> dict | None:
    row = await connection.fetchrow(
        """
        update public.workflow_errors
        set
            dead_letter_alert_attempt_count =
                dead_letter_alert_attempt_count
                + 1,
            dead_letter_alert_next_at = (
                now()
                + (
                    $2
                    * interval '1 second'
                )
            ),
            updated_at = now()
        where id = $1::uuid
          and status = 'DEAD_LETTER'
          and dead_letter_alerted_at is null
          and (
              dead_letter_alert_next_at is null
              or dead_letter_alert_next_at <= now()
          )
        returning *;
        """,
        error_id,
        lease_seconds,
    )

    return dict(row) if row else None


async def mark_dead_letter_alert_sent(
    connection: asyncpg.Connection,
    *,
    error_id,
) -> None:
    await connection.execute(
        """
        update public.workflow_errors
        set
            dead_letter_alerted_at = now(),
            dead_letter_alert_error = null,
            dead_letter_alert_next_at = null,
            updated_at = now()
        where id = $1::uuid;
        """,
        error_id,
    )


async def mark_dead_letter_alert_failed(
    connection: asyncpg.Connection,
    *,
    error_id,
    error_message: str,
    retry_delay_seconds: int,
) -> None:
    await connection.execute(
        """
        update public.workflow_errors
        set
            dead_letter_alert_error = $2,
            dead_letter_alert_next_at = (
                now()
                + (
                    $3
                    * interval '1 second'
                )
            ),
            updated_at = now()
        where id = $1::uuid;
        """,
        error_id,
        error_message[:1000],
        retry_delay_seconds,
    )
