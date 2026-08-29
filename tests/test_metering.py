from app.schemas import UsageType
from app.services.metering import MeteringService
from app.models import UsageEvent


def test_same_idempotency_key_creates_one_event(db, free_tenant):
    service = MeteringService(db)

    first = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=1,
        idempotency_key="duplicate-test",
    )

    second = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=1,
        idempotency_key="duplicate-test",
    )

    assert first.id == second.id

    events = (
        db.query(UsageEvent)
        .filter(
            UsageEvent.tenant_id == free_tenant.id,
            UsageEvent.idempotency_key == "duplicate-test",
        )
        .all()
    )

    assert len(events) == 1


def test_different_idempotency_keys_create_different_events(
    db,
    free_tenant,
):
    service = MeteringService(db)

    first = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=1,
        idempotency_key="key-1",
    )

    second = service.record_usage(
        tenant=free_tenant,
        usage_type=UsageType.API_CALL,
        quantity=1,
        idempotency_key="key-2",
    )

    assert first.id != second.id