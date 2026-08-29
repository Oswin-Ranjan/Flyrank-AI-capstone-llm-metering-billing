import pytest
from fastapi import HTTPException

from app.schemas import UsageType
from app.services.metering import MeteringService


def test_usage_can_reach_exact_quota(db, free_tenant):
    service = MeteringService(db)

    event = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=3,
        idempotency_key="exact-limit",
    )

    assert event.quantity == 3


def test_usage_above_quota_is_rejected(db, free_tenant):
    service = MeteringService(db)

    with pytest.raises(HTTPException) as exc:
        service.record_usage(
            tenant=free_tenant,
            usage_type=UsageType.API_CALL,
            quantity=4,
            idempotency_key="over-limit",
        )

    assert exc.value.status_code == 429


def test_usage_just_below_quota_is_allowed(db, free_tenant):
    service = MeteringService(db)

    event = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=2,
        idempotency_key="below-limit",
    )

    assert event.quantity == 2