-- ============================================================
-- LeadFlow AI
-- Make low-intent valid leads reachable as COLD
-- ============================================================

update public.qualification_config
set
    config_value = '{
        "website": 5,
        "meta": 4,
        "manual": 0,
        "csv_test": 0
    }'::jsonb,
    description = (
        'Configurable source quality score. '
        'Manual and CSV sources receive no automatic '
        'source-quality bonus.'
    ),
    active = true,
    updated_at = now()
where config_key = 'source_quality_points';