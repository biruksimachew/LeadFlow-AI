select
    full_name,
    source,
    status,
    score,
    assigned_owner_id,
    assigned_queue,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where email_normalized =
    'delivered+leadflow-website01@resend.dev';