select
    full_name,
    source,
    service_type,
    status,
    score,
    assigned_owner_id,
    assigned_queue,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where email_normalized =
    'delivered+leadflow-finalmanual01@resend.dev';