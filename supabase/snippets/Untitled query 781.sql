select
    assigned_owner_id,
    count(*) as lead_count
from public.leads
where assigned_owner_id is not null
  and assigned_owner_id <> 'YOUR_HUBSPOT_OWNER_ID'
group by assigned_owner_id
order by lead_count desc;