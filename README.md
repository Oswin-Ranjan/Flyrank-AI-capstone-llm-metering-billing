# FlyRank Usage Metering & Billing Engine

A backend service for SaaS usage metering, quota enforcement, cost calculation,
and Stripe subscription synchronization.

## Problem

SaaS applications need to know:

1. How much a customer has used.
2. What that usage costs.
3. Whether the customer has reached their plan limits.

This project implements those capabilities with an emphasis on correctness
under retries, quota boundaries, and webhook duplication.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Stripe Test Mode
- Stripe CLI
- Pytest

## Core Scope

- Free and Pro plans
- API call metering
- AI token metering
- Idempotent usage recording
- Monthly quota enforcement
- Usage and cost reporting
- Stripe Checkout
- Stripe webhook verification
- Duplicate webhook prevention

## Limitations

The core implementation intentionally does not include:

- Real production payments.
- Overage billing.
- Invoicing.
- Proration.
- Production-grade authentication.
- Actual AI model calls.

Razorpay Test Mode is used for subscription testing.

AI token usage is simulated and only the usage numbers are metered.

## Project Status

Phase 1 - Design and project setup

Phase 2 - Core billing logic

Phase 3 - Razorpay Integration

Phase 4 - Cost & Finalization