import asyncpg

from app.config import settings
from app.models.lead import NormalizedLead
from app.providers.ai.base import (
    AIContext,
    AIProviderError,
)
from app.providers.ai.factory import (
    build_ai_provider,
)
from app.repositories.qualification import (
    persist_ai_assessment_failure,
    persist_ai_assessment_success,
)
from app.services.ai_review import (
    determine_ai_final_status,
)


def _configured_model() -> str | None:

    if settings.ai_provider.lower() == "openai":
        return settings.openai_model

    if settings.ai_provider.lower() == "mock":
        return "leadflow-mock-v1"

    return None


async def run_ai_assessment(
    pool: asyncpg.Pool,
    *,
    lead_id,
    correlation_id: str,
    lead: NormalizedLead,
    qualification: dict,
) -> str:
    """
    Run AI enrichment without giving AI authority over
    deterministic hard rules.

    SUCCEEDED assessments are never repeated.
    FAILED assessments may be safely retried.
    """

    if qualification["ai_status"] in {
        "SUCCEEDED",
        "SKIPPED",
    }:
        return qualification["final_status"]

    score_breakdown = (
        qualification["score_breakdown"]
        or {}
    )

    service_area = score_breakdown.get(
        "service_area",
        {},
    )

    context = AIContext(
        service_zone=service_area.get("zone"),
        deterministic_score=(
            qualification["score"]
        ),
        deterministic_status=(
            qualification["qualification_status"]
        ),
    )

    try:

        provider = build_ai_provider()

        provider_result = await provider.assess(
            lead,
            context,
        )

        final_status, review_reasons = (
            determine_ai_final_status(
                lead=lead,
                deterministic_status=(
                    qualification[
                        "qualification_status"
                    ]
                ),
                hard_rule_result=(
                    qualification[
                        "hard_rule_result"
                    ]
                ),
                assessment=(
                    provider_result.assessment
                ),
            )
        )

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_ai_assessment_success(
                    connection,
                    qualification_id=(
                        qualification["id"]
                    ),
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    provider_result=provider_result,
                    final_status=final_status,
                    review_reasons=review_reasons,
                )

        return final_status

    except AIProviderError as exc:

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_ai_assessment_failure(
                    connection,
                    qualification_id=(
                        qualification["id"]
                    ),
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    deterministic_status=(
                        qualification[
                            "qualification_status"
                        ]
                    ),
                    provider=settings.ai_provider,
                    model=_configured_model(),
                    prompt_version=(
                        settings.ai_prompt_version
                    ),
                    error_code=exc.code,
                    error_message=exc.message,
                )

        return qualification[
            "qualification_status"
        ]

    except (
        asyncpg.PostgresError,
        OSError,
    ):
        # Persistence/network failure is different from an
        # AI-provider failure. Let the caller expose a safe retry.
        raise

    except Exception as exc:

        async with pool.acquire() as connection:

            async with connection.transaction():

                await persist_ai_assessment_failure(
                    connection,
                    qualification_id=(
                        qualification["id"]
                    ),
                    lead_id=lead_id,
                    correlation_id=correlation_id,
                    deterministic_status=(
                        qualification[
                            "qualification_status"
                        ]
                    ),
                    provider=settings.ai_provider,
                    model=_configured_model(),
                    prompt_version=(
                        settings.ai_prompt_version
                    ),
                    error_code="AI_UNEXPECTED_ERROR",
                    error_message=(
                        f"{type(exc).__name__}: {str(exc)}"
                    ),
                )

        return qualification[
            "qualification_status"
        ]