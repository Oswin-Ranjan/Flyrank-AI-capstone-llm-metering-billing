# EVIDENCE

## Definition of Done Evidence

Evidence is recorded phase by phase based on the implemented and tested functionality.

---

## Phase 1 — Design & Project Setup

### Project starts successfully

**Status:** Complete

**Evidence:**
- Application starts successfully.
- PostgreSQL database starts through Docker.
- `GET /health` responds successfully.
- FastAPI `/docs` is available.

### Database Schema

**Status:** Complete

**Command:**
```bash
alembic upgrade head
```

**Evidence:**
- Alembic migration completed successfully.
- PostgreSQL tables verified:
  - `tenants`
  - `plans`
  - `subscriptions`
  - `usage_events`
  - `payment_events`
  - `alembic_version`

### Seed Data

**Status:** Complete

**Command:**
```bash
python -m app.seed
```

**Evidence:**
- Free plan created.
- Pro plan created.
- Demo tenant created.
- Demo tenant assigned a Free subscription.

**Seed output:**
```
Database seeded successfully.
Free Plan ID: 1
Pro Plan ID: 2
Demo Tenant ID: 1
```

### API Contract

**Status:** Complete

Defined API surface:

- `GET /health`
- `POST /generate`
- `GET /usage`
- `POST /billing/subscription`
- `POST /webhooks/razorpay`

### Idempotency Strategy

**Status:** Complete

**Evidence:**
- `usage_events` contains `idempotency_key`.
- A unique constraint exists on `(tenant_id, idempotency_key)`.
- Repeated requests using the same tenant and idempotency key return the existing usage event.

### Quota Strategy

**Status:** Complete

**Evidence:**
- Quota is checked before recording a new usage event.
- Usage is calculated against the tenant's active subscription plan.
- Requests exceeding the plan limit return HTTP `429 Too Many Requests`.
- Rejected requests are not recorded as usage events.

---

## Phase 2 — Core Billing Logic

### Idempotent Usage Metering

**Status:** Complete

**Manual API test:**

```
POST /generate

X-Tenant-ID: <tenant_id>
Idempotency-Key: api-test-001
```

**Request:**
```json
{
  "usage_type": "API_CALL",
  "quantity": 1
}
```

**Evidence:**
- First request successfully created a usage event.
- Sending the same request again with the same `Idempotency-Key` returned the same usage event.
- The database contained only one usage event for the repeated request.
- Using a different idempotency key created a separate usage event.

### Quota Enforcement

**Status:** Complete

**Manual boundary test:**

Temporary Free-plan API quota: 3 API calls

**Test sequence:**

| Request | Result |
| ------- | ------ |
| Request 1 | Allowed |
| Request 2 | Allowed |
| Request 3 | Allowed |
| Request 4 | Rejected |

**Evidence:**
- Request taking usage exactly to the configured limit was allowed.
- Request exceeding the configured limit returned HTTP `429`.
- The response contained the current usage, requested quantity, usage type, and configured limit.
- The request exceeding the limit was not recorded as a usage event.

After testing, the Free-plan API call limit was restored to 1000 API calls/month.

### API Validation

**Status:** Complete

**Evidence:**

| Case | Result |
| ---- | ------ |
| Zero quantity | `422` |
| Negative quantity | `422` |
| Invalid usage type | `422` |
| Missing `Idempotency-Key` | `422` |
| Nonexistent tenant | `404` |

### Usage Summary

**Status:** Complete

**Endpoint:** `GET /usage`

**Evidence:**
- Returns current API call usage.
- Returns current AI token usage.
- Returns plan limits.
- Returns calculated cost.
- API calls and AI token usage are tracked independently.

### Automated Idempotency Tests

**Status:** Complete

**Evidence:**
- Same idempotency key creates one event.
- Different idempotency keys create different events.
- Repeated API requests return the original usage event.

### Automated Quota Tests

**Status:** Complete

**Evidence:**
- Usage below the limit is accepted.
- Usage exactly at the limit is accepted.
- Usage above the limit is rejected.
- Over-limit requests return HTTP `429`.

---

## Phase 3 — Razorpay Integration

### Razorpay Test Mode

**Status:** Complete

**Evidence:**
- Razorpay Test Mode configured.
- Pro subscription plan created.
- Razorpay test credentials stored in environment variables.
- Razorpay webhook configured with a public HTTPS endpoint.

### Subscription Creation

**Status:** Complete

**Evidence:**
- `POST /billing/subscription` successfully created a Razorpay subscription.
- Razorpay returned a subscription ID.
- Subscription initially entered the `created` state.

### Webhook Signature Verification

**Status:** Complete

**Evidence:**
- Unsigned webhook request returned HTTP `400`.
- Invalid webhook signatures are rejected before event processing.
- Invalid webhook requests do not modify subscription state.

### Subscription Webhook Processing

**Status:** Complete

**Evidence:**
- `subscription.authenticated` webhook received successfully.
- `subscription.activated` webhook received successfully.
- Both events were stored in `payment_events`.

### Free → Pro Synchronization

**Status:** Complete

**Evidence:**
- Tenant initially had a Free subscription.
- Razorpay subscription was successfully authorized.
- `subscription.activated` webhook was received.
- Pro subscription became active.
- `GET /usage` returned Pro limits:
  - API calls: 10,000
  - AI tokens: 1,000,000

### Webhook Deduplication

**Status:** Complete

**Evidence:**
- Webhook event IDs are stored in `payment_events`.
- Repeated delivery of the same provider event ID is detected.
- Duplicate webhook processing is skipped.

### Subscription State Synchronization

**Status:** Complete

**Evidence:**
- `subscription.updated` updates the local subscription state.
- `subscription.cancelled` updates the local subscription state.
- Older active subscriptions are deactivated when a new subscription becomes active.

### Final Acceptance Probe

**Status:** Complete

```
Free Tenant
    ↓
Razorpay Subscription
    ↓
Authorization
    ↓
Verified Webhook
    ↓
subscription.activated
    ↓
Pro Subscription Active
    ↓
GET /usage shows Pro limits
```

---

## Phase 4 — Cost & Finalization

### Cost Calculation

**Status:** Complete

**Evidence:**
- API call cost is calculated using integer units.
- AI token costs distinguish fresh input, cached input, output, and reasoning tokens.
- Cached input uses a lower price than fresh input.
- Reasoning tokens use output pricing.
- Pinned pricing tests verify exact totals.

**Pinned pricing:**

| Unit | Cost (micro-dollars) |
| ---- | --------------------: |
| API call | 1,000 |
| Input token | 2 |
| Cached input token | 1 |
| Output token | 8 |
| Reasoning token | 8 |

### Pinned Cost Test

**Status:** Complete

**Test values:**

```
Input tokens = 400
Cached input tokens = 200
Output tokens = 300
Reasoning tokens = 100
```

**Calculation:**

```
400 × 2 = 800
200 × 1 = 200
300 × 8 = 2400
100 × 8 = 800

Total = 4200 micro-dollars
```

**Equivalent value:** `$0.0042`

### Usage Cost Rollup

**Status:** Complete

**Evidence:**
- `GET /usage` returns current monthly API usage.
- `GET /usage` returns current monthly AI token usage.
- `GET /usage` returns active plan limits.
- `GET /usage` returns calculated monthly cost.
- Retrying the same idempotent AI request does not increase usage or cost twice.

### Cost Tests

**Status:** Complete

**Command:**
```bash
pytest -v
```

**Evidence:**
- API call pricing test passed.
- AI token pricing test passed.
- Cached input pricing test passed.
- Reasoning token pricing test passed.
- Pinned cost test passed.
- Retry/double-cost test passed.
- Full test suite passed.

### Background Reconciliation

**Status:** Complete

**Evidence:**
- Usage reconciliation job implemented.
- Job recalculates costs from persisted usage events.
- Retry handling is included for transient failures.
- Permanent failures are logged after the retry limit.

---

## Phase 5 — Demo & Submission

### Final Demo Flow

**Status:** Complete

The final demonstration covers the core evaluation scenarios:

```
Health Check
    ↓
Usage Metering
    ↓
Idempotency Retry
    ↓
Quota Boundary
    ↓
AI Token Cost
    ↓
Razorpay Subscription
    ↓
Webhook Verification
    ↓
Duplicate Webhook
    ↓
GET /usage
```

### Repository Documentation

**Status:** Complete

Final repository documentation includes:

- `README.md`
- `BUILDLOG.md`
- `EVIDENCE.md`
- `capstone.yaml`

### Final Security Review

**Status:** Complete

**Evidence:**
- `.env` is excluded from version control.
- Secrets are configured through environment variables.
- Webhook signatures are verified.
- Tenant-specific data access is enforced.
- Provider event IDs are deduplicated.
- Database uniqueness constraints protect idempotent usage records.