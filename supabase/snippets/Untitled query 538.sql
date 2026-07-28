select
    template_key,
    provider,
    status,
    consent_basis,
    payload
from public.communications
where lead_id = (
    select id
    from public.leads
    where email_normalized like
        'delivered+leadflow-cold-no-consent-%@resend.dev'
    order by created_at desc
    limit 1
);