-- ============================================================
-- LeadFlow AI
-- CRM synchronization state
-- ============================================================

alter table public.leads
add column crm_sync_status text
not null default 'PENDING'
check (
    crm_sync_status in (
        'PENDING',
        'IN_PROGRESS',
        'SUCCEEDED',
        'FAILED',
        'SKIPPED'
    )
);

alter table public.leads
add column crm_last_synced_at timestamptz;

alter table public.leads
add column crm_last_error_code text;


create index idx_leads_crm_sync_status
on public.leads(crm_sync_status);