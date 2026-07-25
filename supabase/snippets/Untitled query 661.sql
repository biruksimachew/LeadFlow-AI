select
    column_name,
    data_type,
    udt_name
from information_schema.columns
where table_schema = 'public'
and table_name = 'leads'
and column_name in (
    'status',
    'appointment_status'
);