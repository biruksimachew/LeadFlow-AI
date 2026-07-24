from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class CRMContactResult:
    contact_id: str
    created: bool


@dataclass(slots=True)
class CRMDealResult:
    deal_id: str
    created: bool


@dataclass(slots=True)
class CRMOwner:
    id: str
    email: str | None
    first_name: str | None
    last_name: str | None


@dataclass(slots=True)
class CRMContactMatch:
    contact_id: str
    matched_by: str


class CRMProviderError(RuntimeError):

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


class CRMProvider(Protocol):

    async def health_check(self) -> bool:
        ...

    async def list_owners(
        self,
    ) -> list[CRMOwner]:
        ...

    async def ensure_properties(self) -> None:
        ...

    async def find_contact(
        self,
        *,
        email: str | None,
        phone_e164: str | None,
    ) -> CRMContactMatch | None:
        ...


    



    async def upsert_contact(
        self,
        *,
        email: str | None,
        phone_e164: str | None,
        properties: dict[str, str],
    ) -> CRMContactResult:
        ...




    async def find_deal(
        self,
        *,
        leadflow_lead_id: str,
    ) -> CRMDealResult | None:
        ...


    async def upsert_deal(
        self,
        *,
        leadflow_lead_id: str,
        properties: dict[str, str],
    ) -> CRMDealResult:
        ...


    async def associate_contact_with_deal(
        self,
        *,
        contact_id: str,
        deal_id: str,
    ) -> None:
        ...