import re

from app.models.lead import LeadIntakeRequest, NormalizedLead


def normalize_name(value: str) -> str:
    """
    Remove unnecessary whitespace while preserving
    a human-readable name.
    """
    return " ".join(value.strip().split())


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None

    return value.strip().lower()


def normalize_phone_e164(value: str | None) -> str | None:
    """
    Normalize explicit international numbers to E.164-like form.

    Local numbers are intentionally not assigned a country code
    until service-area/country configuration exists.
    """
    if value is None:
        return None

    cleaned = value.strip()
    digits = re.sub(r"\D", "", cleaned)

    if not digits:
        return None

    # Explicit international + prefix
    if cleaned.startswith("+"):
        if 8 <= len(digits) <= 15:
            return f"+{digits}"

        return None

    # International 00 prefix
    if cleaned.startswith("00"):
        international_digits = digits[2:]

        if 8 <= len(international_digits) <= 15:
            return f"+{international_digits}"

    return None


def normalize_message(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def normalize_lead(lead: LeadIntakeRequest) -> NormalizedLead:
    return NormalizedLead(
        full_name=normalize_name(lead.full_name),

        email_raw=str(lead.email) if lead.email else None,
        email_normalized=normalize_email(
            str(lead.email) if lead.email else None
        ),

        phone_raw=lead.phone,
        phone_e164=normalize_phone_e164(lead.phone),

        service_type=lead.service_type,

        location_raw=" ".join(
            lead.location.strip().split()
        ),

        urgency=lead.urgency,

        message=normalize_message(lead.message),

        source=lead.source,

        preferred_contact=lead.preferred_contact,

        consent_marketing=lead.consent_marketing,
    )