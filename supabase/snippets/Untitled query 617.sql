select
    full_name,
    assigned_owner_id,
    assigned_queue,
    routing_rule_id,
    routed_at,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where email_normalized =
'mason.carter.routing02@example.com';