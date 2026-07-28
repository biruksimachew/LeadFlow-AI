# LeadFlow AI — Dashboard Operations Pack

This pack completes the operational dashboard and lead workspace without
rebuilding the existing lead detail, review, retry, authentication, manual
entry, or Meta simulator flows.

## Files

- `supabase/migrations/20260728170000_complete_dashboard_operations.sql`
- `apps/web/src/lib/data/dashboard.ts`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/lib/data/leads.ts`
- `apps/web/src/app/dashboard/leads/page.tsx`
- `apps/web/src/app/dashboard/loading.tsx`
- `apps/web/src/app/dashboard/error.tsx`

## What it adds

- One RLS-aware dashboard snapshot RPC rather than many browser-facing queries
- Filter indexes for source, service, owner, score, and update time
- Live dashboard metrics and distributions
- Recent leads and oldest unresolved work
- Real CRM, communication, and workflow error signals
- Correlation-ID search
- Status, service, source, score, owner, and date filters
- Newest, oldest, score, and update sorting
- Exact count and server-side pagination
- Clear-filter action
- Route-level loading and safe error states

The SQL function is `SECURITY INVOKER`, checks active operator access, and
continues to rely on the existing row-level security policies.
