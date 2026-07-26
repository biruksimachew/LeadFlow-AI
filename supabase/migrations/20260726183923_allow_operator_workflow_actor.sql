alter table public.workflow_events
drop constraint if exists workflow_events_actor_type_check;


alter table public.workflow_events
add constraint workflow_events_actor_type_check
check (
    actor_type in (
        'system',
        'workflow',
        'user',
        'provider',
        'operator'
    )
);