create table if not exists public.lead_overrides (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid not null
        references public.leads(id)
        on delete cascade,

    actor_user_id uuid not null,

    actor_email text,

    actor_role text not null,

    previous_values jsonb not null,
    new_values jsonb not null,

    reason text not null
        check (char_length(trim(reason)) >= 10),

    created_at timestamptz not null default now()
);


create index if not exists
lead_overrides_lead_id_created_at_idx
on public.lead_overrides (
    lead_id,
    created_at desc
);


alter table public.lead_overrides
enable row level security;


drop policy if exists
"operators can read lead overrides"
on public.lead_overrides;


create policy
"operators can read lead overrides"
on public.lead_overrides
for select
to authenticated
using (
    public.is_leadflow_operator()
);


grant select
on public.lead_overrides
to authenticated;