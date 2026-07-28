-- Complete automatic retry, dead-letter recovery, and alert delivery.

alter table public.workflow_errors
add column if not exists retry_started_at timestamptz;

alter table public.workflow_errors
add column if not exists retry_worker_id text;

alter table public.workflow_errors
add column if not exists dead_letter_alerted_at timestamptz;

alter table public.workflow_errors
add column if not exists dead_letter_alert_error text;

alter table public.workflow_errors
add column if not exists dead_letter_alert_attempt_count integer
not null default 0
check (dead_letter_alert_attempt_count >= 0);

alter table public.workflow_errors
add column if not exists dead_letter_alert_next_at timestamptz;


create index if not exists
workflow_errors_due_retry_idx
on public.workflow_errors (
    next_retry_at,
    created_at
)
where (
    status = 'OPEN'
    and retryable = true
);


create index if not exists
workflow_errors_stale_retry_idx
on public.workflow_errors (
    retry_started_at
)
where status = 'RETRYING';


create index if not exists
workflow_errors_due_alert_idx
on public.workflow_errors (
    dead_letter_alert_next_at,
    created_at
)
where (
    status = 'DEAD_LETTER'
    and dead_letter_alerted_at is null
);


-- Existing retryable errors become immediately eligible.
update public.workflow_errors
set
    next_retry_at = coalesce(
        next_retry_at,
        now()
    ),
    updated_at = now()
where status = 'OPEN'
and retryable = true;


-- Existing non-retryable failures are final failures.
update public.workflow_errors
set
    status = 'DEAD_LETTER',
    next_retry_at = null,
    retry_started_at = null,
    retry_worker_id = null,
    dead_letter_alert_next_at = coalesce(
        dead_letter_alert_next_at,
        now()
    ),
    updated_at = now()
where status = 'OPEN'
and retryable = false;


-- Existing dead letters are eligible for an alert unless already sent.
update public.workflow_errors
set dead_letter_alert_next_at = coalesce(
    dead_letter_alert_next_at,
    now()
)
where status = 'DEAD_LETTER'
and dead_letter_alerted_at is null;
