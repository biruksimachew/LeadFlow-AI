select
    service_type,
    service_zone,
    target_queue,
    priority,
    count(*) as rule_count
from public.routing_rules
group by
    service_type,
    service_zone,
    target_queue,
    priority
having count(*) > 1;
