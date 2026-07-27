-- ============================================================
-- LeadFlow AI
-- Stable routing rule identifiers for reproducible provisioning
-- ============================================================

alter table public.routing_rules
add column if not exists rule_key text;

create unique index if not exists
    uq_routing_rules_rule_key
on public.routing_rules(rule_key)
where rule_key is not null;
