-- ============================================================
-- LeadFlow AI
-- Align intake persistence fields
-- ============================================================

alter table public.leads
add column preferred_contact text not null default 'unknown'
check (
    preferred_contact in (
        'email',
        'phone',
        'sms',
        'unknown'
    )
);


alter table public.lead_source_events
add column intake_id text;


-- Safe even if source events already exist.
update public.lead_source_events
set intake_id = 'legacy_' || id::text
where intake_id is null;


alter table public.lead_source_events
alter column intake_id set not null;


create unique index idx_lead_source_events_intake_id
on public.lead_source_events(intake_id);