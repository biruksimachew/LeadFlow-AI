alter table public.operator_profiles
drop constraint if exists operator_profiles_role_check;


alter table public.operator_profiles
add constraint operator_profiles_role_check
check (
    role in (
        'ADMIN',
        'OPERATIONS_MANAGER',
        'OPERATOR',
        'REVIEWER'
    )
);