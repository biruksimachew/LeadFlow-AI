# LeadFlow AI Reliability Closeout

This pack completes automatic retry, exponential backoff, dead-letter handling, Slack final-failure alerts, worker health visibility, and deterministic acceptance coverage.

## Files included

- `.env.example`
- `supabase/migrations/20260728190000_complete_retry_dead_letter_recovery.sql`
- `apps/api/app/config.py`
- `apps/api/app/main.py`
- `apps/api/app/repositories/workflow_errors.py`
- `apps/api/app/routers/orchestration.py`
- `apps/api/app/routers/retries.py`
- `apps/api/app/services/continuation.py`
- `apps/api/app/services/workflow_failure.py`
- `apps/api/app/services/retry_worker.py`
- `apps/api/app/services/dead_letter_alerts.py`
- `apps/api/tests/acceptance/test_reliability.py`

## Behavior

1. A transient CRM or communications failure is recorded as `OPEN` with a scheduled retry.
2. The API background worker claims due retries with row locking and stale-claim recovery.
3. Retry delay uses exponential backoff and a configurable maximum.
4. Successful retry resolves the workflow error without repeating completed CRM or communication side effects.
5. The third failed retry moves the record to `DEAD_LETTER`.
6. Non-retryable failures move directly to `DEAD_LETTER`.
7. Dead letters produce a Slack alert. In local mock mode, the alert is recorded without contacting Slack.
8. Failed Slack alert delivery is retried separately.
9. Manual admin retry remains available.
10. Every state change is written to `workflow_events` with the correlation ID.

## Installation

Extract the pack into the repository root and allow matching files to be replaced.

Apply the migration:

```powershell
npx supabase migration up --local
```

Rebuild and recreate the API container:

```powershell
docker compose up -d --build --force-recreate api
```

The new settings have safe defaults. To make them explicit in the private root `.env`, add:

```env
SLACK_DEAD_LETTER_CHANNEL=leadflow-alerts
WORKFLOW_RETRY_ENABLED=true
WORKFLOW_RETRY_MAX_ATTEMPTS=3
WORKFLOW_RETRY_BASE_DELAY_SECONDS=30
WORKFLOW_RETRY_MAX_DELAY_SECONDS=300
WORKFLOW_RETRY_POLL_SECONDS=2
WORKFLOW_RETRY_BATCH_SIZE=10
WORKFLOW_RETRY_STALE_AFTER_SECONDS=120
WORKFLOW_DEAD_LETTER_ALERT_RETRY_SECONDS=60
```

Keep `COMMUNICATION_PROVIDER=mock` for the local portfolio demo. In live mode, the Slack bot token and a valid dead-letter channel are required for real alerts.

## Verification

Check worker health:

```powershell
Invoke-RestMethod "http://localhost:8000/health/retry-worker"
```

Expected:

```text
status  : ok
enabled : True
running : True
```

Run the core suite:

```powershell
docker compose exec api pytest tests/acceptance/test_core.py -q
```

Run all acceptance tests:

```powershell
docker compose exec -e RUN_LIVE_ACCEPTANCE=1 api pytest tests/acceptance -q
```

The previous suite contained 17 tests. This pack adds three reliability tests, so the target is:

```text
20 passed
```

The new tests prove:

- retryable failure receives a future `next_retry_at`;
- automatic retry resolves safely;
- exhausted retry reaches `DEAD_LETTER` and records a Slack alert.

Review the dashboard after the suite:

```text
http://localhost:3000/dashboard/errors
```

## Commit

After migration, worker health, and all tests are green:

```powershell
git add .
git commit -m "feat: complete retry and dead-letter recovery"
git push
```
