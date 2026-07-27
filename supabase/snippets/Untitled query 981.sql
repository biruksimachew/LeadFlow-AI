select
    full_name,
    source,
    service_type,
    status,
    score,
    assigned_owner_id,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where email_normalized =
    'delivered+leadflow-manual02@resend.dev';