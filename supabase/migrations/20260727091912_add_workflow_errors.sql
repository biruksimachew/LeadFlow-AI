create table if not exists public.workflow_errors (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid not null
        references public.leads(id)
        on delete cascade,

    correlation_id text not null,

    failed_action text not null,

    provider text,

    error_code text not null,

    error_message text,

    retryable boolean not null default false,

    retry_count integer not null default 0
        check (retry_count >= 0),

    status text not null default 'OPEN'
        check (
            status in (
                'OPEN',
                'RETRYING',
                'RESOLVED',
                'DEAD_LETTER'
            )
        ),

    next_retry_at timestamptz,

    last_retry_actor_id uuid,

    last_retry_reason text,

    resolution_notes text,

    created_at timestamptz not null default now(),

    updated_at timestamptz not null default now(),

    resolved_at timestamptz,

    unique (
        lead_id,
        failed_action
    )
);


create index if not exists
workflow_errors_status_created_idx
on public.workflow_errors (
    status,
    created_at desc
);


create index if not exists
workflow_errors_lead_id_idx
on public.workflow_errors (
    lead_id
);


alter table public.workflow_errors
enable row level security;


drop policy if exists
"operators can read workflow errors"
on public.workflow_errors;


create policy
"operators can read workflow errors"
on public.workflow_errors
for select
to authenticated
using (
    public.is_leadflow_operator()
);


grant select
on public.workflow_errors
to authenticated;


-- Backfill currently failed communications such as Lucas.
insert into public.workflow_errors (
    lead_id,
    correlation_id,
    failed_action,
    provider,
    error_code,
    error_message,
    retryable,
    status
)
select
    c.lead_id,
    c.correlation_id,
    'lead_continuation',
    c.provider,
    coalesce(
        c.error_code,
        'COMMUNICATION_FAILED'
    ),
    c.error_message,
    case
        when lower(
            coalesce(
                c.payload ->> 'retryable',
                'false'
            )
        ) = 'true'
        then true
        else false
    end,
    'OPEN'
from public.communications c
where c.status = 'FAILED'
on conflict (
    lead_id,
    failed_action
)
do nothing;