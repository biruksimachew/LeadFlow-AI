-- ============================================================
-- LeadFlow AI
-- Fix routing rule key uniqueness for ON CONFLICT support
-- ============================================================

drop index if exists public.uq_routing_rules_rule_key;

create unique index uq_routing_rules_rule_key
on public.routing_rules(rule_key);