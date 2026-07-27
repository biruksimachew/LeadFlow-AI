select
    full_name,
    status,
    score,
    assigned_owner_id,
    assigned_queue,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where id =
    'ba0828b9-acb7-4bef-988b-8a197a23c4b5';