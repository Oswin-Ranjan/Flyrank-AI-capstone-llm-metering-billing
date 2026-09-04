# EVIDENCE

## Definition of Done Evidence

Evidence will be added continuously as each requirement is completed.

---

## Phase 1

### Project starts successfully

Status: In progress

Planned proof:
- `docker compose up --build`
- `GET /health`
- FastAPI `/docs` loads successfully

### Database schema

Status: Complete

Command:

```bash
alembic upgrade head
```

Evidence:
- Alembic migration completed successfully.
- PostgreSQL tables verified:
  - tenants
  - plans
  - subscriptions
  - usage_events
  - stripe_events
  - alembic_version

### Seed Data

Status: Complete

Command:

```bash
python -m app.seed
```

Evidence:
- Free plan created
- Pro plan created
- Demo tenant created
- Demo tenant assigned a Free subscription

Terminal output:

  Database seeded successfully.
  
  Free Plan ID: 1
  
  Pro Plan ID: 2
  
  Demo Tenant ID: 1

### Design Document  

Status: Complete

Evidence:
- DESIGN.md documents:
  - Problem
  - Scope
  - Plans and quotas
  - Data model
  - API surface
  - Idempotency strategy
  - Quota strategy
  - Layered architecture
  - Explicit non-goal

### API contract

Status: Complete

Defined API surface:
- POST /generate
- GET /usage
- POST /billing/checkout
- POST /webhooks/stripe

### Idempotency strategy

Status: Complete

Evidence:
- usage_events contains idempotency_key.
- A unique constraint exists on (tenant_id, idempotency_key).
- Detailed behavior is documented in DESIGN.md.

### Idempotency

Status: Complete

Evidence:
- Repeated requests using the same Idempotency-Key returned the same usage event.
- The repeated request did not create a second usage event.
- Database verification showed only one usage event for the repeated idempotency key.

### Quota enforcement

Status: Complete

Evidence:
- Quota is checked before recording a new usage event.
- Usage is calculated against the tenant's active subscription plan.
- Requests exceeding the plan limit return "429 Too Many Requests".
- Rejected requests are not recorded as usage events.

### Cost calculation

Status: Not started

### Stripe integration

Status: Not started

### Testing

Status: Not started

---

## Phase 2

### Idempotent usage metering

Status: Complete


Manual API test:

POST /generate

X-Tenant-ID: <tenant_id>

Idempotency-Key: api-test-001


Request:

{
  "usage_type": "API_CALL",
  "quantity": 1
}

Evidence:
- First request successfully created a usage event.
- Sending the same request again with the same "Idempotency-Key" returned the same usage event.
- The database contained only one usage event for the repeated request.
- Using a different idempotency key created a separate usage event.

### Quota enforcement

Status: Complete

Manual boundary test:

Temporary Free-plan API quota:

API call limit = 3

Test sequence:

Request 1 → Allowed

Request 2 → Allowed

Request 3 → Allowed

Request 4 → Rejected

Evidence:
- Request taking usage exactly to the configured limit was allowed.
- Request exceeding the configured limit returned HTTP 429.
- The response explained:
  - current usage
  - requested quantity
  - usage type
  - configured limit
- The request exceeding the limit was not recorded as a usage event.

After testing, the Free-plan API call limit was restored to: 1000 API calls/month

### API Validation

Status: Complete

Evidence:
- Zero quantity → 422
- Negative quantity → 422
- Invalid usage type → 422
- Missing Idempotency-Key → 422
- Nonexistent tenant → 404

### Usage Summary

Status: Complete

Endpoint: GET /usage

Planned evidence:
- `GET /usage` returns API call usage.
- `GET /usage` returns AI token usage.
- Plan limits are returned.
- Current cost is returned.
- API calls and AI token usage are tracked independently.

### Automated Idempotency Tests

Status: Complete

Evidence:
- Same idempotency key creates one event.
- Different idempotency keys create different events.
- Repeated API request returns the original usage event.

### Automated Quota Tests

Status: Complete

Evidence:
- Usage just below the limit.
- Usage exactly at the limit.
- Usage above the limit.
- Over-limit request returns 429.

### Cost calculation

Status: Not started

### Stripe integration

Status: Not started

### Testing

Status: In Progress

Current manual tests completed:
- GET /health
- POST /generate normal request
- Repeated POST /generate with same idempotency key
- POST /generate with different idempotency key
- AI token metering
- Quota boundary test
- Over-quota 429 test
- Tenant lookup validation

Remaining:
- Complete automated pytest coverage.
- Complete API validation tests.
- Complete usage summary tests.
- Complete Stripe tests.
- Complete cost calculation tests.

---

## Phase 3 — Stripe Integration (Razorpay Alternative)

### Razorpay Test Mode

Status: Complete

Evidence:

- Razorpay Test Mode configured.
- Pro subscription plan created.
- Razorpay test credentials stored in environment variables.
- Razorpay webhook configured with a public HTTPS endpoint.

### Subscription Creation

Status: Complete

Evidence:

- `POST /billing/subscription` successfully created a Razorpay subscription.
- Razorpay returned a subscription ID.
- Subscription initially entered the `created` state.

### Webhook Signature Verification

Status: Complete

Evidence:

- Unsigned webhook request returned HTTP 400.
- Invalid webhook signatures are rejected before event processing.

### Subscription Webhook Processing

Status: Complete

Evidence:

- `subscription.authenticated` webhook received successfully.
- `subscription.activated` webhook received successfully.
- Both events were stored in `payment_events`.

### Free → Pro Synchronization

Status: Complete

Evidence:

- Tenant initially had a Free subscription.
- Razorpay subscription was successfully authorized.
- `subscription.activated` webhook was received.
- Pro subscription became active.
- `GET /usage` returned Pro limits:
  - API calls: 10000
  - AI tokens: 1000000

### Webhook Deduplication

Status: Complete

Evidence:

- Webhook event IDs are stored in `payment_events`.
- Repeated delivery of the same provider event ID is ignored.
- Duplicate processing returns the documented duplicate response.

### Subscription State Synchronization

Status: Complete

Evidence:

- `subscription.updated` updates the local subscription state.
- `subscription.cancelled` updates the local subscription state.

### Final Acceptance Probe

Status: Complete

```text
Free tenant
    ↓
Razorpay subscription
    ↓
Authorization
    ↓
Verified webhook
    ↓
subscription.activated
    ↓
Pro subscription active
    ↓
GET /usage shows Pro limits