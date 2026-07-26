insert into public.operator_profiles (
    user_id,
    display_name,
    role
)
select
    id,
    'LeadFlow Operator',
    'ADMIN'
from auth.users
where email = 'operator@northstar.local'
on conflict (user_id)
do update set
    display_name = excluded.display_name,
    role = excluded.role,
    is_active = true,
    updated_at = now();