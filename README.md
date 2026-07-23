# LeadFlow AI

AI-assisted lead qualification, CRM routing, appointment booking, and sales-operations automation system.

> **Portfolio Simulation**
>
> LeadFlow AI is a production-style portfolio project built for the fictional company **NorthStar Home Services**. It is not presented as paid client work, and all demonstration data is synthetic.

## What LeadFlow AI Does

LeadFlow AI is designed to automate the operational lifecycle of incoming service leads:

Lead Intake → Validation → Normalization → Duplicate Detection → Qualification → CRM Routing → Customer Communication → Appointment Booking → Audit & Operations Monitoring

The goal is not to build a chatbot demo, but a dependable lead-processing system where every important action is traceable.

## Current Progress

### Lead Intake Foundation

- [x] Dockerized FastAPI service
- [x] Swagger/OpenAPI documentation
- [x] Canonical lead schema
- [x] Input validation
- [x] Email and phone normalization
- [x] Supabase PostgreSQL persistence
- [x] Source-event preservation
- [x] Workflow audit logging
- [x] Transactional database writes
- [x] Idempotent intake handling
- [x] Local duplicate detection
- [ ] Deterministic qualification engine
- [ ] AI-assisted qualification
- [ ] HubSpot CRM integration
- [ ] Lead routing
- [ ] Email/SMS automation
- [ ] Slack alerts
- [ ] Appointment automation
- [ ] Operations dashboard
- [ ] Retry and dead-letter workflows

## Architecture

Current implementation:

```text
Client / Lead Source
        |
        v
     FastAPI
        |
        +-- Validation
        +-- Normalization
        +-- Idempotency
        +-- Duplicate Detection
        |
        v
Supabase PostgreSQL
        |
        +-- leads
        +-- lead_source_events
        +-- workflow_events