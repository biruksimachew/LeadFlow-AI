import asyncio
import os
import sys

import asyncpg

REQUIRED_QUALIFICATION_KEYS = {
    "service_area_points",
    "supported_service_points",
    "urgency_points",
    "data_completeness_points",
    "source_quality_points",
    "score_bands",
    "timeline_readiness_points",
}

REQUIRED_TEMPLATES = {
    "hot_email",
    "warm_email",
    "cold_nurture_email",
    "hot_sms",
    "hot_slack_channel",
    "hot_slack_owner",
}

REQUIRED_ROUTING_RULES = {
    "north_plumbing_primary",
    "north_electrical_primary",
    "north_hvac_primary",
    "north_appliance_repair_primary",
}

async def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    connection = await asyncpg.connect(database_url)
    errors: list[str] = []

    try:
        q_rows = await connection.fetch(
            "select config_key from public.qualification_config where active = true;"
        )
        q_keys = {row["config_key"] for row in q_rows}
        missing = REQUIRED_QUALIFICATION_KEYS - q_keys
        if missing:
            errors.append("Missing qualification config: " + ", ".join(sorted(missing)))

        t_rows = await connection.fetch(
            "select template_key from public.message_templates where active = true;"
        )
        t_keys = {row["template_key"] for row in t_rows}
        missing = REQUIRED_TEMPLATES - t_keys
        if missing:
            errors.append("Missing templates: " + ", ".join(sorted(missing)))

        r_rows = await connection.fetch(
            '''
            select rule_key, target_owner_id, active, available
            from public.routing_rules
            where rule_key = any($1::text[]);
            ''',
            list(REQUIRED_ROUTING_RULES),
        )
        routed = {
            row["rule_key"]
            for row in r_rows
            if row["active"] and row["available"] and row["target_owner_id"] != "UNCONFIGURED"
        }
        missing = REQUIRED_ROUTING_RULES - routed
        if missing:
            errors.append("Routing is not provisioned: " + ", ".join(sorted(missing)))

        fallback = await connection.fetchrow(
            "select fallback_owner_id from public.routing_config where config_key = 'default';"
        )
        if fallback is None or fallback["fallback_owner_id"] == "UNCONFIGURED":
            errors.append("Default fallback owner is not provisioned.")

        area = await connection.fetchrow(
            "select zone_code from public.service_areas where zone_code = 'north' and active = true;"
        )
        if area is None:
            errors.append("North service area is missing.")
    finally:
        await connection.close()

    if errors:
        print("Demo configuration check FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Demo configuration check PASSED.")
    print(" - service area: OK")
    print(" - qualification config: OK")
    print(" - message templates: OK")
    print(" - routing rules: OK")
    print(" - fallback owner: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
