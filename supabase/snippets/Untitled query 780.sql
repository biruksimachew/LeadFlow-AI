select
    u.email,
    p.display_name,
    p.role,
    p.is_active
from public.operator_profiles p
join auth.users u
    on u.id = p.user_id
order by u.email;