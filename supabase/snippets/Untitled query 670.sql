select
    event_type,
    actor_type,
    provider,
    result,
    error_code,
    details,
    created_at
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'delivered+leadflow-recovery01@resend.dev'
)
order by created_at;