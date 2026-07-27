select
    full_name,
    assigned_owner_id,
    crm_sync_status,
    hubspot_contact_id,
    hubspot_deal_id
from public.leads
where crm_sync_status = 'SUCCEEDED'
  and assigned_owner_id is not null
order by updated_at desc
limit 10;