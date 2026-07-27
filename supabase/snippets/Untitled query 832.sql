select
    id,
    service_type,
    service_zone,
    target_owner_id
from public.routing_rules
order by priority desc;