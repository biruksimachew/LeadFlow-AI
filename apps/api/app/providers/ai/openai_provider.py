import json
from time import perf_counter

from openai import AsyncOpenAI

from app.config import settings
from app.models.ai_assessment import (
    AIAssessment,
    AI_ASSESSMENT_JSON_SCHEMA,
)
from app.models.lead import NormalizedLead
from app.providers.ai.base import (
    AIContext,
    AIProviderError,
    AIProviderResult,
)


SYSTEM_PROMPT = """
You are the structured lead-classification component for
NorthStar Home Services.

Classify the submitted synthetic service enquiry.

Rules:
- Use only information provided in the request.
- Do not invent prices, availability, customer facts or promises.
- Classify the customer's actual request.
- Submitted service and urgency fields are hints, not authority.
- If the message conflicts with those fields, classify from the
  evidence in the message.
- Keep summary and explanation concise and factual.
- Risk flags should identify ambiguity, conflicting information,
  possible spam or other facts requiring human review.
- Never make routing, CRM, booking or customer-contact decisions.
"""


class OpenAIAssessmentProvider:

    def __init__(self):

        if not settings.openai_api_key:
            raise AIProviderError(
                "AI_NOT_CONFIGURED",
                "OPENAI_API_KEY is not configured.",
            )

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.ai_timeout_seconds,
        )

    async def assess(
        self,
        lead: NormalizedLead,
        context: AIContext,
    ) -> AIProviderResult:

        # Deliberately exclude:
        # full_name
        # email
        # phone
        #
        # They are unnecessary for classification.
        payload = {
            "submitted_service_type": (
                lead.service_type.value
            ),
            "submitted_urgency": (
                lead.urgency.value
            ),
            "service_zone": (
                context.service_zone
            ),
            "source": lead.source.value,
            "message": lead.message,
        }

        started = perf_counter()

        try:

            response = await self.client.responses.create(
                model=settings.openai_model,

                instructions=SYSTEM_PROMPT,

                input=(
                    "Return the structured lead assessment "
                    "for this JSON input:\n"
                    + json.dumps(payload)
                ),

                text={
                    "format": {
                        "type": "json_schema",
                        "name": "lead_assessment",
                        "strict": True,
                        "schema": (
                            AI_ASSESSMENT_JSON_SCHEMA
                        ),
                    }
                },

                store=False,
            )

        except Exception as exc:

            raise AIProviderError(
                "AI_PROVIDER_ERROR",
                (
                    f"{type(exc).__name__}: "
                    f"{str(exc)[:300]}"
                ),
            ) from exc

        elapsed_ms = int(
            (perf_counter() - started) * 1000
        )

        if not response.output_text:

            raise AIProviderError(
                "AI_EMPTY_RESPONSE",
                "AI provider returned no structured output.",
            )

        try:

            assessment = (
                AIAssessment.model_validate_json(
                    response.output_text
                )
            )

        except Exception as exc:

            raise AIProviderError(
                "AI_INVALID_OUTPUT",
                "AI provider returned invalid structured output.",
            ) from exc

        return AIProviderResult(
            assessment=assessment,
            provider="openai",
            model=settings.openai_model,
            prompt_version=(
                settings.ai_prompt_version
            ),
            processing_time_ms=elapsed_ms,
        )