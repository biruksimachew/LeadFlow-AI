-- ============================================================
-- LeadFlow AI
-- Operational dashboard snapshot and filter indexes
-- ============================================================

create index if not exists idx_leads_source
on public.leads(source);

create index if not exists idx_leads_service_type
on public.leads(service_type);

create index if not exists idx_leads_assigned_owner_id
on public.leads(assigned_owner_id);

create index if not exists idx_leads_score
on public.leads(score);

create index if not exists idx_leads_updated_at
on public.leads(updated_at desc);

create index if not exists idx_appointments_status
on public.appointments(status);

create index if not exists idx_communications_status
on public.communications(status);


create or replace function public.get_leadflow_dashboard_snapshot()
returns jsonb
language plpgsql
stable
security invoker
set search_path = ''
as $$
declare
    snapshot jsonb;
begin
    if not public.is_leadflow_operator() then
        raise exception 'LeadFlow operator access required'
            using errcode = '42501';
    end if;

    select jsonb_build_object(
        'generated_at',
        now(),

        'total_leads',
        (
            select count(*)::integer
            from public.leads
        ),

        'new_leads_24h',
        (
            select count(*)::integer
            from public.leads
            where created_at >= now() - interval '24 hours'
        ),

        'latest_lead_at',
        (
            select max(created_at)
            from public.leads
        ),

        'status_breakdown',
        coalesce(
            (
                select jsonb_object_agg(
                    grouped.status,
                    grouped.total
                )
                from (
                    select
                        status,
                        count(*)::integer as total
                    from public.leads
                    group by status
                ) grouped
            ),
            '{}'::jsonb
        ),

        'source_breakdown',
        coalesce(
            (
                select jsonb_object_agg(
                    grouped.source,
                    grouped.total
                )
                from (
                    select
                        source,
                        count(*)::integer as total
                    from public.leads
                    group by source
                ) grouped
            ),
            '{}'::jsonb
        ),

        'service_breakdown',
        coalesce(
            (
                select jsonb_object_agg(
                    grouped.service_type,
                    grouped.total
                )
                from (
                    select
                        service_type,
                        count(*)::integer as total
                    from public.leads
                    group by service_type
                ) grouped
            ),
            '{}'::jsonb
        ),

        'score_breakdown',
        jsonb_build_object(
            'high',
            (
                select count(*)::integer
                from public.leads
                where score >= 80
            ),
            'medium',
            (
                select count(*)::integer
                from public.leads
                where score >= 55
                  and score < 80
            ),
            'low',
            (
                select count(*)::integer
                from public.leads
                where score < 55
            )
        ),

        'appointment_breakdown',
        coalesce(
            (
                select jsonb_object_agg(
                    grouped.status,
                    grouped.total
                )
                from (
                    select
                        status,
                        count(*)::integer as total
                    from public.appointments
                    group by status
                ) grouped
            ),
            '{}'::jsonb
        ),

        'open_workflow_errors',
        (
            select count(*)::integer
            from public.workflow_errors
            where status in (
                'OPEN',
                'RETRYING'
            )
        ),

        'dead_letter_workflow_errors',
        (
            select count(*)::integer
            from public.workflow_errors
            where status = 'DEAD_LETTER'
        ),

        'failed_crm_syncs',
        (
            select count(*)::integer
            from public.leads
            where crm_sync_status = 'FAILED'
        ),

        'failed_communications',
        (
            select count(*)::integer
            from public.communications
            where status = 'FAILED'
        ),

        'recent_leads',
        coalesce(
            (
                select jsonb_agg(
                    to_jsonb(recent_row)
                    order by recent_row.created_at desc
                )
                from (
                    select
                        id,
                        correlation_id,
                        full_name,
                        email_normalized,
                        service_type,
                        source,
                        score,
                        status,
                        created_at
                    from public.leads
                    order by created_at desc
                    limit 8
                ) recent_row
            ),
            '[]'::jsonb
        ),

        'oldest_review',
        (
            select to_jsonb(review_row)
            from (
                select
                    id,
                    correlation_id,
                    full_name,
                    service_type,
                    score,
                    status,
                    created_at
                from public.leads
                where status = 'REVIEW_REQUIRED'
                order by created_at asc
                limit 1
            ) review_row
        ),

        'oldest_workflow_error',
        (
            select to_jsonb(error_row)
            from (
                select
                    id,
                    lead_id,
                    correlation_id,
                    failed_action,
                    provider,
                    error_code,
                    status,
                    retry_count,
                    created_at
                from public.workflow_errors
                where status in (
                    'OPEN',
                    'RETRYING',
                    'DEAD_LETTER'
                )
                order by created_at asc
                limit 1
            ) error_row
        )
    )
    into snapshot;

    return snapshot;
end;
$$;


revoke all
on function public.get_leadflow_dashboard_snapshot()
from public;

grant execute
on function public.get_leadflow_dashboard_snapshot()
to authenticated;
