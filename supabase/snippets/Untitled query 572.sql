select count(*) as remaining_placeholders
from public.routing_rules
where target_owner_id = 'YOUR_HUBSPOT_OWNER_ID';