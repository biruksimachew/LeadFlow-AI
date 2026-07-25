from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class MessageResult:
    provider: str
    provider_message_id: str
    payload: dict


class CommunicationProviderError(RuntimeError):

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ):
        super().__init__(message)

        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code


class CommunicationProvider(Protocol):

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        idempotency_key: str,
    ) -> MessageResult:
        ...

    async def send_sms(
        self,
        *,
        to: str,
        body: str,
    ) -> MessageResult:
        ...

    async def send_slack(
        self,
        *,
        recipient: str,
        body: str,
    ) -> MessageResult:
        ...