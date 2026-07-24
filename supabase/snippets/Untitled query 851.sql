insert into public.routing_config (
    config_key,
    fallback_owner_id,
    fallback_queue
)
values (
    'default',
    '96064820',
    'general'
);


insert into public.routing_rules (
    name,
    priority,
    service_type,
    service_zone,
    weekdays,
    start_time,
    end_time,
    target_owner_id,
    target_queue
)
values
(
    'North Plumbing',
    100,
    'plumbing',
    'north',
    '{1,2,3,4,5}',
    '08:00',
    '18:00',
    '96064820',
    'plumbing'
),
(
    'North Electrical',
    100,
    'electrical',
    'north',
    '{1,2,3,4,5}',
    '08:00',
    '18:00',
    '96064820',
    'electrical'
),
(
    'North HVAC',
    100,
    'hvac',
    'north',
    '{1,2,3,4,5}',
    '08:00',
    '18:00',
    '96064820',
    'hvac'
),
(
    'North Appliance',
    100,
    'appliance_repair',
    'north',
    '{1,2,3,4,5}',
    '08:00',
    '18:00',
    '96064820',
    'appliance'
);