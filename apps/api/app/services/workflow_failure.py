from __future__ import annotations

import json
from dataclasses import dataclass

from app.config import settings
from app.repositories.workflow_errors import (
    upsert_workflow_error,
)


@dataclass(slots=True)
class WorkflowStageError(RuntimeError):
    code: str
    message: str
    retryable: bool = False
    provider: str | None = None

    def __post_init__(self) -> None:
        RuntimeError.__init__(
            self,
            self.message,
        )


def classify_retryable_code(
    error_code: str | None,
) -> bool:
    normalized = (
        error_code
        or ""
    ).upper()

    retryable_markers = (
        "TIMEOUT",
        "NETWORK",
        "RATE_LIMIT",
        "SERVER_ERROR",
        "UNAVAILABLE",
        "TEMPORARY",
        "CONNECTION",
        "BAD_GATEWAY",
        "GATEWAY_TIMEOUT",
    )

    return any(
        marker in normalized
        for marker in retryable_markers
    )


def failure_metadata(
    exc: Exception,
) -> tuple[
    str,
    str,
    bool,
    str | None,
]:
    error_code = str(
        getattr(
            exc,
            "code",
            "LEAD_CONTINUATION_FAILED",
        )
    )
    error_message = str(
        getattr(
            exc,
            "message",
            str(exc),
        )
    )
    retryable = bool(
        getattr(
            exc,
            "retryable",
            classify_retryable_code(
                error_code
            ),
        )
    )
    provider = getattr(
        exc,
        "provider",
        None,
    )

    if provider is None:
        upper_code = error_code.upper()

        if upper_code.startswith("RESEND_"):
            provider = "resend"
        elif upper_code.startswith("SLACK_"):
            provider = "slack"
        elif upper_code.startswith("TWILIO_"):
            provider = "twilio"
        elif upper_code.startswith("HUBSPOT_"):
            provider = "hubspot"

    return (
        error_code,
        error_message,
        retryable,
        provider,
    )


async def record_workflow_failure(
    pool,
    *,
    lead_id,
    correlation_id: str,
    failed_action: str,
    exc: Exception,
    trigger: str,
    initiated_by: str | None = None,
) -> dict:
    (
        error_code,
        error_message,
        retryable,
        provider,
    ) = failure_metadata(exc)

    async with pool.acquire() as connection:
        async with connection.transaction():
            state = await upsert_workflow_error(
                connection,
                lead_id=lead_id,
                correlation_id=correlation_id,
                failed_action=failed_action,
                provider=provider,
                error_code=error_code,
                error_message=(
                    error_message[:1000]
                ),
                retryable=retryable,
                max_attempts=(
                    settings
                    .workflow_retry_max_attempts
                ),
                base_delay_seconds=(
                    settings
                    .workflow_retry_base_delay_seconds
                ),
                max_delay_seconds=(
                    settings
                    .workflow_retry_max_delay_seconds
                ),
            )

            if state["status"] == "OPEN":
                event_type = (
                    "WORKFLOW_RETRY_SCHEDULED"
                )
                event_result = "retried"
            else:
                event_type = (
                    "WORKFLOW_DEAD_LETTERED"
                )
                event_result = "failed"

            await connection.execute(
                """
                insert into public.workflow_events (
                    lead_id,
                    correlation_id,
                    event_type,
                    actor_type,
                    actor_id,
                    provider,
                    result,
                    details,
                    error_code,
                    error_message
                )
                values (
                    $1::uuid,
                    $2,
                    $3,
                    'workflow',
                    $4,
                    $5,
                    $6,
                    $7::jsonb,
                    $8,
                    $9
                );
                """,
                lead_id,
                correlation_id,
                event_type,
                initiated_by,
                provider,
                event_result,
                json.dumps({
                    "workflow_error_id": str(
                        state["id"]
                    ),
                    "failed_action":
                        failed_action,
                    "trigger": trigger,
                    "retryable": retryable,
                    "retry_count": (
                        state["retry_count"]
                    ),
                    "max_attempts": (
                        settings
                        .workflow_retry_max_attempts
                    ),
                    "next_retry_at": (
                        state["next_retry_at"]
                        .isoformat()
                        if state["next_retry_at"]
                        else None
                    ),
                }),
                error_code,
                error_message[:1000],
            )

    return state
