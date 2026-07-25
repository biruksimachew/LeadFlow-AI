from uuid import uuid4

import httpx

from app.config import settings

from app.providers.communications.base import (
    CommunicationProviderError,
    MessageResult,
)


class LiveCommunicationProvider:

    def __init__(self):

        if not settings.resend_api_key:
            raise CommunicationProviderError(
                "RESEND_NOT_CONFIGURED",
                "RESEND_API_KEY is missing.",
            )

        if not settings.slack_bot_token:
            raise CommunicationProviderError(
                "SLACK_NOT_CONFIGURED",
                "SLACK_BOT_TOKEN is missing.",
            )

        self.timeout = (
            settings.communication_timeout_seconds
        )

    async def _request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: dict,
        provider: str,
    ) -> dict:

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json_body,
                )

        except httpx.TimeoutException as exc:

            raise CommunicationProviderError(
                f"{provider.upper()}_TIMEOUT",
                f"{provider} request timed out.",
                retryable=True,
            ) from exc

        except httpx.RequestError as exc:

            raise CommunicationProviderError(
                f"{provider.upper()}_NETWORK_ERROR",
                str(exc),
                retryable=True,
            ) from exc

        if response.status_code == 429:

            raise CommunicationProviderError(
                f"{provider.upper()}_RATE_LIMIT",
                f"{provider} rate limit reached.",
                retryable=True,
                status_code=429,
            )

        if response.status_code >= 500:

            raise CommunicationProviderError(
                f"{provider.upper()}_SERVER_ERROR",
                (
                    f"{provider} returned "
                    f"{response.status_code}."
                ),
                retryable=True,
                status_code=response.status_code,
            )

        if response.status_code >= 400:

            raise CommunicationProviderError(
                f"{provider.upper()}_API_ERROR",
                (
                    f"{provider} returned "
                    f"{response.status_code}: "
                    f"{response.text[:500]}"
                ),
                retryable=False,
                status_code=response.status_code,
            )

        if not response.content:
            return {}

        payload = response.json()

        # Slack returns HTTP 200 even for many API errors.
        if (
            provider == "slack"
            and payload.get("ok") is False
        ):
            raise CommunicationProviderError(
                "SLACK_API_ERROR",
                (
                    "Slack rejected the request: "
                    f"{payload.get('error', 'unknown_error')}"
                ),
                retryable=False,
                status_code=response.status_code,
            )

        return payload

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        idempotency_key: str,
    ) -> MessageResult:

        request_payload = {
            "from": settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "text": body,
        }

        response = await self._request(
            method="POST",
            url="https://api.resend.com/emails",
            headers={
                "Authorization": (
                    f"Bearer {settings.resend_api_key}"
                ),
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
            json_body=request_payload,
            provider="resend",
        )

        message_id = response.get("id")

        if not message_id:
            raise CommunicationProviderError(
                "RESEND_EMPTY_RESULT",
                "Resend returned no message ID.",
                retryable=True,
            )

        return MessageResult(
            provider="resend",
            provider_message_id=str(message_id),
            payload={
                "to": to,
                "subject": subject,
                "idempotency_key": idempotency_key,
            },
        )

    async def send_sms(
        self,
        *,
        to: str,
        body: str,
    ) -> MessageResult:
        """
        SMS remains deliberately mocked for this portfolio
        environment.
        """

        return MessageResult(
            provider="twilio_mock",
            provider_message_id=(
                f"twilio_mock_{uuid4().hex}"
            ),
            payload={
                "to": to,
                "body": body,
                "expected_provider": "twilio",
                "expected_result": "queued",
            },
        )

    async def _open_slack_dm(
        self,
        user_id: str,
    ) -> str:

        payload = await self._request(
            method="POST",
            url=(
                "https://slack.com/api/"
                "conversations.open"
            ),
            headers={
                "Authorization": (
                    f"Bearer {settings.slack_bot_token}"
                ),
                "Content-Type": "application/json",
            },
            json_body={
                "users": user_id,
            },
            provider="slack",
        )

        channel_id = (
            payload.get("channel", {})
            .get("id")
        )

        if not channel_id:
            raise CommunicationProviderError(
                "SLACK_DM_OPEN_FAILED",
                "Slack returned no DM channel ID.",
                retryable=True,
            )

        return str(channel_id)

    async def send_slack(
        self,
        *,
        recipient: str,
        body: str,
    ) -> MessageResult:

        channel_id = recipient

        if recipient.startswith("U"):
            channel_id = await self._open_slack_dm(
                recipient
            )

        response = await self._request(
            method="POST",
            url=(
                "https://slack.com/api/"
                "chat.postMessage"
            ),
            headers={
                "Authorization": (
                    f"Bearer {settings.slack_bot_token}"
                ),
                "Content-Type": "application/json",
            },
            json_body={
                "channel": channel_id,
                "text": body,
                "unfurl_links": False,
                "unfurl_media": False,
            },
            provider="slack",
        )

        timestamp = response.get("ts")

        if not timestamp:
            raise CommunicationProviderError(
                "SLACK_EMPTY_RESULT",
                "Slack returned no message timestamp.",
                retryable=True,
            )

        return MessageResult(
            provider="slack",
            provider_message_id=str(timestamp),
            payload={
                "recipient": recipient,
                "channel_id": channel_id,
                "text": body,
            },
        )