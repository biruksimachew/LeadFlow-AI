from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.repositories.routing import (
    get_existing_assignment,
    load_fallback,
    load_routing_rules,
    persist_assignment,
)


@dataclass(slots=True)
class RoutingResult:
    owner_id: str
    queue: str | None
    routing_rule_id: str | None
    fallback: bool


async def route_lead(
    connection,
    *,
    lead_id,
    correlation_id: str,
    service_type: str,
    service_zone: str | None,
    now: datetime | None = None,
) -> RoutingResult:

    existing = await get_existing_assignment(
        connection,
        lead_id,
    )

    if existing:
        return RoutingResult(
            owner_id=existing["assigned_owner_id"],
            queue=existing["assigned_queue"],
            routing_rule_id=(
                str(existing["routing_rule_id"])
                if existing["routing_rule_id"]
                else None
            ),
            fallback=False,
        )

    rules = await load_routing_rules(connection)

    for rule in rules:

        if (
            rule["service_type"]
            and rule["service_type"] != service_type
        ):
            continue

        if (
            rule["service_zone"]
            and rule["service_zone"] != service_zone
        ):
            continue

        current = now or datetime.now(
            ZoneInfo(rule["timezone"])
        )

        local = current.astimezone(
            ZoneInfo(rule["timezone"])
        )

        if local.isoweekday() not in rule["weekdays"]:
            continue

        if not (
            rule["start_time"]
            <= local.time().replace(tzinfo=None)
            <= rule["end_time"]
        ):
            continue

        await persist_assignment(
            connection,
            lead_id=lead_id,
            correlation_id=correlation_id,
            owner_id=rule["target_owner_id"],
            queue=rule["target_queue"],
            routing_rule_id=rule["id"],
            fallback=False,
        )

        return RoutingResult(
            owner_id=rule["target_owner_id"],
            queue=rule["target_queue"],
            routing_rule_id=str(rule["id"]),
            fallback=False,
        )

    fallback = await load_fallback(connection)

    await persist_assignment(
        connection,
        lead_id=lead_id,
        correlation_id=correlation_id,
        owner_id=fallback["fallback_owner_id"],
        queue=fallback["fallback_queue"],
        routing_rule_id=None,
        fallback=True,
    )

    return RoutingResult(
        owner_id=fallback["fallback_owner_id"],
        queue=fallback["fallback_queue"],
        routing_rule_id=None,
        fallback=True,
    )