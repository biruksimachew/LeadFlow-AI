from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import asyncpg
import pytest

from app.config import settings
from app.providers.communications.base import (
    CommunicationProviderError,
)
from app.services.continuation import (
    ContinuationResult,
)
from app.services.retry_worker import (
    WorkflowRetryWorker,
)
from app.services.workflow_failure import (
    record_workflow_failure,
)


pytestmark = pytest.mark.live


async def _pool(database_url: str):
    return await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=2,
    )


def test_17_retryable_failure_is_scheduled(
    harness,
    require_live,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "workflow_retry_base_delay_seconds",
        3600,
    )

    intake = harness.intake(
        harness.lead_payload(
            prefix="retry-scheduled",
        ),
        idempotency_key=(
            "accept-reliability-scheduled-"
            f"{uuid4().hex}"
        ),
    )

    async def scenario():
        pool = await _pool(
            harness.database_url
        )
        try:
            return await record_workflow_failure(
                pool,
                lead_id=intake["lead_id"],
                correlation_id=(
                    intake["correlation_id"]
                ),
                failed_action=(
                    "lead_continuation"
                ),
                exc=CommunicationProviderError(
                    "RESEND_TIMEOUT",
                    "Controlled transient failure.",
                    retryable=True,
                ),
                trigger="ACCEPTANCE_TEST",
            )
        finally:
            await pool.close()

    state = asyncio.run(scenario())

    assert state["status"] == "OPEN"
    assert state["retryable"] is True
    assert state["retry_count"] == 0
    assert state["next_retry_at"] is not None
    assert (
        state["next_retry_at"]
        > datetime.now(timezone.utc)
    )

    event = harness.fetchrow(
        """
        select event_type, result
        from public.workflow_events
        where lead_id = $1::uuid
          and event_type =
              'WORKFLOW_RETRY_SCHEDULED'
        order by created_at desc
        limit 1;
        """,
        intake["lead_id"],
    )

    assert event is not None
    assert event["result"] == "retried"


def test_18_automatic_retry_resolves_safely(
    harness,
    require_live,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "workflow_retry_base_delay_seconds",
        3600,
    )

    intake = harness.intake(
        harness.lead_payload(
            prefix="retry-resolved",
        ),
        idempotency_key=(
            "accept-reliability-resolved-"
            f"{uuid4().hex}"
        ),
    )

    async def fake_continuation(
        pool,
        *,
        lead_id,
        trigger,
        initiated_by=None,
        force_crm_sync=False,
    ):
        return ContinuationResult(
            status="SUCCEEDED",
            final_status="QUALIFIED_WARM",
            owner_id="acceptance-owner",
            crm_sync_status="SUCCEEDED",
        )

    import app.services.retry_worker as worker_module

    monkeypatch.setattr(
        worker_module,
        "run_lead_continuation",
        fake_continuation,
    )

    async def scenario():
        pool = await _pool(
            harness.database_url
        )
        try:
            state = await record_workflow_failure(
                pool,
                lead_id=intake["lead_id"],
                correlation_id=(
                    intake["correlation_id"]
                ),
                failed_action=(
                    "lead_continuation"
                ),
                exc=CommunicationProviderError(
                    "RESEND_TIMEOUT",
                    "Controlled transient failure.",
                    retryable=True,
                ),
                trigger="ACCEPTANCE_TEST",
            )

            worker = WorkflowRetryWorker(
                pool,
                worker_id=(
                    "acceptance-retry-success"
                ),
            )

            result = await worker.process_error(
                str(state["id"])
            )

            return state, result
        finally:
            await pool.close()

    state, result = asyncio.run(scenario())

    assert result is not None
    assert result["status"] == "RESOLVED"

    final_state = harness.fetchrow(
        """
        select
            status,
            retry_count,
            resolved_at,
            next_retry_at
        from public.workflow_errors
        where id = $1::uuid;
        """,
        state["id"],
    )

    assert final_state["status"] == "RESOLVED"
    assert final_state["retry_count"] == 1
    assert final_state["resolved_at"] is not None
    assert final_state["next_retry_at"] is None

    events = harness.fetch(
        """
        select event_type
        from public.workflow_events
        where lead_id = $1::uuid
          and event_type in (
              'WORKFLOW_AUTO_RETRY_STARTED',
              'WORKFLOW_AUTO_RETRY_SUCCEEDED'
          );
        """,
        intake["lead_id"],
    )

    assert {
        row["event_type"]
        for row in events
    } == {
        "WORKFLOW_AUTO_RETRY_STARTED",
        "WORKFLOW_AUTO_RETRY_SUCCEEDED",
    }


def test_19_exhausted_retry_dead_letters_and_alerts(
    harness,
    require_live,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "workflow_retry_base_delay_seconds",
        3600,
    )
    monkeypatch.setattr(
        settings,
        "communication_provider",
        "mock",
    )

    intake = harness.intake(
        harness.lead_payload(
            prefix="retry-dead-letter",
        ),
        idempotency_key=(
            "accept-reliability-dead-"
            f"{uuid4().hex}"
        ),
    )

    async def fake_continuation(
        pool,
        *,
        lead_id,
        trigger,
        initiated_by=None,
        force_crm_sync=False,
    ):
        return ContinuationResult(
            status="FAILED",
            error_code="RESEND_TIMEOUT",
        )

    import app.services.retry_worker as worker_module

    monkeypatch.setattr(
        worker_module,
        "run_lead_continuation",
        fake_continuation,
    )

    async def scenario():
        pool = await _pool(
            harness.database_url
        )
        try:
            state = await record_workflow_failure(
                pool,
                lead_id=intake["lead_id"],
                correlation_id=(
                    intake["correlation_id"]
                ),
                failed_action=(
                    "lead_continuation"
                ),
                exc=CommunicationProviderError(
                    "RESEND_TIMEOUT",
                    "Controlled transient failure.",
                    retryable=True,
                ),
                trigger="ACCEPTANCE_TEST",
            )

            async with pool.acquire() as connection:
                await connection.execute(
                    """
                    update public.workflow_errors
                    set
                        retry_count = $2,
                        next_retry_at = (
                            now()
                            + interval '1 hour'
                        )
                    where id = $1::uuid;
                    """,
                    state["id"],
                    (
                        settings
                        .workflow_retry_max_attempts
                        - 1
                    ),
                )

            worker = WorkflowRetryWorker(
                pool,
                worker_id=(
                    "acceptance-retry-dead"
                ),
            )

            result = await worker.process_error(
                str(state["id"])
            )

            return state, result
        finally:
            await pool.close()

    state, result = asyncio.run(scenario())

    assert result is not None
    assert result["status"] == "DEAD_LETTER"

    final_state = harness.fetchrow(
        """
        select
            status,
            retry_count,
            next_retry_at,
            dead_letter_alerted_at,
            dead_letter_alert_error
        from public.workflow_errors
        where id = $1::uuid;
        """,
        state["id"],
    )

    assert final_state["status"] == "DEAD_LETTER"
    assert (
        final_state["retry_count"]
        == settings.workflow_retry_max_attempts
    )
    assert final_state["next_retry_at"] is None
    assert (
        final_state["dead_letter_alerted_at"]
        is not None
    )
    assert (
        final_state["dead_letter_alert_error"]
        is None
    )

    alert = harness.fetchrow(
        """
        select event_type, provider, result
        from public.workflow_events
        where lead_id = $1::uuid
          and event_type =
              'WORKFLOW_DEAD_LETTER_ALERT_SENT'
        order by created_at desc
        limit 1;
        """,
        intake["lead_id"],
    )

    assert alert is not None
    assert alert["provider"] == "slack"
    assert alert["result"] == "succeeded"
