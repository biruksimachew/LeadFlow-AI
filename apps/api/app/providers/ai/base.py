from dataclasses import dataclass
from typing import Protocol

from app.models.ai_assessment import AIAssessment
from app.models.lead import NormalizedLead


@dataclass(slots=True)
class AIContext:
    service_zone: str | None
    deterministic_score: int
    deterministic_status: str


@dataclass(slots=True)
class AIProviderResult:
    assessment: AIAssessment

    provider: str
    model: str
    prompt_version: str

    processing_time_ms: int


class AIProviderError(RuntimeError):

    def __init__(
        self,
        code: str,
        message: str,
    ):
        super().__init__(message)

        self.code = code
        self.message = message


class AIProvider(Protocol):

    async def assess(
        self,
        lead: NormalizedLead,
        context: AIContext,
    ) -> AIProviderResult:
        ...