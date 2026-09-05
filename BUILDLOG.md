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
- help structure the design document, project
architecture, and implementation plan.

All generated code will be reviewed, tested, and modified as required.

### Human decisions
- Python + FastAPI selected as the implementation lane.
- PostgreSQL selected as the database.
- Docker selected for local database/runtime setup.
- Core scope is limited to the requirements defined in the capstone brief.

### Design decisions

- Selected Python + FastAPI.
- PostgreSQL is used for persistent storage.
- SQLAlchemy is used as the ORM.
- Alembic is used for schema migrations.
- Usage events use a tenant-scoped idempotency key.
- Stripe events are stored to prevent duplicate webhook processing.
- The core scope is limited to the required usage, quota, cost, and subscription functionality.
- Real payments, invoicing, proration, and overage billing are outside the core scope.

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

```text
UNIQUE(tenant_id, idempotency_key)

This prevents duplicate usage events when the same billable request is retried.
```

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
```
1,000 API calls/month
100,000 AI tokens/month
```

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

Cost is currently returned as 0 because detailed cost calculation is implemented in a later phase.

### API Validation

Added request validation for:

- Quantity greater than zero
- Supported usage types
- Required Idempotency-Key
- Existing tenant

Invalid requests return appropriate 4xx responses instead of being recorded.

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
- /usage returns the correct usage summary.

### Manual API Verification

The following API behaviors were manually verified through the FastAPI Swagger interface:
```
GET /health
POST /generate
GET /usage
```
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

- Replaced Stripe integration with Razorpay Test Mode because Razorpay
  provides the required subscription and webhook capabilities for this
  implementation.
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

### Security

- Webhook requests without a signature are rejected.
- Invalid webhook signatures are rejected.
- Provider event IDs are stored to prevent duplicate processing.

### AI assistance

AI assistance was used to help structure and review the Razorpay integration, webhook handling, and tests. Implementation was manually reviewed and tested.

---

## Phase 4 — Cost & Finalization

### Cost calculation

Implemented:

- Integer-based cost calculation.
- API call pricing.
- AI input-token pricing.
- Cached input-token pricing.
- Output-token pricing.
- Reasoning-token pricing.

Reasoning tokens use the same pricing as output tokens.

### Usage rollup

Updated `GET /usage` to return:

- Current API call usage.
- API call limit.
- Current AI token usage.
- AI token limit.
- Current monthly cost.

### Testing

Added deterministic tests for:

- API call cost.
- AI token cost.
- Cached input pricing.
- Reasoning-token pricing.
- Pinned pricing totals.
- Usage cost rollup.
- Retried requests not increasing cost twice.

### AI assistance

AI assistance was used to help structure the cost calculator and related tests.

Pricing rules and expected values were reviewed manually and pinned in tests.