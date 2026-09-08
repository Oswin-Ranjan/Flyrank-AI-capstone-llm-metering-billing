# BUILDLOG

## Phase 1 — Design

### Project setup

- Selected the Python + FastAPI lane.
- Created the initial layered project structure.
- Added Docker and PostgreSQL.
- Added dependency management.
- Defined the initial database entities.

### AI assistance

AI assistance was used to:

- understand and break down the capstone requirements,
- design the initial project structure,
- draft boilerplate configuration,
- help structure the project architecture and implementation plan.

All generated code was reviewed, tested, and modified as required.

### Human decisions

- Python + FastAPI selected as the implementation lane.
- PostgreSQL selected as the database.
- Docker selected for local database/runtime setup.
- Core scope was limited to the requirements defined in the capstone brief.
- Razorpay Test Mode was selected later as the payment provider for the implementation.

### Design decisions

- Selected Python + FastAPI.
- PostgreSQL is used for persistent storage.
- SQLAlchemy is used as the ORM.
- Alembic is used for schema migrations.
- Usage events use a tenant-scoped idempotency key.
- Payment events are stored to prevent duplicate webhook processing.
- The core scope is limited to usage, quota, cost, and subscription functionality.
- Real production payments, invoicing, proration, and overage billing are outside the core scope.

---

## Phase 2 — Core Billing Logic

### Metering

Implemented the core usage metering flow through `POST /generate`.

The endpoint supports two usage types:

- `API_CALL`
- `AI_TOKEN`

Each billable request requires an `Idempotency-Key`.

The metering service:

1. Identifies the tenant.
2. Checks whether the idempotency key has already been processed.
3. Checks the tenant's active plan quota.
4. Creates a usage event when the request is allowed.
5. Returns the existing usage event when the same idempotency key is retried.

### Idempotency

Added tenant-scoped idempotency protection using:

```
UNIQUE(tenant_id, idempotency_key)
```

This prevents duplicate usage events when the same billable request is retried.

Manual verification confirmed:

- Repeating a request with the same idempotency key returned the same usage event.
- The repeated request did not create another usage event.
- Different idempotency keys created separate usage events.

### Quota Enforcement

Implemented quota checks based on the tenant's active subscription plan.

The quota calculation uses:

```
current usage + requested quantity
```

A request is allowed when the projected usage is within the configured limit.

A request exceeding the limit returns:

```
HTTP 429 Too Many Requests
```

The response includes:

- Usage type
- Current usage
- Requested quantity
- Configured limit

Manual boundary testing verified:

- Usage below the limit is allowed.
- Usage exactly at the limit is allowed.
- Usage above the limit is rejected.
- Rejected usage is not recorded.

The Free plan uses:

- 1,000 API calls/month
- 100,000 AI tokens/month

A temporary lower quota was used during development to make boundary testing practical.

### Usage Summary

Implemented:

```
GET /usage
```

The endpoint returns:

- Current API call usage
- API call limit
- Current AI token usage
- AI token limit
- Current cost

The cost value was later updated in Phase 4 to use the implemented cost calculation.

### API Validation

Added request validation for:

- Quantity greater than zero
- Supported usage types
- Required `Idempotency-Key`
- Existing tenant

For AI-token requests, validation also ensures that the requested quantity matches the sum of the token categories.

Invalid requests return appropriate `4xx` responses instead of being recorded.

### Automated Testing

Added tests covering:

- Same idempotency key creates only one usage event.
- Different idempotency keys create separate events.
- Usage below the quota is accepted.
- Usage exactly at the quota is accepted.
- Usage above the quota is rejected.
- Invalid quantities are rejected.
- Invalid usage types are rejected.
- Missing idempotency keys are rejected.
- Unknown tenants are rejected.
- `/usage` returns the usage summary.

### Manual API Verification

The following API behaviors were manually verified through the FastAPI Swagger interface:

- `GET /health`
- `POST /generate`
- `GET /usage`

Manual tests included:

- Normal API call metering
- AI token metering
- Repeated requests with the same idempotency key
- Requests using different idempotency keys
- Quota boundary testing
- Over-quota rejection
- Invalid request validation
- Tenant lookup validation

### AI Assistance

AI assistance was used during Phase 2 to:

- Structure the metering and quota services.
- Design the idempotency strategy.
- Draft API schemas and routes.
- Suggest automated test cases.
- Help diagnose and fix implementation issues encountered during testing.

The generated suggestions were reviewed, modified where necessary, and manually tested before being used in the project.

### Human Decisions

- FastAPI was used for the API layer.
- SQLAlchemy was used for database access.
- PostgreSQL was used for persistent usage storage.
- Tenant + idempotency key uniqueness was enforced at the database level.
- Quota checking was performed before creating a new usage event.
- API calls and AI tokens were tracked as separate usage types.
- A temporary lower quota was used during development for practical boundary testing.

---

## Phase 3 — Razorpay Integration

### Completed

- Replaced the originally planned Stripe integration with Razorpay Test Mode because Razorpay provided the required subscription and webhook capabilities for this implementation.
- Created a Razorpay Pro subscription plan.
- Implemented subscription creation through the Razorpay API.
- Added provider-neutral subscription fields.
- Implemented webhook signature verification.
- Implemented webhook event deduplication.
- Implemented subscription lifecycle synchronization.
- Verified the real `subscription.authenticated` webhook.
- Verified the real `subscription.activated` webhook.
- Verified the Free → Pro transition.
- Verified Pro limits through `GET /usage`.

### Subscription Creation

Implemented:

```
POST /billing/subscription
```

The endpoint creates a Razorpay subscription and returns the provider subscription information required for the test flow.

### Webhook Processing

Implemented:

```
POST /webhooks/razorpay
```

The webhook handler processes supported subscription lifecycle events and synchronizes them with the local subscription record.

### Security

- Webhook requests without a signature are rejected.
- Invalid webhook signatures are rejected.
- Provider event IDs are stored to prevent duplicate processing.
- Duplicate webhook events are not processed again.

### Subscription Synchronization

When a Razorpay subscription becomes active:

- The corresponding local subscription is updated.
- The tenant is assigned the corresponding plan.
- Older active subscriptions for the same tenant are deactivated.

### Verification

The real Razorpay subscription flow was tested through the deployed webhook endpoint.

Verified events included:

- `subscription.authenticated`
- `subscription.activated`

After activation, `GET /usage` reflected the Pro plan limits:

- API calls: 10,000
- AI tokens: 1,000,000

### AI Assistance

AI assistance was used to help structure and review the Razorpay integration, webhook handling, configuration, and tests.

Implementation was manually reviewed and tested before being finalized.

---

## Phase 4 — Cost & Finalization

### Cost Calculation

Implemented:

- Integer-based cost calculation.
- API call pricing.
- AI input-token pricing.
- Cached input-token pricing.
- Output-token pricing.
- Reasoning-token pricing.

Reasoning tokens use the same pricing as output tokens.

**Pinned pricing:**

| Unit | Cost (micro-dollars) |
| ---- | --------------------: |
| API call | 1,000 |
| Input token | 2 |
| Cached input token | 1 |
| Output token | 8 |
| Reasoning token | 8 |

### Token Accounting

Added separate tracking for:

- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `reasoning_tokens`

AI requests validate that:

```
quantity =
    input_tokens
    + cached_input_tokens
    + output_tokens
    + reasoning_tokens
```

### Usage Rollup

Updated `GET /usage` to return:

- Current API call usage.
- API call limit.
- Current AI token usage.
- AI token limit.
- Current monthly cost.

### Pinned Cost Test

A deterministic pricing case was added:

```
Input tokens            = 400
Cached input tokens     = 200
Output tokens           = 300
Reasoning tokens        = 100
```

**Expected cost:**

```
400 × 2   = 800
200 × 1   = 200
300 × 8   = 2400
100 × 8   = 800

Total = 4200 micro-dollars
```

### Testing

Added deterministic tests for:

- API call cost.
- AI token cost.
- Cached input pricing.
- Reasoning-token pricing.
- Pinned pricing totals.
- Usage cost rollup.
- Retried requests not increasing cost twice.

### Background Reconciliation

Added a usage reconciliation background job that:

- Reads persisted usage events.
- Recalculates usage costs.
- Supports retry handling for transient failures.
- Logs failures after the retry limit.

### AI Assistance

AI assistance was used to help structure the cost calculator, token accounting, reconciliation job, and related tests.

Pricing rules and expected values were reviewed manually and pinned in tests.

---

## Phase 5 — Demo & Submission

### Finalization

- Finalized the project README.
- Finalized the evidence documentation.
- Updated the build log with the completed implementation phases.
- Removed outdated Stripe-specific documentation and references.
- Added the final project status and verification checklist.
- Prepared the project for final demonstration and submission.

### Final Demo Flow

The final demonstration covers:

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
Duplicate Webhook Handling
    ↓
GET /usage
```

### Final Verification

The final project verification includes:

- Database migration verification.
- API endpoint verification.
- Idempotency verification.
- Quota boundary verification.
- Cost calculation verification.
- Razorpay subscription verification.
- Webhook security verification.
- Webhook deduplication verification.
- Usage summary verification.
- Automated test execution.
- Repository and secret-handling review.

### AI Assistance

AI assistance was used during Phase 5 to:

- Review project documentation.
- Organize the final build log and evidence.
- Prepare the final demo flow.
- Identify outdated documentation and consistency issues.

All final documentation and implementation decisions were reviewed before submission.

### Human Decisions

- Razorpay Test Mode was retained as the payment implementation.
- Evidence was kept separate from implementation details so that final claims can be traced to actual testing results.

### Final Project State

The completed project contains:

- Multi-tenant usage metering
- API call tracking
- AI token tracking
- Idempotency
- Quota enforcement
- Cost calculation
- Subscription management
- Razorpay webhook processing
- Webhook verification
- Webhook deduplication
- Usage reporting
- Background reconciliation
- Automated testing
- Final project documentation