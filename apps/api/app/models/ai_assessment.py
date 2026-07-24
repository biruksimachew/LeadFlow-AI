from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AIIntent(str, Enum):
    REQUEST_SERVICE = "request_service"
    REQUEST_QUOTE = "request_quote"
    ASK_QUESTION = "ask_question"
    EXISTING_JOB = "existing_job"
    COMPLAINT = "complaint"
    OTHER = "other"


class AIServiceCategory(str, Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    APPLIANCE_REPAIR = "appliance_repair"
    OTHER = "other"
    UNKNOWN = "unknown"


class AIUrgency(str, Enum):
    EMERGENCY = "emergency"
    WITHIN_24_HOURS = "within_24_hours"
    WITHIN_7_DAYS = "within_7_days"
    PLANNING = "planning"
    UNKNOWN = "unknown"


class AIAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: AIIntent

    service_category: AIServiceCategory

    urgency: AIUrgency

    confidence: float = Field(
        ge=0,
        le=1,
    )

    summary: str = Field(
        min_length=1,
        max_length=300,
    )

    risk_flags: list[str] = Field(
        max_length=8,
    )

    explanation: str = Field(
        min_length=1,
        max_length=500,
    )


AI_ASSESSMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "request_service",
                "request_quote",
                "ask_question",
                "existing_job",
                "complaint",
                "other",
            ],
        },
        "service_category": {
            "type": "string",
            "enum": [
                "plumbing",
                "electrical",
                "hvac",
                "appliance_repair",
                "other",
                "unknown",
            ],
        },
        "urgency": {
            "type": "string",
            "enum": [
                "emergency",
                "within_24_hours",
                "within_7_days",
                "planning",
                "unknown",
            ],
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "summary": {
            "type": "string",
            "maxLength": 300,
        },
        "risk_flags": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "maxItems": 8,
        },
        "explanation": {
            "type": "string",
            "maxLength": 500,
        },
    },
    "required": [
        "intent",
        "service_category",
        "urgency",
        "confidence",
        "summary",
        "risk_flags",
        "explanation",
    ],
    "additionalProperties": False,
}