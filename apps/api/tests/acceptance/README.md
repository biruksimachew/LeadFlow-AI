# LeadFlow AI Acceptance Tests

The acceptance suite is split into two layers.

## Core acceptance

Core tests exercise deterministic LeadFlow behavior without requiring
external provider calls.

Run:

```bash
pytest tests/acceptance/test_core.py -v
```

The core suite checks:

1. demo configuration
2. event idempotency
3. duplicate customer detection
4. warm qualification
5. unsupported-service review
6. service-area hard disqualification
7. HOT qualification
8. provisioned routing

## Live integration acceptance

Live tests use the published n8n workflow and configured external
integrations. They can create synthetic HubSpot records and send
provider test communications.

Run only in the synthetic demo environment:

```bash
RUN_LIVE_ACCEPTANCE=1 pytest tests/acceptance/test_live_integrations.py -v
```

The live suite checks:

9. n8n happy path
10. n8n duplicate branch
11. n8n review branch
12. HubSpot replay safety
13. communication replay safety
14. cold-lead consent protection
15. outside-area n8n stop behavior

All test identities are synthetic and generated uniquely for each run.
