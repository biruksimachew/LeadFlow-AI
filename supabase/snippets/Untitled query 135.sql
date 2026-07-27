select
    config_key,
    fallback_owner_id,
    fallback_queue
from public.routing_config
where fallback_owner_id = 'YOUR_HUBSPOT_OWNER_ID';