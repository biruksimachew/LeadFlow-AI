-- ============================================================
-- LeadFlow AI
-- Qualification engine foundation
-- ============================================================


-- ------------------------------------------------------------
-- Approved service areas
-- ------------------------------------------------------------

create table public.service_areas (
    id uuid primary key default gen_random_uuid(),

    zone_code text not null unique,
    display_name text not null,

    postal_codes text[] not null default '{}',

    active boolean not null default true,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Qualification configuration
--
-- JSONB keeps the rules editable without changing application
-- code every time the business changes a score.
-- ------------------------------------------------------------

create table public.qualification_config (
    id uuid primary key default gen_random_uuid(),

    config_key text not null unique,
    config_value jsonb not null,

    description text,

    active boolean not null default true,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ------------------------------------------------------------
-- Qualification results
-- ------------------------------------------------------------

create table public.qualification_results (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid not null
        references public.leads(id)
        on delete cascade,

    correlation_id text not null,

    deterministic_score smallint not null
        check (
            deterministic_score between 0 and 100
        ),

    score_breakdown jsonb not null,

    hard_rule_result text,

    qualification_status text not null
        check (
            qualification_status in (
                'QUALIFIED_HOT',
                'QUALIFIED_WARM',
                'COLD',
                'REVIEW_REQUIRED',
                'DISQUALIFIED'
            )
        ),

    created_at timestamptz not null default now()
);


create index idx_qualification_results_lead
    on public.qualification_results(lead_id);

create index idx_qualification_results_status
    on public.qualification_results(qualification_status);


-- ------------------------------------------------------------
-- Seed default qualification rules
-- ------------------------------------------------------------

insert into public.qualification_config (
    config_key,
    config_value,
    description
)
values

(
    'service_area_points',
    '{"approved": 25, "outside": 0}',
    'Points awarded for approved service area.'
),

(
    'supported_service_points',
    '{"supported": 20, "unsupported": 0}',
    'Points awarded for supported service type.'
),

(
    'urgency_points',
    '{
        "emergency": 15,
        "within_24_hours": 12,
        "within_7_days": 8,
        "planning": 3,
        "unknown": 0
    }',
    'Qualification points by urgency.'
),

(
    'data_completeness_points',
    '{
        "complete": 10,
        "mostly_complete": 7,
        "partial": 3
    }',
    'Points based on lead data completeness.'
),

(
    'source_quality_points',
    '{
        "website": 5,
        "meta": 4,
        "manual": 3,
        "csv_test": 3
    }',
    'Configurable source quality score.'
),

(
    'score_bands',
    '{
        "hot_min": 80,
        "warm_min": 55,
        "cold_min": 30
    }',
    'Qualification score thresholds.'
);