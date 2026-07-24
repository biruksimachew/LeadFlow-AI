create table public.routing_rules (
    id uuid primary key default gen_random_uuid(),

    name text not null,

    priority integer not null default 100,

    service_type text,
    service_zone text,

    weekdays smallint[] not null
        default '{1,2,3,4,5}',

    start_time time not null default '08:00',
    end_time time not null default '18:00',

    timezone text not null
        default 'America/New_York',

    target_owner_id text not null,
    target_queue text,

    available boolean not null default true,
    active boolean not null default true,

    created_at timestamptz not null default now()
);


create table public.routing_config (
    config_key text primary key,

    fallback_owner_id text not null,
    fallback_queue text,

    timezone text not null
        default 'America/New_York',

    updated_at timestamptz not null default now()
);


alter table public.leads
add column assigned_queue text;

alter table public.leads
add column routing_rule_id uuid
references public.routing_rules(id);

alter table public.leads
add column routed_at timestamptz;