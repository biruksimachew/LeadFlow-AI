create table public.message_templates (
    template_key text primary key,
    channel text not null
        check (channel in ('email', 'sms', 'slack')),
    subject_template text,
    body_template text not null,
    active boolean not null default true,
    updated_at timestamptz not null default now()
);


create table public.communications (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid not null
        references public.leads(id)
        on delete cascade,

    correlation_id text not null,

    channel text not null
        check (channel in ('email', 'sms', 'slack')),

    template_key text not null,

    recipient text,

    provider text not null,

    provider_message_id text,

    status text not null
        check (
            status in (
                'SENT',
                'FAILED',
                'SKIPPED'
            )
        ),

    consent_basis text,

    payload jsonb,

    error_code text,
    error_message text,

    created_at timestamptz not null default now(),
    sent_at timestamptz,

    unique (
        lead_id,
        channel,
        template_key
    )
);


create table public.appointments (
    id uuid primary key default gen_random_uuid(),

    lead_id uuid not null unique
        references public.leads(id)
        on delete cascade,

    correlation_id text not null,

    provider text not null,

    booking_url text not null,

    external_appointment_id text,

    start_at timestamptz,
    end_at timestamptz,
    timezone text,

    status text not null
        check (
            status in (
                'LINK_SENT',
                'BOOKED',
                'CANCELLED',
                'COMPLETED'
            )
        ),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


insert into public.message_templates (
    template_key,
    channel,
    subject_template,
    body_template
)
values

(
    'hot_email',
    'email',
    'We received your {service_type} request',
    'Hi {first_name},

We received your {service_type} request.

You can choose a suitable appointment time here:

{booking_url}

A NorthStar Home Services team member will review your request.

This message does not guarantee pricing or service availability.'
),

(
    'warm_email',
    'email',
    'We received your {service_type} request',
    'Hi {first_name},

We received your {service_type} request.

Our team will review the information you submitted and follow up if anything else is required.

Thank you,
NorthStar Home Services'
),

(
    'cold_nurture_email',
    'email',
    'Following up on your {service_type} request',
    'Hi {first_name},

Thanks for contacting NorthStar Home Services about {service_type}.

When you are ready to continue, you can submit a new request or reply to our team.

To stop receiving follow-up messages, use the opt-out option provided by the communication channel.'
),

(
    'hot_sms',
    'sms',
    null,
    'NorthStar Home Services received your {service_type} request. Booking link: {booking_url}. Pricing and availability are confirmed only after review.'
),

(
    'hot_slack_channel',
    'slack',
    null,
    'HOT LEAD | Score: {score} | Service: {service_type} | Location: {location} | Source: {source} | Owner: {owner_id} | Lead: {lead_url}'
),

(
    'hot_slack_owner',
    'slack',
    null,
    'You have been assigned a HOT lead. Score: {score} | Service: {service_type} | Location: {location} | Lead: {lead_url}'
);