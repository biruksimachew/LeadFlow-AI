# LeadFlow AI

I built LeadFlow AI as a production-style portfolio project around a fictional home-services company called **NorthStar Home Services**.

The idea was to solve a real operational problem: leads can arrive from different sources, but once they enter the business they need to be validated, qualified, routed, synced to the CRM, followed up with, and tracked without creating duplicates or losing failures.

I also wanted to build something more realistic than a simple AI chatbot or one-off automation. LeadFlow is designed as a complete lead-operations system with business rules, AI assistance, human review, CRM integration, communications, retries, audit logs, and an internal operations dashboard.

> **Portfolio note:** NorthStar Home Services is fictional. This project is not presented as paid client work, and all customer/test data used in the repository and demos is synthetic.

---

## The Problem I Wanted to Solve

A service business might receive leads from:

- its website;
- Meta lead forms;
- staff entering leads manually;
- imported CSV files;
- other APIs or automation tools.

The problem starts after the lead arrives.

The business still needs to answer questions like:

- Is this lead valid?
- Have we already processed this exact event?
- Is this the same customer submitting again?
- Is the customer inside the service area?
- What service do they need?
- How urgent is the request?
- Should the lead be HOT, WARM, COLD, reviewed, or disqualified?
- Who should own it?
- Has the CRM already been updated?
- Has the customer already received a message?
- What happens if HubSpot, email, or another provider fails?
- Can an operator understand why the system made a decision?

LeadFlow AI is my answer to that workflow.

---

# How LeadFlow Works

```text
Website / Meta / Manual Entry / CSV
                 |
                 v
                n8n
                 |
                 v
              FastAPI
                 |
        +--------+--------+
        |                 |
        v                 v
 Validation          Deduplication
 Normalization       & Idempotency
        |                 |
        +--------+--------+
                 |
                 v
      Deterministic Qualification
                 |
                 v
           AI Assessment
                 |
                 v
         Human Review Gate
                 |
                 v
              Routing
                 |
                 v
           HubSpot CRM
                 |
                 v
      Communications / Booking
                 |
                 v
        Supabase PostgreSQL
                 |
                 v
        Operations Dashboard
```

n8n controls the workflow progression.

FastAPI owns the business rules, qualification logic, routing logic, provider integrations, and persistence.

I deliberately kept those responsibilities separate so important business decisions are not hidden inside visual n8n nodes.

---

# Lead Intake

All supported lead sources are converted into one canonical lead structure before the rest of the workflow runs.

The project currently includes:

- a public website service-request form;
- a synthetic Meta Lead Ads simulator;
- authenticated manual lead entry;
- CSV import;
- direct API intake.

The backend handles validation and normalization before anything continues downstream.

That includes things such as:

- email normalization;
- phone normalization;
- service type validation;
- urgency normalization;
- source tracking;
- original source-event preservation.

---

# Duplicate Detection and Idempotency

One area I paid particular attention to was duplicate processing.

I separated two different cases.

### Same event replayed

If the exact same source event or idempotency key is submitted again, LeadFlow returns the existing lead instead of creating another one.

### Same customer, new event

If the same customer submits a new event, the new source event can still be preserved while LeadFlow recognizes that the customer already exists.

That distinction matters because integrations are where duplicate automation becomes expensive.

A retry should not accidentally create:

- another HubSpot contact;
- another deal;
- another email;
- another appointment;
- another downstream workflow.

---

# Qualification Engine

I did not want AI deciding whether a lead is good or bad by itself.

The main qualification score is deterministic and driven by business configuration stored in PostgreSQL.

The current model considers:

| Factor | What it does |
| --- | --- |
| Service area | Approved areas receive points; outside area is a hard disqualifier |
| Supported service | Supported services continue; unsupported services require review |
| Urgency | Emergency and near-term requests score higher |
| Budget fit | Reserved for structured budget data |
| Timeline/readiness | Explicit booking or near-term intent increases the score |
| Completeness | Better lead information receives more weight |
| Source quality | Configurable source-specific score |

The main score bands are:

```text
80+      QUALIFIED_HOT
55-79    QUALIFIED_WARM
30-54    COLD
<30      REVIEW_REQUIRED
```

The configuration is stored in the database instead of being buried inside application code or n8n.

---

# Where AI Fits In

AI is an additional interpretation layer.

It is not the final authority.

The AI assessment produces structured information such as:

- intent;
- service category;
- urgency;
- confidence;
- summary;
- risk flags;
- explanation.

The project includes a deterministic mock AI provider for repeatable testing and an optional OpenAI provider adapter.

One rule I was strict about is that **AI cannot override hard business rules**.

For example:

```text
Customer is outside service area
              |
              v
        DISQUALIFIED
              |
       AI cannot change it
```

For non-hard-rule decisions, AI uncertainty can stop the automation.

For example:

```text
Deterministic score = 85
Result = QUALIFIED_HOT

AI confidence = 0.55
              |
              v
     LOW_AI_CONFIDENCE
              |
              v
      REVIEW_REQUIRED
```

I would rather send an uncertain lead to a person than pretend the model is confident when it is not.

---

# Human Review

Leads that need a decision from a person appear in the review queue.

Operators can inspect the lead together with:

- qualification score;
- score breakdown;
- AI assessment;
- AI confidence;
- review reasons;
- workflow history.

Authorized roles can apply an override.

The override is persisted in the audit trail before the workflow continues.

That gives the system a real human-in-the-loop path instead of simply logging an AI warning and continuing anyway.

---

# Routing

Qualified leads are assigned using database-backed routing rules.

Routing can consider:

- service type;
- service zone;
- weekday;
- business hours;
- timezone;
- owner availability;
- target queue;
- fallback assignment.

The repository keeps portable routing configuration separate from environment-specific HubSpot owner IDs.

A provisioning script applies the real owner configuration for the current environment.

---

# HubSpot Integration

LeadFlow integrates with HubSpot for contact and deal management.

The integration handles:

- contact lookup;
- email/phone deduplication;
- contact creation and update;
- deal creation and update;
- owner assignment;
- pipeline/stage mapping;
- LeadFlow-to-HubSpot ID persistence.

I also made the CRM stage replay-safe.

If a workflow is retried after HubSpot has already completed successfully, LeadFlow reuses the existing provider records instead of creating another contact or deal.

---

# Communications and Follow-Up

The action pipeline changes depending on the lead state.

For example:

**HOT leads** can trigger booking communication, email, SMS-adapter actions, and Slack alerts.

**WARM leads** can receive follow-up communication.

**COLD leads** can enter nurture only when marketing consent exists.

One acceptance case specifically checks:

```text
COLD lead
+
consent_marketing = false
              |
              v
     nurture evaluated
              |
              v
           SKIPPED
```

I chose to persist that skipped action rather than silently doing nothing.

That way an operator can see that LeadFlow considered the nurture action and intentionally blocked it because consent was missing.

---

# Failure Recovery

External services fail, so I did not want provider errors disappearing inside logs.

LeadFlow stores workflow failures in the database and exposes them through the operations dashboard.

Authorized users can retry failed actions.

The retry logic also tries not to repeat work that already succeeded.

For example:

```text
HubSpot sync        SUCCESS
Email               FAILED
                     |
                     v
                   Retry
                     |
          HubSpot is not recreated
                     |
                     v
              Email retried
```

That is especially important once several external systems are involved in the same workflow.

---

# Operations Dashboard

I built a Next.js dashboard for the operations side of the system.

It includes:

- authenticated operator login;
- lead overview;
- lead detail pages;
- workflow history;
- qualification details;
- CRM state;
- communications;
- appointments;
- review queue;
- human overrides;
- manual lead entry;
- CSV import;
- Meta lead simulator;
- workflow error queue;
- manual retries.

Authentication uses Supabase Auth, and database access is protected using Row Level Security.

The current roles are:

```text
ADMIN
OPERATIONS_MANAGER
OPERATOR
REVIEWER
```

---

# n8n Orchestration

n8n is the primary workflow orchestrator.

The production workflow is exported to:

```text
automation/n8n/workflows/LeadFlow AI - Lead Orchestrator v1.json
```

The main flow is:

```text
Webhook
   |
   v
Intake / Dedupe
   |
   +---- duplicate / stop
   |
   v
Qualification + AI
   |
   +---- review / disqualified / stop
   |
   v
Routing
   |
   v
CRM
   |
   v
Actions
   |
   v
Completed
```

FastAPI exposes individual orchestration stages so n8n can control progression without owning the actual business logic.

---

# Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- asyncpg
- httpx

### Frontend

- Next.js
- TypeScript
- React
- Tailwind CSS

### Database and Authentication

- Supabase
- PostgreSQL
- Supabase Auth
- Row Level Security

### Automation

- n8n
- Docker Compose

### Integrations

- HubSpot
- Resend
- Slack
- calendar webhooks
- optional OpenAI provider
- mock/test providers for reproducible development

---

# Testing

I built an automated acceptance suite rather than relying only on manual testing.

The current result is:

```text
Core acceptance tests       9 / 9
Live integration tests      7 / 7
---------------------------------
Total                      16 / 16
```

The suite covers things such as:

- configuration provisioning;
- exact-event idempotency;
- customer duplicate detection;
- WARM qualification;
- HOT qualification;
- low-confidence AI escalation;
- unsupported-service review;
- outside-area disqualification;
- routing;
- n8n happy path;
- duplicate workflow branch;
- review workflow branch;
- HubSpot replay safety;
- communication replay safety;
- consent-aware COLD nurture;
- prevention of downstream work for disqualified leads.

Core tests:

```bash
docker compose exec api pytest tests/acceptance/test_core.py -v
```

Full live suite:

```bash
docker compose exec -e RUN_LIVE_ACCEPTANCE=1 api pytest tests/acceptance -v
```

The live suite uses synthetic data but can interact with configured test integrations.

---

# Clean Rebuild Test

One thing I specifically wanted to prove before considering the core engineering complete was that the project did not depend on months of accumulated local database state.

I reset the local Supabase database completely and rebuilt the project using:

```text
Database reset
      |
      v
Migrations
      |
      v
seed.sql
      |
      v
Routing provisioning
      |
      v
Demo operator provisioning
      |
      v
Configuration checks
      |
      v
Acceptance suite
```

After the clean rebuild:

```text
16 / 16 acceptance tests passed
```

The demo Auth account was also recreated and successfully tested through the real Next.js login flow.

---

# Repository Structure

```text
leadflow-ai/
|
+-- apps/
|   |
|   +-- api/
|   |   +-- app/
|   |   +-- scripts/
|   |   +-- tests/
|   |
|   +-- web/
|       +-- src/
|
+-- automation/
|   +-- n8n/
|       +-- workflows/
|
+-- supabase/
|   +-- migrations/
|   +-- seed.sql
|
+-- docker-compose.yml
+-- .env.example
+-- README.md
```

---

# Running Locally

## 1. Configure environment variables

Create `.env` from:

```text
.env.example
```

Real credentials must stay outside Git.

---

## 2. Start Supabase

```bash
npx supabase start
```

---

## 3. Start the API and n8n

```bash
docker compose up -d --build
```

---

## 4. Provision environment-specific configuration

```bash
docker compose exec api python scripts/provision_routing.py
```

```bash
docker compose exec api python scripts/provision_demo_operator.py
```

Check the result:

```bash
docker compose exec api python scripts/check_demo_config.py
```

```bash
docker compose exec api python scripts/check_demo_operator.py
```

---

## 5. Start the web app

```bash
cd apps/web
npm install
npm run dev
```

Local services:

```text
Web dashboard:        http://localhost:3000
FastAPI docs:         http://localhost:8000/docs
n8n:                  http://localhost:5678
Supabase Studio:      http://localhost:54323
```

---

# Rebuilding the Local Database

The local Supabase database can be recreated from migrations and seed data.

> This deletes local development data.

```bash
npx supabase db reset --local
```

Then rerun the environment-specific provisioning:

```bash
docker compose exec api python scripts/provision_routing.py
docker compose exec api python scripts/provision_demo_operator.py
```

---

# Security Notes

A few security decisions built into the project:

- real `.env` files are ignored by Git;
- Supabase service credentials stay server-side;
- operator access requires authentication;
- RLS protects dashboard-accessible data;
- orchestration endpoints require an internal token;
- overrides and retries are role-restricted;
- hard qualification rules cannot be overridden by AI;
- calendar webhook handling supports signature verification;
- portfolio demos use synthetic customer data.

This is still a portfolio implementation, so a real production deployment would need environment-specific infrastructure, monitoring, backup, deployment, and security review.

---

# Why I Built This

I wanted this project to demonstrate more than calling an AI API or connecting two SaaS tools together.

The parts I cared about most were the problems that usually appear after the happy-path demo:

- duplicate events;
- retries;
- provider failures;
- uncertain AI output;
- human decisions;
- consent;
- auditability;
- external side effects;
- configuration;
- reproducibility.

That is the kind of automation work I want to focus on: systems that solve an operational problem and can still be understood and controlled when something goes wrong.