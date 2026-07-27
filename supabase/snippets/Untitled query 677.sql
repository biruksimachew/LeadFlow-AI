select
    event_type,
    actor_type,
    actor_id,
    result,
    error_code,
    details,
    created_at
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'lucas.failure01@example.com'
)
and event_type like '%RETRY%'
order by created_at;