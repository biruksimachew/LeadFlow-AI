from dataclasses import dataclass
from typing import Any
import json

import asyncpg

from app.models.lead import NormalizedLead


SUPPORTED_SERVICES = {
    "plumbing",
    "electrical",
    "hvac",
    "appliance_repair",
}


# ============================================================
# Timeline/readiness evidence
#
# These phrases do NOT provide score weights.
# The weights remain database configuration.
#
# This is deterministic text matching, not AI classification.
# ============================================================

EXPLICIT_APPOINTMENT_PHRASES = (
    "book an appointment",
    "book appointment",
    "schedule an appointment",
    "schedule appointment",
    "make an appointment",
    "set up an appointment",
    "book a visit",
    "schedule a visit",
    "book a service",
    "schedule service",
    "book someone",
    "schedule someone",
)

NEAR_TERM_PHRASES = (
    "as soon as possible",
    "asap",
    "right away",
    "immediately",
    "today",
    "tomorrow",
    "this week",
    "within 24 hours",
    "within a day",
    "next few days",
    "need someone soon",
    "need someone to come",
    "send someone",
    "come out soon",
)

EXPLORATORY_PHRASES = (
    "get a quote",
    "request a quote",
    "need a quote",
    "get an estimate",
    "need an estimate",
    "how much",
    "looking into",
    "thinking about",
    "considering",
    "planning",
    "wondering",
    "more information",
)


@dataclass
class QualificationResult:
    score: int
    status: str
    breakdown: dict[str, Any]
    hard_rule_result: str | None


# ============================================================
# Configuration
# ============================================================


async def load_qualification_config(
    connection: asyncpg.Connection,
) -> dict[str, Any]:

    rows = await connection.fetch(
        """
        select
            config_key,
            config_value
        from public.qualification_config
        where active = true;
        """
    )

    config: dict[str, Any] = {}

    for row in rows:

        value = row["config_value"]

        # asyncpg may return json/jsonb as a JSON string.
        if isinstance(value, str):
            value = json.loads(value)

        if not isinstance(value, dict):
            raise ValueError(
                f"Qualification config "
                f"'{row['config_key']}' "
                "must contain a JSON object."
            )

        config[row["config_key"]] = value

    return config


# ============================================================
# Service area
# ============================================================


async def determine_service_area(
    connection: asyncpg.Connection,
    location: str,
) -> tuple[bool, str | None]:
    """
    MVP service-area matching.

    Match configured postal codes against normalized
    location text.

    This can later be replaced by structured address
    parsing without changing the qualification engine.
    """

    rows = await connection.fetch(
        """
        select
            zone_code,
            postal_codes
        from public.service_areas
        where active = true;
        """
    )

    location_lower = location.lower()

    for row in rows:

        for postal_code in row["postal_codes"]:

            if postal_code in location_lower:
                return True, row["zone_code"]

    return False, None


# ============================================================
# Completeness
# ============================================================


def calculate_completeness(
    lead: NormalizedLead,
) -> str:

    important_values = [
        lead.full_name,
        (
            lead.email_normalized
            or lead.phone_e164
        ),
        lead.service_type,
        lead.location_raw,
        lead.urgency,
    ]

    populated = sum(
        value is not None
        and str(value).strip() != ""
        for value in important_values
    )

    if populated == len(important_values):
        return "complete"

    if populated >= 4:
        return "mostly_complete"

    return "partial"


# ============================================================
# Timeline / readiness
# ============================================================


def determine_timeline_readiness(
    lead: NormalizedLead,
) -> tuple[str, str]:
    """
    Determine readiness only from explicit customer wording.

    We deliberately do not infer readiness from urgency alone
    because urgency already receives its own score.

    Returns:
        (readiness_level, evidence)
    """

    message = (
        lead.message or ""
    ).strip().lower()

    if not message:
        return (
            "none",
            "no_message_evidence",
        )

    for phrase in EXPLICIT_APPOINTMENT_PHRASES:

        if phrase in message:
            return (
                "explicit_appointment",
                phrase,
            )

    for phrase in NEAR_TERM_PHRASES:

        if phrase in message:
            return (
                "near_term",
                phrase,
            )

    for phrase in EXPLORATORY_PHRASES:

        if phrase in message:
            return (
                "exploratory",
                phrase,
            )

    return (
        "none",
        "no_readiness_evidence",
    )


# ============================================================
# Score → status
# ============================================================


def status_from_score(
    score: int,
    score_bands: dict[str, int],
) -> str:

    if score >= score_bands["hot_min"]:
        return "QUALIFIED_HOT"

    if score >= score_bands["warm_min"]:
        return "QUALIFIED_WARM"

    if score >= score_bands["cold_min"]:
        return "COLD"

    return "REVIEW_REQUIRED"


# ============================================================
# Main deterministic qualification engine
# ============================================================


async def qualify_lead(
    connection: asyncpg.Connection,
    lead: NormalizedLead,
) -> QualificationResult:

    config = await load_qualification_config(
        connection
    )

    breakdown: dict[str, Any] = {}

    # --------------------------------------------------------
    # HARD RULE: service area
    # --------------------------------------------------------

    in_service_area, zone = (
        await determine_service_area(
            connection,
            lead.location_raw,
        )
    )

    service_area_points = (
        config["service_area_points"]["approved"]
        if in_service_area
        else config["service_area_points"]["outside"]
    )

    breakdown["service_area"] = {
        "points": service_area_points,
        "approved": in_service_area,
        "zone": zone,
    }

    if not in_service_area:

        return QualificationResult(
            score=service_area_points,
            status="DISQUALIFIED",
            breakdown=breakdown,
            hard_rule_result=(
                "OUTSIDE_SERVICE_AREA"
            ),
        )

    # --------------------------------------------------------
    # HARD RULE: supported service
    # --------------------------------------------------------

    supported_service = (
        lead.service_type.value
        in SUPPORTED_SERVICES
    )

    service_points = (
        config[
            "supported_service_points"
        ]["supported"]
        if supported_service
        else config[
            "supported_service_points"
        ]["unsupported"]
    )

    breakdown["supported_service"] = {
        "points": service_points,
        "supported": supported_service,
    }

    if not supported_service:

        return QualificationResult(
            score=service_area_points,
            status="REVIEW_REQUIRED",
            breakdown=breakdown,
            hard_rule_result=(
                "UNSUPPORTED_SERVICE"
            ),
        )

    # --------------------------------------------------------
    # Urgency
    # --------------------------------------------------------

    urgency_points = (
        config["urgency_points"].get(
            lead.urgency.value,
            0,
        )
    )

    breakdown["urgency"] = {
        "points": urgency_points,
        "value": lead.urgency.value,
    }

    # --------------------------------------------------------
    # Budget / fit
    #
    # No structured budget field currently exists.
    # Do not invent customer budget.
    # --------------------------------------------------------

    breakdown["budget_fit"] = {
        "points": 0,
        "reason": "not_provided",
    }

    budget_points = 0

    # --------------------------------------------------------
    # Timeline / readiness
    # --------------------------------------------------------

    (
        readiness_level,
        readiness_evidence,
    ) = determine_timeline_readiness(
        lead
    )

    readiness_config = config[
        "timeline_readiness_points"
    ]

    readiness_points = (
        readiness_config.get(
            readiness_level,
            0,
        )
    )

    breakdown["timeline_readiness"] = {
        "points": readiness_points,
        "level": readiness_level,
        "evidence": readiness_evidence,
    }

    # --------------------------------------------------------
    # Data completeness
    # --------------------------------------------------------

    completeness = calculate_completeness(
        lead
    )

    completeness_points = config[
        "data_completeness_points"
    ][completeness]

    breakdown["data_completeness"] = {
        "points": completeness_points,
        "level": completeness,
    }

    # --------------------------------------------------------
    # Source quality
    # --------------------------------------------------------

    source_points = config[
        "source_quality_points"
    ].get(
        lead.source.value,
        0,
    )

    breakdown["source_quality"] = {
        "points": source_points,
        "source": lead.source.value,
    }

    # --------------------------------------------------------
    # Final deterministic score
    # --------------------------------------------------------

    score = (
        service_area_points
        + service_points
        + urgency_points
        + budget_points
        + readiness_points
        + completeness_points
        + source_points
    )

    score = min(
        max(score, 0),
        100,
    )

    qualification_status = (
        status_from_score(
            score,
            config["score_bands"],
        )
    )

    return QualificationResult(
        score=score,
        status=qualification_status,
        breakdown=breakdown,
        hard_rule_result=None,
    )