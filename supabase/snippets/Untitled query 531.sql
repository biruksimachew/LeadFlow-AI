select
    id,
    full_name,
    service_type,
    score,
    status
from public.leads
where email_normalized =
    'marcus.review01@example.com';