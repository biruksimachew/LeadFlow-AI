select
    id,
    full_name,
    assigned_owner_id,
    assigned_queue,
    routing_rule_id
from public.leads
where assigned_owner_id = 'YOUR_HUBSPOT_OWNER_ID';