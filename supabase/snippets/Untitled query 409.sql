select
    id,
    service_type,
    service_zone,
    target_owner_id,
    target_queue,
    priority,
    active,
    available
from public.routing_rules
where target_owner_id = 'YOUR_HUBSPOT_OWNER_ID';