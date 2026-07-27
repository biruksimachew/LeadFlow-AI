select
    full_name,
    status,
    score,
    assigned_owner_id,
    assigned_queue,
    routing_rule_id,
    crm_sync_status
from public.leads
where email_normalized =
    'delivered+leadflow-repro01@resend.dev';