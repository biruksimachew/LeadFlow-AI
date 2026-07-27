-- ============================================================
-- LeadFlow AI
-- Portable local/demo seed
--
-- External provider identifiers are not hard-coded here.
-- After configuring HUBSPOT_DEFAULT_OWNER_ID, run:
--
--   docker compose exec api python scripts/provision_routing.py
-- ============================================================

insert into public.service_areas (
    zone_code,
    display_name,
    postal_codes,
    active
)
values (
    'north',
    'North District',
    array['10021','10022','10023'],
    true
)
on conflict (zone_code)
do update set
    display_name = excluded.display_name,
    postal_codes = excluded.postal_codes,
    active = true,
    updated_at = now();

insert into public.qualification_config (
    config_key,
    config_value,
    description,
    active
)
values
(
    'service_area_points',
    '{"approved": 25, "outside": 0}'::jsonb,
    'Points awarded for approved service area.',
    true
),
(
    'supported_service_points',
    '{"supported": 20, "unsupported": 0}'::jsonb,
    'Points awarded for supported service type.',
    true
),
(
    'urgency_points',
    '{"emergency":15,"within_24_hours":12,"within_7_days":8,"planning":3,"unknown":0}'::jsonb,
    'Qualification points by urgency.',
    true
),
(
    'data_completeness_points',
    '{"complete":10,"mostly_complete":7,"partial":3}'::jsonb,
    'Points based on lead data completeness.',
    true
),
(
    'source_quality_points',
    '{"website":5,"meta":4,"manual":3,"csv_test":3}'::jsonb,
    'Configurable source quality score.',
    true
),
(
    'score_bands',
    '{"hot_min":80,"warm_min":55,"cold_min":30}'::jsonb,
    'Qualification score thresholds.',
    true
),
(
    'timeline_readiness_points',
    '{"explicit_appointment":10,"near_term":7,"exploratory":2,"none":0}'::jsonb,
    'Deterministic timeline/readiness scoring.',
    true
)
on conflict (config_key)
do update set
    config_value = excluded.config_value,
    description = excluded.description,
    active = true,
    updated_at = now();

insert into public.message_templates (
    template_key,
    channel,
    subject_template,
    body_template,
    active
)
values
(
    'hot_email',
    'email',
    'We received your {service_type} request',
    $template$
Hi {first_name},

We received your {service_type} request.

You can choose a suitable appointment time here:

{booking_url}

A NorthStar Home Services team member will review your request.

This message does not guarantee pricing or service availability.
$template$,
    true
),
(
    'warm_email',
    'email',
    'We received your {service_type} request',
    $template$
Hi {first_name},

We received your {service_type} request.

Our team will review the information you submitted and follow up if anything else is required.

Thank you,
NorthStar Home Services
$template$,
    true
),
(
    'cold_nurture_email',
    'email',
    'Following up on your {service_type} request',
    $template$
Hi {first_name},

Thanks for contacting NorthStar Home Services about {service_type}.

When you are ready to continue, you can submit a new request or reply to our team.

To stop receiving follow-up messages, use the opt-out option provided by the communication channel.
$template$,
    true
),
(
    'hot_sms',
    'sms',
    null,
    'NorthStar Home Services received your {service_type} request. Booking link: {booking_url}. Pricing and availability are confirmed only after review.',
    true
),
(
    'hot_slack_channel',
    'slack',
    null,
    'HOT LEAD | Score: {score} | Service: {service_type} | Location: {location} | Source: {source} | Owner: {owner_id} | Lead: {lead_url}',
    true
),
(
    'hot_slack_owner',
    'slack',
    null,
    'You have been assigned a HOT lead. Score: {score} | Service: {service_type} | Location: {location} | Lead: {lead_url}',
    true
)
on conflict (template_key)
do update set
    channel = excluded.channel,
    subject_template = excluded.subject_template,
    body_template = excluded.body_template,
    active = true,
    updated_at = now();

insert into public.routing_config (
    config_key,
    fallback_owner_id,
    fallback_queue,
    timezone
)
values (
    'default',
    'UNCONFIGURED',
    'general',
    'America/New_York'
)
on conflict (config_key)
do nothing;

insert into public.routing_rules (
    rule_key,
    name,
    priority,
    service_type,
    service_zone,
    weekdays,
    start_time,
    end_time,
    timezone,
    target_owner_id,
    target_queue,
    available,
    active
)
values
(
    'north_plumbing_primary',
    'North District - Plumbing',
    200,
    'plumbing',
    'north',
    array[1,2,3,4,5,6,7]::smallint[],
    '00:00',
    '23:59:59',
    'America/New_York',
    'UNCONFIGURED',
    'plumbing',
    true,
    false
),
(
    'north_electrical_primary',
    'North District - Electrical',
    200,
    'electrical',
    'north',
    array[1,2,3,4,5,6,7]::smallint[],
    '00:00',
    '23:59:59',
    'America/New_York',
    'UNCONFIGURED',
    'electrical',
    true,
    false
),
(
    'north_hvac_primary',
    'North District - HVAC',
    200,
    'hvac',
    'north',
    array[1,2,3,4,5,6,7]::smallint[],
    '00:00',
    '23:59:59',
    'America/New_York',
    'UNCONFIGURED',
    'hvac',
    true,
    false
),
(
    'north_appliance_repair_primary',
    'North District - Appliance Repair',
    200,
    'appliance_repair',
    'north',
    array[1,2,3,4,5,6,7]::smallint[],
    '00:00',
    '23:59:59',
    'America/New_York',
    'UNCONFIGURED',
    'appliance_repair',
    true,
    false
)
on conflict (rule_key)
do update set
    name = excluded.name,
    priority = excluded.priority,
    service_type = excluded.service_type,
    service_zone = excluded.service_zone,
    weekdays = excluded.weekdays,
    start_time = excluded.start_time,
    end_time = excluded.end_time,
    timezone = excluded.timezone,
    target_queue = excluded.target_queue,
    available = true;
