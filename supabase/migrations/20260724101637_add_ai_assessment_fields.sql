-- ============================================================
-- LeadFlow AI
-- Structured AI assessment metadata
-- ============================================================

alter table public.qualification_results
add column ai_status text not null default 'PENDING'
check (
    ai_status in (
        'PENDING',
        'SUCCEEDED',
        'FAILED',
        'SKIPPED'
    )
);

alter table public.qualification_results
add column ai_provider text;

alter table public.qualification_results
add column ai_model text;

alter table public.qualification_results
add column prompt_version text;

alter table public.qualification_results
add column ai_result jsonb;

alter table public.qualification_results
add column ai_confidence numeric(4,3)
check (
    ai_confidence is null
    or (
        ai_confidence >= 0
        and ai_confidence <= 1
    )
);

alter table public.qualification_results
add column ai_processing_time_ms integer
check (
    ai_processing_time_ms is null
    or ai_processing_time_ms >= 0
);

alter table public.qualification_results
add column ai_review_reasons text[]
not null default '{}'::text[];

alter table public.qualification_results
add column ai_error_code text;

alter table public.qualification_results
add column ai_error_message text;

alter table public.qualification_results
add column ai_completed_at timestamptz;

alter table public.qualification_results
add column final_status text;

update public.qualification_results
set final_status = qualification_status
where final_status is null;

alter table public.qualification_results
alter column final_status set not null;

alter table public.qualification_results
add constraint qualification_final_status_check
check (
    final_status in (
        'QUALIFIED_HOT',
        'QUALIFIED_WARM',
        'COLD',
        'REVIEW_REQUIRED',
        'DISQUALIFIED'
    )
);