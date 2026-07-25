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
    'YOUR_HUBSPOT_OWNER_ID',
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
    'YOUR_HUBSPOT_OWNER_ID',
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
    'YOUR_HUBSPOT_OWNER_ID',
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
    'YOUR_HUBSPOT_OWNER_ID',
    'appliance'
);