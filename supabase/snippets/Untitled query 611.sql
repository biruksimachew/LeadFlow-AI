select *
from public.workflow_events
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'olivia.review03@example.com'
)
and event_type = 'HUMAN_OVERRIDE';