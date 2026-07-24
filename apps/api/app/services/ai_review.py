from app.models.ai_assessment import AIAssessment
from app.models.lead import NormalizedLead


AI_CONFIDENCE_THRESHOLD = 0.70


def determine_ai_final_status(
    *,
    lead: NormalizedLead,
    deterministic_status: str,
    hard_rule_result: str | None,
    assessment: AIAssessment,
) -> tuple[str, list[str]]:

    review_reasons: list[str] = []

    # AI can never override a hard rule.
    if hard_rule_result is not None:
        return (
            deterministic_status,
            review_reasons,
        )

    if (
        assessment.confidence
        < AI_CONFIDENCE_THRESHOLD
    ):
        review_reasons.append(
            "LOW_AI_CONFIDENCE"
        )

    ai_service = (
        assessment.service_category.value
    )

    submitted_service = (
        lead.service_type.value
    )

    if (
        ai_service != "unknown"
        and ai_service != submitted_service
    ):
        review_reasons.append(
            "SERVICE_CATEGORY_CONFLICT"
        )

    ai_urgency = assessment.urgency.value

    submitted_urgency = lead.urgency.value

    if (
        ai_urgency != "unknown"
        and submitted_urgency != "unknown"
        and ai_urgency != submitted_urgency
    ):
        review_reasons.append(
            "URGENCY_CONFLICT"
        )

    if review_reasons:
        return (
            "REVIEW_REQUIRED",
            review_reasons,
        )

    return (
        deterministic_status,
        review_reasons,
    )