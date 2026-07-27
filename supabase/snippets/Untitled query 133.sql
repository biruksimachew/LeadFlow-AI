select
    channel,
    template_key,
    provider,
    status,
    error_code,
    error_message,
    payload
from public.communications
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'lucas.failure01@example.com'
);