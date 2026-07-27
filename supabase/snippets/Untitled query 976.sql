select
    event_type,
    result,
    error_code
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'delivered+leadflow-warm02@resend.dev'
)
and event_type like '%CONTINUATION%'
order by created_at;