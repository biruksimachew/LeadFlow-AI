from app.models.lead import NormalizedLead
from app.services.contact_mapping import split_name


def build_contact_properties(
    *,
    lead: NormalizedLead,
    score: int,
    status: str,
    correlation_id: str,
    service_zone: str | None,
) -> dict[str, str]:

    first_name, last_name = split_name(
        lead.full_name
    )

    properties: dict[str, str] = {
        "firstname": first_name,
        "lastname": last_name,
        "leadflow_score": str(score),
        "leadflow_source": lead.source.value,
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

    if lead.email_normalized:
        properties["email"] = (
            lead.email_normalized
        )

    if lead.phone_e164:

        properties["phone"] = (
            lead.phone_e164
        )

        properties[
            "leadflow_phone_e164"
        ] = lead.phone_e164

    if service_zone:
        properties[
            "leadflow_service_zone"
        ] = service_zone

    return properties