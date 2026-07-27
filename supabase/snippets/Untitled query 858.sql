select
    rr.id,
    rr.service_type,
    rr.service_zone,
    rr.target_queue,
    count(l.id) as referenced_leads
from public.routing_rules rr
left join public.leads l
    on l.routing_rule_id = rr.id
group by
    rr.id,
    rr.service_type,
    rr.service_zone,
    rr.target_queue
order by
    rr.service_type,
    referenced_leads desc;