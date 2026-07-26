select
    id,
    full_name,
    service_type,
    score,
    status,
    created_at
from public.leads
where status = 'REVIEW_REQUIRED'
order by created_at desc;