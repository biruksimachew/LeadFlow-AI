begin;

-- Replace the old placeholder on every routing rule.
update public.routing_rules
set target_owner_id = '96064820'
where target_owner_id = 'YOUR_HUBSPOT_OWNER_ID';


-- Replace the fake fallback owner as well.
update public.routing_config
set
    fallback_owner_id = '96064820',
    updated_at = now()
where config_key = 'default';


-- Remove only the unused duplicate rules.
-- We keep the referenced plumbing/electrical rules,
-- plus one canonical HVAC and appliance rule.

delete from public.routing_rules
where id in (
    'b5d6e69e-83bf-4f82-af1a-226ced779a17', -- duplicate plumbing
    'b7909652-2a41-431c-95b9-62a7e7e3c457', -- duplicate electrical
    'a6b4ba25-4900-4691-bdbd-7aa2f21fafe0', -- duplicate HVAC
    '3c55b6fa-c566-456a-b4cd-7cac93befa29'  -- duplicate appliance
);

commit;