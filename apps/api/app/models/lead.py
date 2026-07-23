from enum import Enum

from pydantic import BaseModel, EmailStr, Field, model_validator


class ServiceType(str, Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    APPLIANCE_REPAIR = "appliance_repair"
    OTHER = "other"


class Urgency(str, Enum):
    EMERGENCY = "emergency"
    WITHIN_24_HOURS = "within_24_hours"
    WITHIN_7_DAYS = "within_7_days"
    PLANNING = "planning"
    UNKNOWN = "unknown"


class LeadSource(str, Enum):
    WEBSITE = "website"
    META = "meta"
    MANUAL = "manual"
    CSV_TEST = "csv_test"


class PreferredContact(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    UNKNOWN = "unknown"


class LeadIntakeRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)

    service_type: ServiceType

    location: str = Field(
        min_length=1,
        max_length=250,
    )

    urgency: Urgency

    message: str | None = Field(
        default=None,
        max_length=2000,
    )

    source: LeadSource

    preferred_contact: PreferredContact = PreferredContact.UNKNOWN

    consent_marketing: bool = False

    @model_validator(mode="after")
    def validate_contact_method(self):
        """
        Lead must contain at least one usable contact method.
        """
        if not self.email and not self.phone:
            raise ValueError(
                "At least one contact method is required: email or phone."
            )

        return self


class NormalizedLead(BaseModel):
    full_name: str

    email_raw: str | None
    email_normalized: str | None

    phone_raw: str | None
    phone_e164: str | None

    service_type: ServiceType
    location_raw: str
    urgency: Urgency

    message: str | None

    source: LeadSource
    preferred_contact: PreferredContact
    consent_marketing: bool


class LeadIntakeResponse(BaseModel):
    success: bool

    intake_id: str
    correlation_id: str

    status: str

    normalized_lead: NormalizedLead

    replayed: bool = False
    duplicate: bool = False

    duplicate_match_fields: list[str] = []

    message: str