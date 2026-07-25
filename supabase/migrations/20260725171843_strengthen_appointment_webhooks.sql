alter table public.appointments
add column attendee_email text;

alter table public.appointments
add column provider_payload jsonb;

alter table public.appointments
add column webhook_received_at timestamptz;


create unique index
uq_appointments_external_appointment_id
on public.appointments(external_appointment_id)
where external_appointment_id is not null;