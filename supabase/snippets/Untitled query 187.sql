select
    channel,
    template_key,
    provider,
    status,
    error_code,
    error_message
from public.communications
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'delivered+leadflow-warm02@resend.dev'
);