from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Plan, Subscription, UsageEvent, Tenant
from app.schemas import UsageType


class QuotaService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_plan(self, tenant: Tenant) -> Plan:
        subscription = self.db.scalar(
            select(Subscription)
            .where(
                Subscription.tenant_id == tenant.id,
                Subscription.status == "active",
            )
            .order_by(Subscription.created_at.desc())
        )

        if subscription is None:
            raise HTTPException(
                status_code=402,
                detail="No active subscription found.",
            )

        plan = self.db.get(Plan, subscription.plan_id)

        if plan is None:
            raise HTTPException(
                status_code=500,
                detail="Subscription plan not found.",
            )

        return plan

    def get_current_usage(
        self,
        tenant: Tenant,
        usage_type: UsageType,
    ) -> int:
        month_start = datetime.utcnow().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        result = self.db.scalar(
            select(func.coalesce(func.sum(UsageEvent.quantity), 0))
            .where(
                UsageEvent.tenant_id == tenant.id,
                UsageEvent.usage_type == usage_type.value,
                UsageEvent.created_at >= month_start,
            )
        )

        return int(result or 0)

    def get_limit(
        self,
        plan: Plan,
        usage_type: UsageType,
    ) -> int:
        if usage_type == UsageType.API_CALL:
            return plan.api_call_limit

        if usage_type == UsageType.AI_TOKEN:
            return plan.ai_token_limit

        raise ValueError(f"Unsupported usage type: {usage_type}")

    def check_quota(
        self,
        tenant: Tenant,
        usage_type: UsageType,
        requested_quantity: int,
    ) -> None:
        if usage_type == UsageType.AI_TOKEN:
            return

        plan = self.get_active_plan(tenant)
        current_usage = self.get_current_usage(
            tenant,
            usage_type,
        )
        limit = self.get_limit(
            plan,
            usage_type,
        )

        projected_usage = current_usage + requested_quantity

        if projected_usage > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Usage quota exceeded.",
                    "usage_type": usage_type.value,
                    "used": current_usage,
                    "requested": requested_quantity,
                    "limit": limit,
                },
            )