-- ============================================================
-- LeadFlow AI
-- Migration: Lead intake foundation
-- ============================================================


-- ------------------------------------------------------------
-- Canonical lead record
-- ------------------------------------------------------------

create table public.leads (
    id uuid primary key default gen_random_uuid(),

    correlation_id text not null unique,

    source text not null
        check (
            source in (
                'website',
                'meta',
                'manual',
                'csv_test'
            )
        ),

    source_record_id text,

    full_name text not null,

    email_normalized text,
    phone_e164 text,

    service_type text not null
        check (
            service_type in (
                'plumbing',
                'electrical',
                'hvac',
                'appliance_repair',
                'other'
            )
        ),

    location_text text not null,
    service_zone text,

    urgency text not null
        check (
            urgency in (
                'emergency',
                'within_24_hours',
                'within_7_days',
                'planning',
                'unknown'
            )
        ),

    message text,

    consent_marketing boolean not null default false,

    score smallint not null default 0
        check (score between 0 and 100),

    status text not null default 'RECEIVED'
        check (
            status in (
                'RECEIVED',
                'INVALID',
                'DUPLICATE',
                'QUALIFIED_HOT',
                'QUALIFIED_WARM',
                'COLD',
                'REVIEW_REQUIRED',
                'DISQUALIFIED',
                'BOOKING_SENT',
                'APPOINTMENT_BOOKED',
                'CONTACTED',
                'CLOSED_WON',
                'CLOSED_LOST'
            )
        ),

    assigned_owner_id text,

    hubspot_contact_id text,
    hubspot_deal_id text,

    appointment_status text not null default 'none'
        check (
            appointment_status in (
                'none',
                'link_sent',
                'booked',
                'cancelled',
                'completed'
            )
        ),

    last_error_code text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Source intake events
--
-- Every submission gets its own source event.
-- This becomes crucial later for duplicates and idempotency.
-- ------------------------------------------------------------

create table public.lead_source_events (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid references public.leads(id)
        on delete set null,

    correlation_id text not null,

    source text not null
        check (
            source in (
                'website',
                'meta',
                'manual',
                'csv_test'
            )
        ),

    source_record_id text,

    idempotency_key text not null unique,

    ingestion_status text not null default 'RECEIVED'
        check (
            ingestion_status in (
                'RECEIVED',
                'PROCESSED',
                'INVALID',
                'DUPLICATE',
                'FAILED'
            )
        ),

    raw_payload jsonb not null default '{}'::jsonb,
    normalized_payload jsonb,

    received_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Append-only workflow / audit timeline
-- ------------------------------------------------------------

create table public.workflow_events (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid references public.leads(id)
        on delete set null,

    correlation_id text not null,

    event_type text not null,

    actor_type text not null default 'system'
        check (
            actor_type in (
                'system',
                'workflow',
                'user',
                'provider'
            )
        ),

    actor_id text,

    provider text,

    result text not null
        check (
            result in (
                'started',
                'succeeded',
                'failed',
                'skipped',
                'retried'
            )
        ),

    details jsonb not null default '{}'::jsonb,

    error_code text,
    error_message text,

    created_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------

create index idx_leads_email_normalized
    on public.leads(email_normalized);

create index idx_leads_phone_e164
    on public.leads(phone_e164);

create index idx_leads_status
    on public.leads(status);

create index idx_leads_created_at
    on public.leads(created_at desc);

create index idx_source_events_correlation
    on public.lead_source_events(correlation_id);

create index idx_workflow_events_lead
    on public.workflow_events(lead_id);

create index idx_workflow_events_correlation
    on public.workflow_events(correlation_id);

create index idx_workflow_events_created_at
    on public.workflow_events(created_at desc);


-- ------------------------------------------------------------
-- Automatically maintain leads.updated_at
-- ------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


create trigger set_leads_updated_at
before update on public.leads
for each row
execute function public.set_updated_at();