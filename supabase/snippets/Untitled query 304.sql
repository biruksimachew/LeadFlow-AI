select count(*)
from public.appointments
where lead_id = (
    select id
    from public.leads
    where email_normalized =
    'sophia.turner.hot02@example.com'
);