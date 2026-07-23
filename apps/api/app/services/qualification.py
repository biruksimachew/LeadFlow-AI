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


@dataclass
class QualificationResult:
    score: int
    status: str
    breakdown: dict[str, Any]
    hard_rule_result: str | None


async def load_qualification_config(
    connection: asyncpg.Connection,
) -> dict[str, Any]:

    rows = await connection.fetch(
        """
        select config_key, config_value
        from public.qualification_config
        where active = true;
        """
    )

    config: dict[str, Any] = {}

    for row in rows:
        value = row["config_value"]

        # asyncpg may return json/jsonb as a JSON string.
        # Convert it into normal Python objects before use.
        if isinstance(value, str):
            value = json.loads(value)

        if not isinstance(value, dict):
            raise ValueError(
                f"Qualification config '{row['config_key']}' "
                "must contain a JSON object."
            )

        config[row["config_key"]] = value

    return config

async def determine_service_area(
    connection: asyncpg.Connection,
    location: str,
) -> tuple[bool, str | None]:
    """
    MVP service-area matching.

    Match configured postal codes against normalized
    location text.

    Later this can be replaced by structured address
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

    in_service_area, zone = await determine_service_area(
        connection,
        lead.location_raw,
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
            hard_rule_result="OUTSIDE_SERVICE_AREA",
        )

    # --------------------------------------------------------
    # Supported service
    # --------------------------------------------------------

    supported_service = (
        lead.service_type.value in SUPPORTED_SERVICES
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
            hard_rule_result="UNSUPPORTED_SERVICE",
        )

    # --------------------------------------------------------
    # Urgency
    # --------------------------------------------------------

    urgency_points = config["urgency_points"].get(
        lead.urgency.value,
        0,
    )

    breakdown["urgency"] = {
        "points": urgency_points,
        "value": lead.urgency.value,
    }

    # --------------------------------------------------------
    # Data completeness
    # --------------------------------------------------------

    completeness = calculate_completeness(lead)

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
    # Budget + readiness
    #
    # No reliable structured information exists yet.
    # The client brief explicitly says not to invent values.
    # --------------------------------------------------------

    breakdown["budget_fit"] = {
        "points": 0,
        "reason": "not_provided",
    }

    breakdown["timeline_readiness"] = {
        "points": 0,
        "reason": "not_structured_yet",
    }

    score = (
        service_area_points
        + service_points
        + urgency_points
        + completeness_points
        + source_points
    )

    score = min(max(score, 0), 100)

    qualification_status = status_from_score(
        score,
        config["score_bands"],
    )

    return QualificationResult(
        score=score,
        status=qualification_status,
        breakdown=breakdown,
        hard_rule_result=None,
    )