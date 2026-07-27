select
    event_type,
    provider,
    result,
    error_code,
    error_message,
    details,
    created_at
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'lucas.failure01@example.com'
)
and (
    event_type like '%COMMUNICATION%'
    or event_type like '%CONTINUATION%'
)
order by created_at;