from __future__ import annotations

import json
from uuid import uuid4

import httpx

from app.config import settings


async def _record_alert_event(
    pool,
    *,
    workflow_error: dict,
    succeeded: bool,
    provider_message_id: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    async with pool.acquire() as connection:
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
                $1::uuid,
                $2,
                $3,
                'provider',
                'slack',
                $4,
                $5::jsonb,
                $6,
                $7
            );
            """,
            workflow_error["lead_id"],
            workflow_error[
                "correlation_id"
            ],
            (
                "WORKFLOW_DEAD_LETTER_ALERT_SENT"
                if succeeded
                else (
                    "WORKFLOW_DEAD_LETTER_ALERT_FAILED"
                )
            ),
            (
                "succeeded"
                if succeeded
                else "failed"
            ),
            json.dumps({
                "workflow_error_id": str(
                    workflow_error["id"]
                ),
                "failed_action": (
                    workflow_error[
                        "failed_action"
                    ]
                ),
                "channel": (
                    settings
                    .slack_dead_letter_channel
                ),
                "provider_message_id":
                    provider_message_id,
                "retry_count": (
                    workflow_error[
                        "retry_count"
                    ]
                ),
            }),
            error_code,
            (
                error_message[:1000]
                if error_message
                else None
            ),
        )


def _alert_body(
    workflow_error: dict,
) -> str:
    lead_url = (
        f"{settings.dashboard_base_url}"
        f"/dashboard/leads/"
        f"{workflow_error['lead_id']}"
    )

    return (
        "LeadFlow DEAD LETTER\n"
        f"Action: "
        f"{workflow_error['failed_action']}\n"
        f"Provider: "
        f"{workflow_error['provider'] or 'unknown'}\n"
        f"Error: "
        f"{workflow_error['error_code']}\n"
        f"Retries: "
        f"{workflow_error['retry_count']}\n"
        f"Correlation: "
        f"{workflow_error['correlation_id']}\n"
        f"Lead: {lead_url}"
    )


async def send_dead_letter_alert(
    pool,
    *,
    workflow_error: dict,
) -> tuple[bool, str | None]:
    if (
        settings.communication_provider
        .strip()
        .lower()
        == "mock"
    ):
        provider_message_id = (
            f"slack_mock_{uuid4().hex}"
        )

        await _record_alert_event(
            pool,
            workflow_error=workflow_error,
            succeeded=True,
            provider_message_id=(
                provider_message_id
            ),
        )

        return True, None

    if not settings.slack_bot_token:
        message = (
            "SLACK_BOT_TOKEN is missing."
        )

        await _record_alert_event(
            pool,
            workflow_error=workflow_error,
            succeeded=False,
            error_code=(
                "SLACK_NOT_CONFIGURED"
            ),
            error_message=message,
        )

        return False, message

    try:
        async with httpx.AsyncClient(
            timeout=(
                settings
                .communication_timeout_seconds
            )
        ) as client:
            response = await client.post(
                (
                    "https://slack.com/api/"
                    "chat.postMessage"
                ),
                headers={
                    "Authorization": (
                        "Bearer "
                        f"{settings.slack_bot_token}"
                    ),
                    "Content-Type":
                        "application/json",
                },
                json={
                    "channel": (
                        settings
                        .slack_dead_letter_channel
                    ),
                    "text": _alert_body(
                        workflow_error
                    ),
                    "unfurl_links": False,
                    "unfurl_media": False,
                },
            )

        payload = (
            response.json()
            if response.content
            else {}
        )

        if (
            response.status_code >= 400
            or payload.get("ok") is False
        ):
            raise RuntimeError(
                "Slack rejected the dead-letter "
                f"alert: HTTP "
                f"{response.status_code}, "
                f"{payload.get('error', 'unknown_error')}"
            )

        provider_message_id = str(
            payload.get("ts")
            or uuid4().hex
        )

        await _record_alert_event(
            pool,
            workflow_error=workflow_error,
            succeeded=True,
            provider_message_id=(
                provider_message_id
            ),
        )

        return True, None

    except Exception as exc:
        message = str(exc)

        await _record_alert_event(
            pool,
            workflow_error=workflow_error,
            succeeded=False,
            error_code=(
                "SLACK_DEAD_LETTER_ALERT_FAILED"
            ),
            error_message=message,
        )

        return False, message
