select
    event_type,
    result,
    provider,
    error_code,
    error_message,
    details,
    created_at
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'maya.review04@example.com'
)
and (
    event_type like '%CONTINUATION%'
    or event_type like '%COMMUNICATION%'
)
order by created_at;