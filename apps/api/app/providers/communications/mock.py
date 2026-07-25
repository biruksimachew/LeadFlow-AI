from uuid import uuid4

from app.providers.communications.base import (
    MessageResult,
)


class MockCommunicationProvider:

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        body: str,
    ) -> MessageResult:

        payload = {
            "to": to,
            "subject": subject,
            "body": body,
        }

        return MessageResult(
            provider="mock",
            provider_message_id=(
                f"mock_email_{uuid4().hex}"
            ),
            payload=payload,
        )

    async def send_sms(
        self,
        *,
        to: str,
        body: str,
    ) -> MessageResult:

        payload = {
            "to": to,
            "body": body,
        }

        return MessageResult(
            provider="mock",
            provider_message_id=(
                f"mock_sms_{uuid4().hex}"
            ),
            payload=payload,
        )

    async def send_slack(
        self,
        *,
        recipient: str,
        body: str,
    ) -> MessageResult:

        payload = {
            "recipient": recipient,
            "body": body,
        }

        return MessageResult(
            provider="mock",
            provider_message_id=(
                f"mock_slack_{uuid4().hex}"
            ),
            payload=payload,
        )