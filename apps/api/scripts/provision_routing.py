import asyncio
import os
import sys

import asyncpg

ROUTING_RULES = (
    ("north_plumbing_primary", "North District - Plumbing", "plumbing", "plumbing"),
    ("north_electrical_primary", "North District - Electrical", "electrical", "electrical"),
    ("north_hvac_primary", "North District - HVAC", "hvac", "hvac"),
    ("north_appliance_repair_primary", "North District - Appliance Repair", "appliance_repair", "appliance_repair"),
)

async def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    owner_id = os.getenv("HUBSPOT_DEFAULT_OWNER_ID")
    timezone = os.getenv("ROUTING_TIMEZONE", "America/New_York")

    if not database_url:
        print("ERROR: DATABASE_URL is not configured.", file=sys.stderr)
        return 2

    if not owner_id:
        print("ERROR: HUBSPOT_DEFAULT_OWNER_ID is not configured.", file=sys.stderr)
        return 2

    connection = await asyncpg.connect(database_url)

    try:
        async with connection.transaction():
            await connection.execute(
                '''
                insert into public.routing_config (
                    config_key,
                    fallback_owner_id,
                    fallback_queue,
                    timezone,
                    updated_at
                )
                values ('default', $1, 'general', $2, now())
                on conflict (config_key)
                do update set
                    fallback_owner_id = excluded.fallback_owner_id,
                    fallback_queue = excluded.fallback_queue,
                    timezone = excluded.timezone,
                    updated_at = now();
                ''',
                owner_id,
                timezone,
            )

            for rule_key, name, service_type, queue in ROUTING_RULES:
                await connection.execute(
                    '''
                    insert into public.routing_rules (
                        rule_key,
                        name,
                        priority,
                        service_type,
                        service_zone,
                        weekdays,
                        start_time,
                        end_time,
                        timezone,
                        target_owner_id,
                        target_queue,
                        available,
                        active
                    )
                    values (
                        $1,$2,200,$3,'north',
                        array[1,2,3,4,5,6,7]::smallint[],
                        '00:00','23:59:59',$4,$5,$6,true,true
                    )
                    on conflict (rule_key)
                    do update set
                        name = excluded.name,
                        priority = excluded.priority,
                        service_type = excluded.service_type,
                        service_zone = excluded.service_zone,
                        weekdays = excluded.weekdays,
                        start_time = excluded.start_time,
                        end_time = excluded.end_time,
                        timezone = excluded.timezone,
                        target_owner_id = excluded.target_owner_id,
                        target_queue = excluded.target_queue,
                        available = true,
                        active = true;
                    ''',
                    rule_key,
                    name,
                    service_type,
                    timezone,
                    owner_id,
                    queue,
                )

        print("Routing provisioned successfully.")
        print(f"Canonical rules: {len(ROUTING_RULES)}")
        print("Fallback queue: general")
        return 0
    finally:
        await connection.close()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
