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

## Non-Goal

Real payment processing and production billing are out of scope.
Stripe test mode is used only for subscription-flow testing.

## Project Status

Phase 1 - Design and project setup

Phase 2 - Core billing logic