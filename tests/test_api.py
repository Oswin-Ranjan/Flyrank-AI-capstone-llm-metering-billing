from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db
from app.main import app
from app.models import Tenant, UsageEvent


def override_get_db(session):
    def _get_db():
        yield session

    return _get_db


def create_tenant(db):
    from app.models import Plan, Subscription

    plan = Plan(
        name="API Test Free",
        api_call_limit=3,
        ai_token_limit=100,
    )

    tenant = Tenant(
        name="API Test Tenant",
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


def test_generate_endpoint_creates_usage_event(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "api-test-1",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["quantity"] == 1
    assert data["idempotency_key"] == "api-test-1"

    app.dependency_overrides.clear()


def test_generate_endpoint_is_idempotent(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    headers = {
        "X-Tenant-ID": str(tenant.id),
        "Idempotency-Key": "api-idempotency-1",
    }

    payload = {
        "usage_type": "API_CALL",
        "quantity": 1,
    }

    first = client.post(
        "/generate",
        headers=headers,
        json=payload,
    )

    second = client.post(
        "/generate",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        first.json()["usage_event_id"]
        == second.json()["usage_event_id"]
    )

    events = db.scalars(
        select(UsageEvent).where(
            UsageEvent.tenant_id == tenant.id,
            UsageEvent.idempotency_key == "api-idempotency-1",
        )
    ).all()

    assert len(events) == 1

    app.dependency_overrides.clear()


def test_generate_endpoint_rejects_over_quota(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "api-quota-1",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 4,
        },
    )

    assert response.status_code == 429

    app.dependency_overrides.clear()

def test_usage_endpoint_returns_summary(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    generate_response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "usage-summary-1",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 2,
        },
    )

    assert generate_response.status_code == 200

    response = client.get(
        "/usage",
        headers={
            "X-Tenant-ID": str(tenant.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["api_calls"]["used"] == 2
    assert data["api_calls"]["limit"] == 3
    assert data["ai_tokens"]["used"] == 0
    assert data["ai_tokens"]["limit"] == 100
    assert data["cost"] == 0

    app.dependency_overrides.clear()    
    
def test_generate_rejects_zero_quantity(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "validation-1",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 0,
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()    
    
def test_generate_requires_idempotency_key(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 1,
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()   

def test_generate_rejects_negative_quantity(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "validation-negative",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": -1,
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()     
    
def test_generate_rejects_invalid_usage_type(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "validation-type",
        },
        json={
            "usage_type": "VIDEO_MINUTES",
            "quantity": 1,
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()   
    
def test_generate_rejects_unknown_tenant(db):
    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-ID": "999999",
            "Idempotency-Key": "unknown-tenant",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"

    app.dependency_overrides.clear()     
    
def test_usage_tracks_api_calls_and_ai_tokens_separately(db):
    tenant = create_tenant(db)

    app.dependency_overrides[get_db] = override_get_db(db)

    client = TestClient(app)

    client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "api-usage-1",
        },
        json={
            "usage_type": "API_CALL",
            "quantity": 2,
        },
    )

    client.post(
        "/generate",
        headers={
            "X-Tenant-ID": str(tenant.id),
            "Idempotency-Key": "token-usage-1",
        },
        json={
            "usage_type": "AI_TOKEN",
            "quantity": 50,
        },
    )

    response = client.get(
        "/usage",
        headers={
            "X-Tenant-ID": str(tenant.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["api_calls"]["used"] == 2
    assert data["ai_tokens"]["used"] == 50

    app.dependency_overrides.clear()    