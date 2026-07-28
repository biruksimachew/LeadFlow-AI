from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from uuid import uuid4

import asyncpg
import httpx
import pytest


@dataclass(frozen=True)
class LeadIdentity:
    email: str
    phone: str


class AcceptanceHarness:
    def __init__(self) -> None:
        self.api_base_url = os.getenv(
            "ACCEPTANCE_API_BASE_URL",
            "http://127.0.0.1:8000",
        ).rstrip("/")

        self.n8n_webhook_url = os.getenv(
            "ACCEPTANCE_N8N_WEBHOOK_URL",
            "http://n8n:5678/webhook/leadflow-intake",
        )

        self.database_url = os.getenv("DATABASE_URL")
        self.orchestrator_token = os.getenv(
            "N8N_INTERNAL_API_TOKEN",
        )
        self.default_owner_id = os.getenv(
            "HUBSPOT_DEFAULT_OWNER_ID",
        )

        if not self.database_url:
            raise RuntimeError(
                "DATABASE_URL is required for acceptance tests.",
            )

        if not self.orchestrator_token:
            raise RuntimeError(
                "N8N_INTERNAL_API_TOKEN is required for acceptance tests.",
            )

        self.client = httpx.Client(
            timeout=httpx.Timeout(45.0),
        )

    def close(self) -> None:
        self.client.close()

    def new_identity(
        self,
        prefix: str,
    ) -> LeadIdentity:
        token = uuid4().hex[:10]
        last_four = int(
            uuid4().hex[:6],
            16,
        ) % 10000

        return LeadIdentity(
            email=(
                f"delivered+leadflow-{prefix}-{token}"
                "@resend.dev"
            ),
            phone=f"+1202555{last_four:04d}",
        )

    def lead_payload(
        self,
        *,
        prefix: str,
        service_type: str = "electrical",
        location: str = "North District, 10021",
        urgency: str = "within_7_days",
        source: str = "website",
        message: str | None = None,
        consent_marketing: bool = False,
        preferred_contact: str = "email",
        full_name: str = "Acceptance Test Lead",
        email: str | None = None,
        phone: str | None = None,
    ) -> dict:
        identity = self.new_identity(prefix)

        return {
            "full_name": full_name,
            "email": (
                identity.email
                if email is None
                else email
            ),
            "phone": (
                identity.phone
                if phone is None
                else phone
            ),
            "service_type": service_type,
            "location": location,
            "urgency": urgency,
            "message": (
                message
                if message is not None
                else (
                    "Several outlets stopped working and I need "
                    "an electrician to inspect the circuit this week."
                )
            ),
            "source": source,
            "preferred_contact": preferred_contact,
            "consent_marketing": consent_marketing,
        }

    def orchestration_headers(
        self,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "X-LeadFlow-Orchestrator-Token":
                self.orchestrator_token,
        }

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        return headers

    def intake(
        self,
        payload: dict,
        *,
        idempotency_key: str,
    ) -> dict:
        response = self.client.post(
            f"{self.api_base_url}/api/v1/orchestration/intake",
            headers=self.orchestration_headers(
                idempotency_key=idempotency_key,
            ),
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def stage(
        self,
        lead_id: str,
        stage: str,
    ) -> dict:
        response = self.client.post(
            (
                f"{self.api_base_url}/api/v1/orchestration/"
                f"leads/{lead_id}/{stage}"
            ),
            headers=self.orchestration_headers(),
        )
        response.raise_for_status()
        return response.json()

    def n8n(
        self,
        payload: dict,
        *,
        idempotency_key: str,
    ) -> dict:
        response = self.client.post(
            self.n8n_webhook_url,
            headers={
                "Idempotency-Key": idempotency_key,
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def _fetchrow(
        self,
        query: str,
        *args,
    ):
        connection = await asyncpg.connect(
            self.database_url,
        )
        try:
            return await connection.fetchrow(
                query,
                *args,
            )
        finally:
            await connection.close()

    async def _fetch(
        self,
        query: str,
        *args,
    ):
        connection = await asyncpg.connect(
            self.database_url,
        )
        try:
            return await connection.fetch(
                query,
                *args,
            )
        finally:
            await connection.close()

    def fetchrow(
        self,
        query: str,
        *args,
    ):
        return asyncio.run(
            self._fetchrow(
                query,
                *args,
            )
        )

    def fetch(
        self,
        query: str,
        *args,
    ):
        return asyncio.run(
            self._fetch(
                query,
                *args,
            )
        )


@pytest.fixture(scope="session")
def harness() -> AcceptanceHarness:
    test_harness = AcceptanceHarness()

    response = test_harness.client.get(
        f"{test_harness.api_base_url}/health",
    )
    response.raise_for_status()

    yield test_harness

    test_harness.close()


@pytest.fixture
def require_live() -> None:
    if os.getenv("RUN_LIVE_ACCEPTANCE") != "1":
        pytest.skip(
            "Set RUN_LIVE_ACCEPTANCE=1 to run live integration tests.",
        )
