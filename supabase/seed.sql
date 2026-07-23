insert into public.leads (
    correlation_id,
    source,
    source_record_id,
    full_name,
    email_normalized,
    phone_e164,
    service_type,
    location_text,
    service_zone,
    urgency,
    message,
    consent_marketing,
    score,
    status
)
values (
    'corr_seed_plumbing_001',
    'website',
    'seed-web-001',
    'Daniel Brooks',
    'daniel.brooks@example.test',
    '+12025550184',
    'plumbing',
    'North District, 10021',
    'north',
    'within_24_hours',
    'Kitchen pipe is leaking.',
    true,
    0,
    'RECEIVED'
);