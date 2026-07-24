from app.config import settings
from app.models.lead import NormalizedLead


def build_deal_properties(
    *,
    lead_id: str,
    lead: NormalizedLead,
    score: int,
    status: str,
    correlation_id: str,
) -> dict[str, str]:

    if not settings.hubspot_deal_pipeline_id:
        raise ValueError(
            "HUBSPOT_DEAL_PIPELINE_ID is not configured."
        )

    if not settings.hubspot_deal_stage_id:
        raise ValueError(
            "HUBSPOT_DEAL_STAGE_ID is not configured."
        )

    return {
        "dealname": (
            f"{lead.full_name} - "
            f"{lead.service_type.value}"
        ),

        "pipeline": (
            settings.hubspot_deal_pipeline_id
        ),

        "dealstage": (
            settings.hubspot_deal_stage_id
        ),

        "leadflow_lead_id": lead_id,

        "leadflow_score": str(score),

        "leadflow_source": (
            lead.source.value
        ),

        "leadflow_service_type": (
            lead.service_type.value
        ),

        "leadflow_urgency": (
            lead.urgency.value
        ),

        "leadflow_automation_status": status,

        "leadflow_correlation_id": (
            correlation_id
        ),
    }