insert into public.operator_profiles (
    user_id,
    display_name,
    role,
    is_active
)
select
    id,
    'Test Operator',
    'OPERATOR',
    true
from auth.users
where email = 'unauthorized@northstar.local'
on conflict (user_id)
do update set
    display_name = excluded.display_name,
    role = 'OPERATOR',
    is_active = true,
    updated_at = now();