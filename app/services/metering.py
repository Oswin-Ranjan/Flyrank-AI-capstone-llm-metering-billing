from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Tenant, UsageEvent
from app.schemas import UsageType
from app.services.quota import QuotaService


class MeteringService:
    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)

    def record_usage(
        self,
        tenant: Tenant,
        usage_type: UsageType,
        quantity: int,
        idempotency_key: str,
        input_tokens: int = 0,
        cached_input_tokens: int = 0,
        output_tokens: int = 0,
        reasoning_tokens: int = 0,
    ) -> UsageEvent:
        # 1. Check whether this request was already processed.
        existing_event = self.db.scalar(
            select(UsageEvent).where(
                UsageEvent.tenant_id == tenant.id,
                UsageEvent.idempotency_key == idempotency_key,
            )
        )

        if existing_event:
            return existing_event

        # 2. New request -> enforce quota.
        self.quota_service.check_quota(
            tenant=tenant,
            usage_type=usage_type,
            requested_quantity=quantity,
        )

        # 3. Record usage.
        usage_event = UsageEvent(
            tenant_id=tenant.id,
            usage_type=usage_type.value,
            quantity=quantity,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            idempotency_key=idempotency_key,
        )

        self.db.add(usage_event)

        try:
            self.db.commit()
            self.db.refresh(usage_event)
            return usage_event

        except IntegrityError:
            # Another concurrent request may have inserted the same
            # idempotency key between our SELECT and INSERT.
            self.db.rollback()

            existing_event = self.db.scalar(
                select(UsageEvent).where(
                    UsageEvent.tenant_id == tenant.id,
                    UsageEvent.idempotency_key == idempotency_key,
                )
            )

            if existing_event:
                return existing_event

            raise