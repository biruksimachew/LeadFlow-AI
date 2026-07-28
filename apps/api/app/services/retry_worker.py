from __future__ import annotations

import asyncio
import json
import logging
from uuid import uuid4

from app.config import settings
from app.repositories.workflow_errors import (
    claim_dead_letter_alert_by_id,
    claim_due_dead_letter_alerts,
    claim_due_workflow_errors,
    claim_workflow_error_by_id,
    get_workflow_error,
    mark_dead_letter_alert_failed,
    mark_dead_letter_alert_sent,
    resolve_workflow_error_for_action,
    upsert_workflow_error,
)
from app.services.continuation import (
    run_lead_continuation,
)
from app.services.dead_letter_alerts import (
    send_dead_letter_alert,
)


logger = logging.getLogger(__name__)


class WorkflowRetryWorker:
    def __init__(
        self,
        pool,
        *,
        worker_id: str | None = None,
    ) -> None:
        self.pool = pool
        self.worker_id = (
            worker_id
            or f"retry-worker-{uuid4().hex[:12]}"
        )
        self._stop_event = asyncio.Event()

    async def stop(self) -> None:
        self._stop_event.set()

    async def _record_event(
        self,
        *,
        workflow_error: dict,
        event_type: str,
        result: str,
        details: dict,
        error_code: str | None = None,
    ) -> None:
        async with self.pool.acquire() as connection:
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
                    error_code
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
                    $8
                );
                """,
                workflow_error["lead_id"],
                workflow_error[
                    "correlation_id"
                ],
                event_type,
                self.worker_id,
                workflow_error["provider"],
                result,
                json.dumps(details),
                error_code,
            )

    async def _claim_due(
        self,
    ) -> list[dict]:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                return await claim_due_workflow_errors(
                    connection,
                    worker_id=self.worker_id,
                    max_attempts=(
                        settings
                        .workflow_retry_max_attempts
                    ),
                    batch_size=(
                        settings
                        .workflow_retry_batch_size
                    ),
                    stale_after_seconds=(
                        settings
                        .workflow_retry_stale_after_seconds
                    ),
                )

    async def _ensure_failed_state(
        self,
        workflow_error: dict,
        *,
        error_code: str | None,
    ) -> dict:
        async with self.pool.acquire() as connection:
            current = await get_workflow_error(
                connection,
                workflow_error["id"],
            )

            if (
                current is not None
                and current["status"]
                != "RETRYING"
            ):
                return current

            async with connection.transaction():
                return await upsert_workflow_error(
                    connection,
                    lead_id=(
                        workflow_error["lead_id"]
                    ),
                    correlation_id=(
                        workflow_error[
                            "correlation_id"
                        ]
                    ),
                    failed_action=(
                        workflow_error[
                            "failed_action"
                        ]
                    ),
                    provider=(
                        workflow_error["provider"]
                    ),
                    error_code=(
                        error_code
                        or workflow_error[
                            "error_code"
                        ]
                    ),
                    error_message=(
                        workflow_error[
                            "error_message"
                        ]
                    ),
                    retryable=bool(
                        workflow_error[
                            "retryable"
                        ]
                    ),
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

    async def process_claimed_error(
        self,
        workflow_error: dict,
    ) -> dict:
        await self._record_event(
            workflow_error=workflow_error,
            event_type=(
                "WORKFLOW_AUTO_RETRY_STARTED"
            ),
            result="started",
            details={
                "workflow_error_id": str(
                    workflow_error["id"]
                ),
                "retry_count": (
                    workflow_error[
                        "retry_count"
                    ]
                ),
                "max_attempts": (
                    settings
                    .workflow_retry_max_attempts
                ),
            },
        )

        continuation = (
            await run_lead_continuation(
                self.pool,
                lead_id=str(
                    workflow_error["lead_id"]
                ),
                trigger="AUTO_RETRY",
                initiated_by=self.worker_id,
                force_crm_sync=False,
            )
        )

        if continuation.status in {
            "SUCCEEDED",
            "SKIPPED",
        }:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    await resolve_workflow_error_for_action(
                        connection,
                        lead_id=(
                            workflow_error[
                                "lead_id"
                            ]
                        ),
                        failed_action=(
                            workflow_error[
                                "failed_action"
                            ]
                        ),
                        resolution_notes=(
                            "Automatic retry completed "
                            "successfully."
                        ),
                    )

            await self._record_event(
                workflow_error=workflow_error,
                event_type=(
                    "WORKFLOW_AUTO_RETRY_SUCCEEDED"
                ),
                result="succeeded",
                details={
                    "workflow_error_id": str(
                        workflow_error["id"]
                    ),
                    "retry_count": (
                        workflow_error[
                            "retry_count"
                        ]
                    ),
                    "continuation_status": (
                        continuation.status
                    ),
                },
            )

            return {
                "status": "RESOLVED",
                "workflow_error_id": str(
                    workflow_error["id"]
                ),
            }

        state = await self._ensure_failed_state(
            workflow_error,
            error_code=(
                continuation.error_code
            ),
        )

        await self._record_event(
            workflow_error=state,
            event_type=(
                "WORKFLOW_AUTO_RETRY_FAILED"
            ),
            result="failed",
            details={
                "workflow_error_id": str(
                    state["id"]
                ),
                "retry_count": (
                    state["retry_count"]
                ),
                "next_retry_at": (
                    state["next_retry_at"]
                    .isoformat()
                    if state["next_retry_at"]
                    else None
                ),
                "final_state": state["status"],
            },
            error_code=(
                continuation.error_code
                or state["error_code"]
            ),
        )

        if state["status"] == "DEAD_LETTER":
            await self.deliver_dead_letter_alert(
                str(state["id"])
            )

        return {
            "status": state["status"],
            "workflow_error_id": str(
                state["id"]
            ),
        }

    async def process_error(
        self,
        error_id: str,
    ) -> dict | None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                claimed = (
                    await claim_workflow_error_by_id(
                        connection,
                        error_id=error_id,
                        worker_id=self.worker_id,
                        max_attempts=(
                            settings
                            .workflow_retry_max_attempts
                        ),
                    )
                )

        if claimed is None:
            return None

        return await self.process_claimed_error(
            claimed
        )

    async def deliver_dead_letter_alert(
        self,
        error_id: str,
    ) -> bool:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                workflow_error = (
                    await claim_dead_letter_alert_by_id(
                        connection,
                        error_id=error_id,
                        lease_seconds=(
                            settings
                            .workflow_dead_letter_alert_retry_seconds
                        ),
                    )
                )

        if workflow_error is None:
            return False

        succeeded, error_message = (
            await send_dead_letter_alert(
                self.pool,
                workflow_error=workflow_error,
            )
        )

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                if succeeded:
                    await mark_dead_letter_alert_sent(
                        connection,
                        error_id=(
                            workflow_error["id"]
                        ),
                    )
                else:
                    await mark_dead_letter_alert_failed(
                        connection,
                        error_id=(
                            workflow_error["id"]
                        ),
                        error_message=(
                            error_message
                            or (
                                "Unknown Slack "
                                "alert failure."
                            )
                        ),
                        retry_delay_seconds=(
                            settings
                            .workflow_dead_letter_alert_retry_seconds
                        ),
                    )

        return succeeded

    async def flush_dead_letter_alerts(
        self,
        *,
        limit: int | None = None,
    ) -> int:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                alerts = (
                    await claim_due_dead_letter_alerts(
                        connection,
                        batch_size=(
                            limit
                            or settings
                            .workflow_retry_batch_size
                        ),
                        lease_seconds=(
                            settings
                            .workflow_dead_letter_alert_retry_seconds
                        ),
                    )
                )

        delivered = 0

        for workflow_error in alerts:
            succeeded, error_message = (
                await send_dead_letter_alert(
                    self.pool,
                    workflow_error=(
                        workflow_error
                    ),
                )
            )

            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    if succeeded:
                        await mark_dead_letter_alert_sent(
                            connection,
                            error_id=(
                                workflow_error["id"]
                            ),
                        )
                        delivered += 1
                    else:
                        await mark_dead_letter_alert_failed(
                            connection,
                            error_id=(
                                workflow_error["id"]
                            ),
                            error_message=(
                                error_message
                                or (
                                    "Unknown Slack "
                                    "alert failure."
                                )
                            ),
                            retry_delay_seconds=(
                                settings
                                .workflow_dead_letter_alert_retry_seconds
                            ),
                        )

        return delivered

    async def run_once(self) -> int:
        claimed_errors = await self._claim_due()

        for workflow_error in claimed_errors:
            try:
                await self.process_claimed_error(
                    workflow_error
                )
            except Exception:
                logger.exception(
                    "Automatic retry crashed. "
                    "workflow_error_id=%s",
                    workflow_error["id"],
                )

        try:
            await self.flush_dead_letter_alerts()
        except Exception:
            logger.exception(
                "Dead-letter alert delivery crashed."
            )

        return len(claimed_errors)

    async def run_forever(self) -> None:
        logger.info(
            "Workflow retry worker started. "
            "worker_id=%s",
            self.worker_id,
        )

        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception:
                logger.exception(
                    "Workflow retry worker loop failed."
                )

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=(
                        settings
                        .workflow_retry_poll_seconds
                    ),
                )
            except TimeoutError:
                pass

        logger.info(
            "Workflow retry worker stopped. "
            "worker_id=%s",
            self.worker_id,
        )
