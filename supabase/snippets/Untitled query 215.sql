insert into public.routing_config (
    config_key,
    fallback_owner_id,
    fallback_queue
)
values (
    'default',
    '96064820',
    'general'
)
on conflict (config_key)
do update set
    fallback_owner_id = excluded.fallback_owner_id,
    fallback_queue = excluded.fallback_queue;

