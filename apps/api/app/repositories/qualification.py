import json

import asyncpg

from app.services.qualification import (
    QualificationResult,
)


async def persist_qualification_result(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    result: QualificationResult,
) -> None:

    breakdown_json = json.dumps(
        result.breakdown
    )

    await connection.execute(
        """
        insert into public.qualification_results (
            lead_id,
            correlation_id,
            deterministic_score,
            score_breakdown,
            hard_rule_result,
            qualification_status
        )
        values (
            $1,
            $2,
            $3,
            $4::jsonb,
            $5,
            $6
        );
        """,
        lead_id,
        correlation_id,
        result.score,
        breakdown_json,
        result.hard_rule_result,
        result.status,
    )


    await connection.execute(
        """
        update public.leads
        set
            score = $2,
            status = $3
        where id = $1;
        """,
        lead_id,
        result.score,
        result.status,
    )


    details_json = json.dumps(
        {
            "score": result.score,
            "status": result.status,
            "hard_rule_result": (
                result.hard_rule_result
            ),
            "breakdown": result.breakdown,
        }
    )


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
            'DETERMINISTIC_QUALIFICATION_COMPLETED',
            'system',
            'succeeded',
            $3::jsonb
        );
        """,
        lead_id,
        correlation_id,
        details_json,
    )

async def get_existing_qualification(
    connection: asyncpg.Connection,
    lead_id,
) -> dict | None:

    row = await connection.fetchrow(
        """
        select
            deterministic_score,
            score_breakdown,
            hard_rule_result,
            qualification_status
        from public.qualification_results
        where lead_id = $1
        order by created_at desc
        limit 1;
        """,
        lead_id,
    )

    if row is None:
        return None

    return {
        "score": row["deterministic_score"],
        "status": row["qualification_status"],
        "hard_rule_result": row["hard_rule_result"],
    }


async def persist_qualification_failure(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    error_code: str,
    error_message: str,
) -> None:

    await connection.execute(
        """
        update public.leads
        set
            status = 'REVIEW_REQUIRED',
            last_error_code = $2
        where id = $1;
        """,
        lead_id,
        error_code,
    )

    details_json = json.dumps(
        {
            "stage": "deterministic_qualification",
            "error_code": error_code,
        }
    )

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            result,
            details,
            error_code,
            error_message
        )
        values (
            $1,
            $2,
            'DETERMINISTIC_QUALIFICATION_FAILED',
            'system',
            'failed',
            $3::jsonb,
            $4,
            $5
        );
        """,
        lead_id,
        correlation_id,
        details_json,
        error_code,
        error_message[:1000],
    )