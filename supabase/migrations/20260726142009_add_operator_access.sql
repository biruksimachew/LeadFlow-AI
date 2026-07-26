create table if not exists public.operator_profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    role text not null default 'OPERATOR'
        check (
            role in (
                'ADMIN',
                'OPERATOR',
                'REVIEWER'
            )
        ),
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


alter table public.operator_profiles
enable row level security;


create or replace function public.is_leadflow_operator()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.operator_profiles
        where user_id = auth.uid()
          and is_active = true
    );
$$;


revoke all
on function public.is_leadflow_operator()
from public;

grant execute
on function public.is_leadflow_operator()
to authenticated;


drop policy if exists
"operator can read own profile"
on public.operator_profiles;

create policy
"operator can read own profile"
on public.operator_profiles
for select
to authenticated
using (
    user_id = auth.uid()
);


alter table public.leads
enable row level security;

drop policy if exists
"operators can read leads"
on public.leads;

create policy
"operators can read leads"
on public.leads
for select
to authenticated
using (
    public.is_leadflow_operator()
);


alter table public.workflow_events
enable row level security;

drop policy if exists
"operators can read workflow events"
on public.workflow_events;

create policy
"operators can read workflow events"
on public.workflow_events
for select
to authenticated
using (
    public.is_leadflow_operator()
);


alter table public.appointments
enable row level security;

drop policy if exists
"operators can read appointments"
on public.appointments;

create policy
"operators can read appointments"
on public.appointments
for select
to authenticated
using (
    public.is_leadflow_operator()
);


alter table public.communications
enable row level security;

drop policy if exists
"operators can read communications"
on public.communications;

create policy
"operators can read communications"
on public.communications
for select
to authenticated
using (
    public.is_leadflow_operator()
);


grant select
on public.operator_profiles
to authenticated;

grant select
on public.leads
to authenticated;

grant select
on public.workflow_events
to authenticated;

grant select
on public.appointments
to authenticated;

grant select
on public.communications
to authenticated;