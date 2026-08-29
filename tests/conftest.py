import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Plan, Tenant, Subscription, UsageEvent


def _build_test_database_url() -> str:
    configured_url = os.getenv("TEST_DATABASE_URL")
    if configured_url:
        return configured_url

    project_root = Path(__file__).resolve().parent.parent
    sqlite_db = project_root / "test_data" / "test.db"
    sqlite_db.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_db}"


TEST_DATABASE_URL = _build_test_database_url()


@pytest.fixture
def db():
    engine_kwargs = {}
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(TEST_DATABASE_URL, **engine_kwargs)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = SessionLocal()

    # Clear data left by an interrupted test run before creating fresh fixtures.
    session.query(UsageEvent).delete()
    session.query(Subscription).delete()
    session.query(Tenant).delete()
    session.query(Plan).delete()
    session.commit()

    try:
        yield session
    finally:
        session.rollback()

        # Remove test data after every test.
        session.query(UsageEvent).delete()
        session.query(Subscription).delete()
        session.query(Tenant).delete()
        session.query(Plan).delete()

        session.commit()
        session.close()
        engine.dispose()


@pytest.fixture
def free_tenant(db: Session):
    plan = Plan(
        name="Test Free",
        api_call_limit=3,
        ai_token_limit=100,
    )

    tenant = Tenant(
        name="Test Tenant",
    )

    db.add(plan)
    db.add(tenant)
    db.flush()

    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        status="active",
    )

    db.add(subscription)
    db.commit()

    return tenant

@pytest.fixture(autouse=True)
def clear_dependency_overrides(db: Session):
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield
    app.dependency_overrides.clear()