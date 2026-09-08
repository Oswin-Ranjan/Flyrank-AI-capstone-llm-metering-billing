# FlyRank Usage Metering & Billing Engine

A backend service for SaaS usage metering, quota enforcement, cost calculation, and subscription synchronization.

## Problem

SaaS applications need to know:

1. How much a customer has used.
2. What that usage costs.
3. Whether the customer has reached their plan limits.

This project implements those capabilities with an emphasis on correctness under retries, quota boundaries, and webhook duplication.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Razorpay Test Mode
- Pytest

## Core Scope

- Free and Pro plans
- API call metering
- AI token metering
- Idempotent usage recording
- Monthly quota enforcement
- Usage and cost reporting
- Razorpay subscription integration
- Razorpay webhook verification
- Duplicate webhook prevention
- Usage reconciliation background job

## Architecture

```
Client → FastAPI → Services → PostgreSQL
```

The main services are Metering, Quota, Usage, Billing, and Cost.

```
Razorpay → Webhook → Signature Verification → Event Deduplication → Subscription Synchronization
```

## Plans

| Plan | API Calls / Month | AI Tokens / Month |
| ---- | -----------------: | -----------------: |
| Free |               1,000 |             100,000 |
| Pro  |              10,000 |           1,000,000 |

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Health check |
| POST | `/generate` | Record billable usage |
| GET | `/usage` | View current usage and cost |
| POST | `/billing/subscription` | Create a subscription |
| POST | `/webhooks/razorpay` | Process Razorpay webhooks |

For `/generate`, the required headers are:

```
X-Tenant-ID: <tenant_id>
Idempotency-Key: <unique_key>
```

**Example API-call request:**

```json
{
  "usage_type": "API_CALL",
  "quantity": 1
}
```

**Example AI-token request:**

```json
{
  "usage_type": "AI_TOKEN",
  "quantity": 1000,
  "input_tokens": 400,
  "cached_input_tokens": 200,
  "output_tokens": 300,
  "reasoning_tokens": 100
}
```

## Idempotency

- Every billable request requires an idempotency key.
- Usage events are unique per tenant and idempotency key.
- Retrying the same request with the same idempotency key returns the existing usage event instead of creating another one.
- This prevents duplicate usage and duplicate billing.

## Quota Enforcement

The system checks current monthly usage plus requested usage against the active plan limit.

| Condition | Result |
| --------- | ------ |
| Within limit | Accepted |
| Exactly at limit | Accepted |
| Above limit | `429 Too Many Requests` |

A rejected request is not recorded as a usage event.

## Cost Calculation

Costs are calculated using integer micro-dollar units instead of floating-point values.

**Pinned pricing:**

| Unit | Cost (micro-dollars) |
| ---- | --------------------: |
| API call | 1,000 |
| Input token | 2 |
| Cached input token | 1 |
| Output token | 8 |
| Reasoning token | 8 |

**Example:**

```
400 input
200 cached input
300 output
100 reasoning

Total = 4200 micro-dollars = $0.0042
```

## Payment Integration

The original capstone specification uses Stripe Test Mode.

This implementation uses Razorpay Test Mode as the payment-provider alternative because Stripe onboarding/testing was not practical in the development environment.

**The subscription flow is:**

```
Create Subscription → Razorpay Test Mode → Webhook → Signature Verification → Event Deduplication → Subscription / Plan Update
```

## Webhook Security

- Razorpay webhook signatures are verified before processing the event.
- Provider event IDs are stored to prevent duplicate processing.

| Event | Result |
| ----- | ------ |
| Invalid signature | `400` |
| Duplicate event | Ignored |
| Valid event | Processed |

## Background Job

A usage reconciliation job recalculates costs from persisted usage events.

It runs outside the normal API request path and includes retry handling for transient failures.

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Capstone
```

### 2. Configure Environment Variables

Create `.env` from `.env.example`.

Configure:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/metering
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxx
RAZORPAY_PRO_PLAN_ID=plan_xxxxxxxxxx
APP_ENV=development
```

### 3. Start PostgreSQL

```bash
docker compose up -d
```

### 4. Apply Migrations

```bash
alembic upgrade head
```

### 5. Seed the Database

```bash
python -m app.seed
```

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

### 7. Run Tests

```bash
pytest -q
```

## Database

The main tables are:

- `tenants`
- `plans`
- `subscriptions`
- `usage_events`
- `payment_events`

Usage and subscription data are tenant-specific, providing tenant isolation.

## Limitations

The core implementation intentionally does not include:

- Real production payments
- Overage billing
- Invoicing
- Proration
- Production-grade authentication
- Actual AI model calls

Razorpay Test Mode is used for subscription testing.

AI token usage is simulated and only the usage numbers are metered.

## Documentation

- `BUILDLOG.md` — Development history
- `EVIDENCE.md` — Implementation evidence

## Project Status

- **Phase 1** — Design and project setup
- **Phase 2** — Core billing logic
- **Phase 3** — Razorpay Integration
- **Phase 4** — Cost & Finalization
- **Phase 5** — Demo & Submission