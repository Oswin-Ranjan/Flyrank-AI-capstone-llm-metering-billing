# Usage Metering & Billing Engine — Design Document

## 1. Problem

A SaaS application needs to answer three questions:

1. How much has a tenant used?
2. What should that usage cost?
3. Has the tenant reached its subscription limits?

This service provides usage metering, quota enforcement, cost calculation,
and Stripe subscription synchronization.

The system is designed around correctness under retries, quota boundaries,
and duplicate webhook events.

---

## 2. Scope

The core system contains:

- Two plans: Free and Pro
- Two usage types:
  - API calls
  - AI tokens
- One dummy billable endpoint: `POST /generate`
- One usage read endpoint: `GET /usage`
- Stripe test-mode Checkout
- Stripe webhook synchronization

AI usage is simulated. No AI model API is required for the core system.

---

## 3. Plans and Quotas

### Free

- 1,000 API calls per month
- 100,000 AI tokens per month

### Pro

- Higher API call limit than Free
- Higher AI token limit than Free

The exact Pro limits are application configuration choices.

---

## 4. Data Model

### Tenant

Represents a customer organization.

Fields:

- `id`
- `name`
- `created_at`

### Plan

Defines the usage limits for a subscription plan.

Fields:

- `id`
- `name`
- `api_call_limit`
- `ai_token_limit`

### Subscription

Associates a tenant with a plan and mirrors Stripe subscription state.

Fields:

- `id`
- `tenant_id`
- `plan_id`
- `stripe_customer_id`
- `stripe_subscription_id`
- `status`
- `created_at`
- `updated_at`

### UsageEvent

Represents one billable usage event.

Fields:

- `id`
- `tenant_id`
- `usage_type`
- `quantity`
- `idempotency_key`
- `created_at`

A unique constraint on `(tenant_id, idempotency_key)` prevents the
same billable request from being recorded more than once.

### StripeEvent

Stores processed Stripe event IDs so duplicate webhook events can be ignored.

Fields:

- `id`
- `stripe_event_id`
- `event_type`
- `processed_at`

---

## 5. API Surface

### POST /generate

Creates a billable usage event.

Request requirements:

- `Idempotency-Key` header
- usage type
- quantity

Processing:

1. Validate the request.
2. Check whether the idempotency key has already been processed.
3. Determine the tenant's current usage.
4. Check the tenant's plan quota.
5. Reject the request if the quota would be exceeded.
6. Record the usage event.
7. Return the result.

Repeated requests using the same tenant and idempotency key must not create
another usage event.

---

### GET /usage

Returns the tenant's current monthly usage, limits, and calculated cost.

The response will expose:

- API calls used
- API call limit
- AI tokens used
- AI token limit
- current cost

---

### POST /billing/checkout

Creates a Stripe Checkout session for upgrading a tenant to the Pro plan.

The service uses Stripe test mode only.

---

### POST /webhooks/stripe

Receives Stripe webhook events.

Supported events:

- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

Processing:

1. Verify the Stripe webhook signature.
2. Check whether the Stripe event has already been processed.
3. Ignore duplicate events.
4. Update the tenant subscription and plan state.
5. Record the processed Stripe event.

---

## 6. Idempotency Strategy

The system uses an idempotency key supplied by the client.

Example:

```text
Idempotency-Key: abc-123