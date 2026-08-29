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