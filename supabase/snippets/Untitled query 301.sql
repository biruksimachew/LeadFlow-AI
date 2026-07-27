select
    channel,
    template_key,
    count(*)
from public.communications
where lead_id = (
    select id
    from public.leads
    where email_normalized =
        'maya.review04@example.com'
)
group by
    channel,
    template_key;