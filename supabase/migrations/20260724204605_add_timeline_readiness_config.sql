insert into public.qualification_config (
    config_key,
    config_value,
    description,
    active
)
values (
    'timeline_readiness_points',
    '{
        "explicit_appointment": 10,
        "near_term": 7,
        "exploratory": 2,
        "none": 0
    }'::jsonb,
    'Deterministic timeline/readiness scoring.',
    true
)
on conflict (config_key)
do update set
    config_value = excluded.config_value,
    description = excluded.description,
    active = true;