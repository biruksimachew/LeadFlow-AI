from time import perf_counter

from app.config import settings
from app.models.ai_assessment import AIAssessment
from app.models.lead import NormalizedLead
from app.providers.ai.base import (
    AIContext,
    AIProviderResult,
)


def infer_service_from_message(
    message: str,
) -> str | None:

    text = message.lower()

    if any(
        word in text
        for word in (
            "pipe",
            "leak",
            "faucet",
            "drain",
            "toilet",
        )
    ):
        return "plumbing"

    if any(
        word in text
        for word in (
            "power",
            "outlet",
            "sparks",
            "breaker",
            "wiring",
        )
    ):
        return "electrical"

    if any(
        word in text
        for word in (
            "air conditioner",
            "ac ",
            "hvac",
            "heating",
            "cooling",
        )
    ):
        return "hvac"

    if any(
        word in text
        for word in (
            "washer",
            "dryer",
            "oven",
            "refrigerator",
            "dishwasher",
        )
    ):
        return "appliance_repair"

    return None


class MockAIProvider:

    async def assess(
        self,
        lead: NormalizedLead,
        context: AIContext,
    ) -> AIProviderResult:

        started = perf_counter()

        message = lead.message or ""

        detected_service = infer_service_from_message(
            message
        )

        risk_flags: list[str] = []

        if detected_service is None:

            detected_service = lead.service_type.value
            confidence = 0.55

        else:
            confidence = 0.94

        if (
            detected_service
            != lead.service_type.value
        ):
            risk_flags.append(
                "service_category_conflict"
            )

        assessment = AIAssessment(
            intent="request_service",
            service_category=detected_service,
            urgency=lead.urgency.value,
            confidence=confidence,
            summary=(
                message[:250]
                if message
                else "Customer submitted a service enquiry."
            ),
            risk_flags=risk_flags,
            explanation=(
                "Assessment based on submitted service, "
                "urgency and customer message."
            ),
        )

        elapsed_ms = int(
            (perf_counter() - started) * 1000
        )

        return AIProviderResult(
            assessment=assessment,
            provider="mock",
            model="leadflow-mock-v1",
            prompt_version=settings.ai_prompt_version,
            processing_time_ms=elapsed_ms,
        )