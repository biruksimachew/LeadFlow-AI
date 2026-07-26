select
    event_type,
    actor_type,
    actor_id,
    result,
    details,
    created_at
from public.workflow_events
where lead_id = '4e9efb4e-67e9-4aa3-902f-9a839e6e680a'
order by created_at desc
limit 5;