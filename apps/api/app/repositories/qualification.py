import json

import asyncpg

from app.providers.ai.base import AIProviderResult
from app.services.qualification import QualificationResult


# ============================================================
# Deterministic qualification
# ============================================================


async def persist_qualification_result(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    result: QualificationResult,
) -> None:
    """
    Persist a successful deterministic qualification result,
    update the canonical lead state and write an audit event.
    """

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
            qualification_status,
            final_status
        )
        values (
            $1,
            $2,
            $3,
            $4::jsonb,
            $5,
            $6,
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
    """
    Return the latest deterministic/AI qualification state
    for a canonical lead.
    """

    row = await connection.fetchrow(
        """
        select
            id,
            deterministic_score,
            score_breakdown,
            hard_rule_result,
            qualification_status,
            final_status,
            ai_status,
            ai_provider,
            ai_model,
            ai_result,
            ai_confidence,
            ai_review_reasons,
            ai_error_code
        from public.qualification_results
        where lead_id = $1
        order by created_at desc
        limit 1;
        """,
        lead_id,
    )

    if row is None:
        return None

    score_breakdown = row["score_breakdown"]

    if isinstance(score_breakdown, str):
        score_breakdown = json.loads(
            score_breakdown
        )

    ai_result = row["ai_result"]

    if isinstance(ai_result, str):
        ai_result = json.loads(
            ai_result
        )

    return {
        "id": row["id"],
        "score": row["deterministic_score"],
        "score_breakdown": score_breakdown,
        "hard_rule_result": row[
            "hard_rule_result"
        ],
        "qualification_status": row[
            "qualification_status"
        ],
        "final_status": row["final_status"],
        "ai_status": row["ai_status"],
        "ai_provider": row["ai_provider"],
        "ai_model": row["ai_model"],
        "ai_result": ai_result,
        "ai_confidence": row["ai_confidence"],
        "ai_review_reasons": list(
            row["ai_review_reasons"] or []
        ),
        "ai_error_code": row["ai_error_code"],
    }


async def persist_qualification_failure(
    connection: asyncpg.Connection,
    *,
    lead_id,
    correlation_id: str,
    error_code: str,
    error_message: str,
) -> None:
    """
    Make a deterministic qualification failure visible.

    The intake remains durable and the lead is moved to
    REVIEW_REQUIRED so it cannot silently disappear.
    """

    safe_error_message = error_message[:1000]

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
            "stage": (
                "deterministic_qualification"
            ),
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
        safe_error_message,
    )


# ============================================================
# AI qualification
# ============================================================


async def persist_ai_assessment_success(
    connection: asyncpg.Connection,
    *,
    qualification_id,
    lead_id,
    correlation_id: str,
    provider_result: AIProviderResult,
    final_status: str,
    review_reasons: list[str],
) -> None:
    """
    Persist a successful structured AI assessment and update
    the final operational status.
    """

    assessment_json = json.dumps(
        provider_result.assessment.model_dump(
            mode="json"
        )
    )

    await connection.execute(
        """
        update public.qualification_results
        set
            ai_status = 'SUCCEEDED',
            ai_provider = $2,
            ai_model = $3,
            prompt_version = $4,
            ai_result = $5::jsonb,
            ai_confidence = $6,
            ai_processing_time_ms = $7,
            ai_review_reasons = $8,
            ai_error_code = null,
            ai_error_message = null,
            ai_completed_at = now(),
            final_status = $9
        where id = $1;
        """,
        qualification_id,
        provider_result.provider,
        provider_result.model,
        provider_result.prompt_version,
        assessment_json,
        provider_result.assessment.confidence,
        provider_result.processing_time_ms,
        review_reasons,
        final_status,
    )

    await connection.execute(
        """
        update public.leads
        set
            status = $2,
            last_error_code = null
        where id = $1;
        """,
        lead_id,
        final_status,
    )

    details_json = json.dumps(
        {
            "provider": (
                provider_result.provider
            ),
            "model": (
                provider_result.model
            ),
            "prompt_version": (
                provider_result.prompt_version
            ),
            "confidence": (
                provider_result
                .assessment
                .confidence
            ),
            "final_status": final_status,
            "review_reasons": (
                review_reasons
            ),
            "processing_time_ms": (
                provider_result
                .processing_time_ms
            ),
        }
    )

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            provider,
            result,
            details
        )
        values (
            $1,
            $2,
            'AI_ASSESSMENT_COMPLETED',
            'provider',
            $3,
            'succeeded',
            $4::jsonb
        );
        """,
        lead_id,
        correlation_id,
        provider_result.provider,
        details_json,
    )


async def persist_ai_assessment_failure(
    connection: asyncpg.Connection,
    *,
    qualification_id,
    lead_id,
    correlation_id: str,
    deterministic_status: str,
    provider: str | None,
    model: str | None,
    prompt_version: str,
    error_code: str,
    error_message: str,
) -> None:
    """
    Persist an AI-provider failure while preserving the
    deterministic qualification result.
    """

    safe_error_message = (
        error_message[:1000]
    )

    await connection.execute(
        """
        update public.qualification_results
        set
            ai_status = 'FAILED',
            ai_provider = $2,
            ai_model = $3,
            prompt_version = $4,
            ai_error_code = $5,
            ai_error_message = $6,
            ai_completed_at = now(),
            final_status = $7
        where id = $1;
        """,
        qualification_id,
        provider,
        model,
        prompt_version,
        error_code,
        safe_error_message,
        deterministic_status,
    )

    await connection.execute(
        """
        update public.leads
        set
            status = $2,
            last_error_code = $3
        where id = $1;
        """,
        lead_id,
        deterministic_status,
        error_code,
    )

    details_json = json.dumps(
        {
            "stage": "ai_assessment",
            "provider": provider,
            "error_code": error_code,
            "fallback_status": (
                deterministic_status
            ),
        }
    )

    await connection.execute(
        """
        insert into public.workflow_events (
            lead_id,
            correlation_id,
            event_type,
            actor_type,
            provider,
            result,
            details,
            error_code,
            error_message
        )
        values (
            $1,
            $2,
            'AI_ASSESSMENT_FAILED',
            'provider',
            $3,
            'failed',
            $4::jsonb,
            $5,
            $6
        );
        """,
        lead_id,
        correlation_id,
        provider,
        details_json,
        error_code,
        safe_error_message,
    )