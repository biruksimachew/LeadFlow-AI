# LeadFlow AI Requirements & Acceptance Matrix

> Baseline: **NorthStar Home Services — LeadFlow AI Client Project Brief v1.0 (22 July 2026)**  
> Portfolio simulation only. All test and demo data must remain synthetic.

## Status Legend

| Status | Meaning |
| --- | --- |
| ✅ Verified | Implemented and supported by an automated or completed manual acceptance check |
| 🟢 Implemented | Implementation exists, but the exact client acceptance condition still needs final evidence |
| 🟡 Partial | Part of the requirement exists, but a meaningful part is still missing or unverified |
| ⏳ Remaining | Not yet implemented or not yet demonstrated |
| ➖ Optional | SHOULD/MAY item not required for core MVP acceptance unless chosen for delivery |

# 1. Functional Requirements

| ID | Priority | Requirement | Status | Evidence / Notes | Remaining Work |
| --- | --- | --- | --- | --- | --- |
| FR-001 | MUST | Website submissions through authenticated/signed webhook with traceable intake ID | 🟡 Partial | Public Next.js request form sends server-side to production n8n intake; canonical intake produces correlation/lead IDs | Add or verify explicit signed/token-authenticated website webhook matching the brief |
| FR-002 | MUST | Meta Lead Ads adapter or realistic mock | ✅ Verified | Authenticated synthetic Meta simulator uses the production orchestration path | Live Meta connection is intentionally not claimed |
| FR-003 | MUST | Authenticated manual lead entry | ✅ Verified | Dashboard manual entry is behind operator authentication | Keep screenshot/demo evidence |
| FR-004 | MUST | CSV import with row-level success/error results | 🟢 Implemented | Dashboard CSV import uses canonical intake | Add final mixed success/error evidence |
| FR-005 | MUST | Reject or flag payload lacking both valid email and phone | 🟢 Implemented | Canonical validation exists | Add exact automated acceptance case |
| FR-006 | MUST | Normalize email, phone, service, source, urgency and location before scoring | ✅ Verified | Canonical normalization occurs before qualification | Add deeper unit coverage only if useful |
| FR-007 | MUST | Search local records and HubSpot by normalized email/phone | ✅ Verified | Local duplicate detection plus HubSpot lookup/upsert | Preserve live duplicate evidence |
| FR-008 | MUST | Link duplicate events and record CRM update/unchanged behavior | ✅ Verified | Same-event and same-customer cases are separate; source events are preserved; CRM replay is safe | Add polished evidence to final test report |
| FR-009 | MUST | Deterministic configurable qualification score + hard rules | ✅ Verified | DB-backed qualification configuration; WARM/HOT/outside/unsupported cases tested | None for MVP behavior |
| FR-010 | MUST | Structured AI assessment with model, prompt version, result, confidence and processing time | ✅ Verified | AI metadata persisted; mock and OpenAI adapters exist | Live OpenAI is optional for demo because mock is reproducible |
| FR-011 | MUST | Low-confidence/conflicting AI routes to human review | ✅ Verified | `<0.70` confidence and conflicts produce `REVIEW_REQUIRED` | Add explicit category-conflict test if desired |
| FR-012 | MUST | Idempotent HubSpot contact create/update | ✅ Verified | Lookup/upsert and provider identity persistence | Keep live evidence |
| FR-013 | MUST | One active deal per qualified service enquiry, associated to contact | ✅ Verified | Deal sync + association; replay preserves provider IDs | Keep CRM evidence |
| FR-014 | MUST | Set lifecycle/score/source/service/urgency/latest automation properties | 🟢 Implemented | HubSpot property provisioning and mappings exist | Final property-by-property check |
| FR-015 | MUST | Route using service category, area, business hours and availability | ✅ Verified | DB routing rules include service, zone, time window, timezone and availability | None for current deterministic rules |
| FR-016 | MUST | Default fallback owner/queue | 🟢 Implemented | `routing_config` + provisioner | Add explicit fallback test |
| FR-017 | MUST | Approved transactional email by qualification outcome | ✅ Verified | DB templates + Resend/live provider | Maintain synthetic recipient policy |
| FR-018 | MUST | Booking URL for hot leads included in approved message | 🟢 Implemented | Booking link persisted and inserted into HOT templates | Add exact HOT end-to-end evidence |
| FR-019 | MUST | SMS sandbox/test or exact mock payload/result | 🟢 Implemented | SMS mock/test path and HOT SMS template exist | Capture final mock payload or configure Twilio sandbox |
| FR-020 | MUST | Block nurture without marketing consent | ✅ Verified | Automated COLD/no-consent test persists nurture as `SKIPPED` | None |
| FR-021 | MUST | Slack alert for hot leads with required context | 🟢 Implemented | HOT Slack templates and live provider exist | Capture final HOT Slack evidence |
| FR-022 | MUST | Slack alert for dead-letter/final failed integrations | ⏳ Remaining / Verify | Workflow error and retry queue exists | Confirm or implement final-failure Slack alert |
| FR-023 | MUST | Dashboard pipeline counts, recent leads, source mix, score distribution, booking, failures and review | 🟡 Partial | Dashboard counts, leads, review and errors exist | Verify/add source mix, score distribution and booking summary |
| FR-024 | MUST | Searchable/filterable lead list | 🟡 Partial / Verify | Lead workspace exists | Verify required search, filters, sort and pagination; implement gaps |
| FR-025 | MUST | Detailed lead view with normalized/source data, score, AI, CRM, messages and audit | ✅ Verified | Lead detail includes qualification, audit, CRM, communications and appointments | Final screenshot evidence |
| FR-026 | MUST | Authorized score/owner/status override requiring reason | 🟢 Implemented | Role-restricted override path + audit exists | Verify all three override types in final test/demo |
| FR-027 | MUST | Retry failed action without unnecessarily rerunning completed work | ✅ Verified | Error queue + authorized retry; CRM and communication replay tests pass | None |
| FR-028 | MUST | Record booking confirmation, appointment time, calendar reference and notification state | 🟢 Implemented | Appointment table + signed booking webhook handling | Final booked-state dashboard evidence |
| FR-029 | MUST | Significant workflow event audit with timestamp, actor, correlation ID and result/error | ✅ Verified | Workflow events, overrides and failures are persisted | Final correlation-ID demo evidence |
| FR-030 | MUST | Scoring weights, service mappings, service areas, fallback owner and template identifiers as configuration | 🟡 Partial | Scoring, service areas, routing/fallback and message templates are persisted | `SUPPORTED_SERVICES` and some template-selection identifiers remain application constants; move to config or document waiver |
| FR-031 | SHOULD | Daily operational summary | ➖ Optional / Not built | — | Add only if useful for portfolio polish |
| FR-032 | SHOULD | CSV export of filtered leads/metrics | ➖ Optional / Not built | — | Add only if useful |

# 2. Non-Functional Requirements

| ID | Requirement | Status | Evidence / Notes | Remaining Work |
| --- | --- | --- | --- | --- |
| NFR-001 | Webhook acknowledgement within 3 seconds; long work asynchronous | 🟡 Partial / Unverified | Current n8n path works, but exact early-ack latency has not been proven | Measure acknowledgement and ensure response occurs before long CRM/comms work if needed |
| NFR-002 | Idempotent intake/CRM and exponential-backoff transient retries | 🟡 Partial | Intake and CRM idempotency are verified; manual recovery exists | Verify/configure exponential-backoff automatic retries |
| NFR-003 | Clean restart after interruption without losing accepted events | 🟢 Implemented / Needs fault test | Durable DB + persistent n8n volume + clean rebuild | Add interruption/restart acceptance test |
| NFR-004 | Maintainable provider/config architecture | 🟢 Mostly implemented | AI/CRM/communication adapters separated; DB-backed scoring/routing | Move remaining hard-coded business mappings to config |
| NFR-005 | Automated tests + repeatable seeded acceptance dataset | ✅ Verified | 9 core + 7 live tests pass after clean DB rebuild | Expand to remaining client scenarios |
| NFR-006 | Structured logs, correlation IDs, workflow status and visible failure queue | 🟡 Partial | Correlation IDs, audit events and error queue exist | Review structured logging and provider-health summary |
| NFR-007 | Keyboard controls, labels, contrast and non-color status indicators | ⏳ Unverified | UI exists | Perform explicit accessibility pass |
| NFR-008 | Docker local setup + environment configuration | ✅ Verified | Compose, `.env.example`, provisioning scripts and clean rebuild | Finish fresh-clone setup guide |
| NFR-009 | Architecture/setup/configuration/test documentation | 🟡 In progress | README + architecture + this matrix | Add configuration, troubleshooting, demo and acceptance docs |

# 3. Security & Privacy Controls

| Control | Status | Notes |
| --- | --- | --- |
| Secrets outside source control | ✅ Verified | `.env` and web local env are untracked; history scan returned no known secret patterns |
| `.env.example` without real credentials | ✅ Verified | Public example exists |
| Server-side authorization for operator actions | ✅ Verified | Supabase Auth + role checks |
| RLS for dashboard-readable operational data | ✅ Verified | RLS policies exist on operator-accessible tables |
| Internal orchestrator token | ✅ Verified | Staged orchestration endpoints require internal token |
| Signed/verified calendar webhook | ✅ Verified | Signed webhook handling implemented/tested |
| Authenticated/signed website webhook | 🟡 Partial | Public form is server-mediated, but the exact HMAC/signed intake contract still needs closing |
| Payload size limits | ⏳ Remaining / Verify | Not demonstrated |
| Rate limiting | ⏳ Remaining / Verify | Not demonstrated |
| Least-privilege provider scopes | 🟡 Manual review | Document provider scopes before handoff |
| HTTPS/secure cookies in hosted deployment | ➖ Environment-specific | Local portfolio environment is HTTP |
| Synthetic portfolio data | ✅ Verified | Acceptance/demo data is synthetic |
| Retention/deletion approach | ⏳ Remaining | Document production retention/deletion policy |
| No protected-attribute scoring | ✅ By design | Qualification model does not use protected attributes |

# 4. Client Acceptance Criteria

The original brief defines acceptance separately from the current 16-test project suite. A green project suite therefore does not automatically mean every original acceptance criterion is closed.

| AC | Criterion | Status | Evidence / Gap |
| --- | --- | --- | --- |
| AC-01 | Hot website lead -> local lead + HubSpot contact/deal + owner + Slack + email/SMS + booking | 🟡 Partial | Components exist, but one exact HOT website end-to-end acceptance case should be captured |
| AC-02 | Same idempotency key creates no duplicate records/messages | ✅ Verified | Core + n8n duplicate tests |
| AC-03 | Existing normalized email/phone links/updates instead of duplicate contact | ✅ Verified | Duplicate-customer + CRM identity logic |
| AC-04 | Outside-area lead stops safely with no unsupported promise | ✅ Verified | Core + n8n outside-area tests |
| AC-05 | Low-confidence/conflicting AI -> REVIEW_REQUIRED while preserving deterministic/source data | ✅ Verified | Dedicated low-confidence test + SQL verification |
| AC-06 | AI unavailable -> deterministic next state remains visible | 🟢 Implemented / Needs exact AC test | Fallback architecture exists | Add provider failure/invalid JSON test |
| AC-07 | HubSpot transient error retries safely without duplicate contact/deal | 🟡 Partial | Replay safety verified | Add controlled transient error + retry/backoff test |
| AC-08 | Non-management user cannot edit scoring or override another owner | 🟡 Partial | Override denial tested | Scoring/config UI permission path not fully represented |
| AC-09 | Override records old/new value, actor, timestamp and reason | ✅ Verified | `lead_overrides` + HUMAN_OVERRIDE audit |
| AC-10 | Booking webhook sets BOOKED and appears on dashboard | 🟢 Implemented | Signed webhook test exists | Add final dashboard e2e proof |
| AC-11 | No nurture without consent | ✅ Verified | Automated live acceptance |
| AC-12 | Test leads traceable end to end by correlation ID | 🟢 Implemented | Correlation IDs persist | Add final evidence packet |
| AC-13 | Dashboard shows pipeline, review, error and booking information | 🟡 Partial | Review/error/leads exist | Verify all executive metrics and booking summary |
| AC-14 | Clean local environment launches from docs/sample env | ✅ Verified | Fresh DB rebuild + reprovision + 16/16 + browser login |
| AC-15 | No real credentials or personal data in repository history | ✅ Verified | Git history and tracked-file scans completed |

# 5. Required Acceptance Dataset Coverage

| Brief Test | Scenario | Status |
| --- | --- | --- |
| T01 | Hot plumbing, valid zone, complete -> HOT + CRM + alert + booking | 🟡 Exact full end-to-end case still needed |
| T02 | Warm HVAC missing preferred time | 🟢 Equivalent WARM behavior tested; add exact dataset case |
| T03 | Duplicate email, new source event | ✅ Covered |
| T04 | Duplicate idempotency key | ✅ Covered |
| T05 | Outside service area | ✅ Covered |
| T06 | Unsupported service | ✅ Covered |
| T07 | Invalid email and no phone | 🟢 Implemented; add exact automated case |
| T08 | AI invalid JSON | 🟡 Add explicit failure/invalid-output test |
| T09-T11 | Provider/retry/review scenarios from brief | 🟡 Cross-check exact scenario coverage during final hardening |
| T12 | Calendar unavailable -> fallback/review; no invented slot | ⏳ Remaining |
| T13 | No marketing consent | ✅ Covered |
| T14 | Manual manager override | 🟢 Implemented; retain exact audit evidence |
| T15 | Booking confirmation webhook | 🟢 Implemented; add dashboard e2e evidence |
| T16 | 50-lead burst test | ⏳ Remaining |

# 6. Required Deliverables

| ID | Deliverable | Status |
| --- | --- | --- |
| D-01 | Source repository + clear commit history | ✅ |
| D-02 | n8n export + configuration documentation | 🟡 Export complete; configuration docs still being finalized |
| D-03 | Next.js dashboard + manual entry | ✅ |
| D-04 | Supabase schema/migrations/seed | ✅ |
| D-05 | Provider adapters | 🟢 Core adapters exist; final calendar/SMS documentation/evidence needed |
| D-06 | Docker / Compose local setup | ✅ |
| D-07 | Automated tests + documented acceptance procedure | 🟢 Suite exists; procedure docs being expanded |
| D-08 | Architecture + workflow diagrams | ✅ `docs/architecture.md` |
| D-09 | README + setup/config/troubleshooting | 🟡 README complete; deeper guides remaining |
| D-10 | Portfolio case study | ⏳ Remaining |
| D-11 | 90-150s demo + longer technical walkthrough | ⏳ Remaining |
| D-12 | Sanitized screenshots/sample data | ⏳ Remaining |

# 7. What the Current 16-Test Suite Proves

```text
Core tests:  9 / 9
Live tests:  7 / 7
Total:      16 / 16
```

The current suite proves:

- reproducible qualification configuration;
- same-event idempotency;
- same-customer duplicate detection;
- deterministic WARM qualification;
- unsupported-service review;
- outside-area disqualification;
- confident-AI HOT result;
- low-confidence AI review escalation;
- provisioned routing;
- n8n happy path;
- n8n duplicate branch;
- n8n review branch;
- CRM replay preserving provider IDs;
- communication replay without duplicate rows;
- consent-aware COLD nurture blocking;
- outside-area n8n stop with no downstream side effects.

That is strong engineering evidence, but it is intentionally listed separately from the full brief so the portfolio does not overstate what has been tested.

# 8. Remaining MVP Closure List

Before calling the original client brief fully accepted, close or explicitly waive:

1. signed/token-authenticated website intake webhook;
2. exact HOT website end-to-end acceptance flow;
3. dead-letter/final-failure Slack alert;
4. full dashboard check: search/filter/sort/pagination, source mix, score distribution and booking summary;
5. configuration coverage for remaining hard-coded business mappings;
6. explicit AI provider failure/invalid JSON test;
7. transient HubSpot failure + retry/backoff test;
8. calendar-unavailable fallback test;
9. performance: `<3s` acknowledgement and 50-lead burst test;
10. accessibility review;
11. payload-size/rate-limit/security hardening review;
12. retention/deletion documentation;
13. final setup/config/troubleshooting/acceptance docs;
14. sanitized screenshots, demo video and portfolio case study.

That list is the practical bridge between **“the system works”** and **“the original client brief is fully accepted.”**
