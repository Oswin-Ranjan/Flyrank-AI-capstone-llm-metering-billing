from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Plan, Subscription, UsageEvent, Tenant
from app.schemas import UsageType
from app.services.cost import CostService


class UsageService:
    def __init__(self, db: Session):
        self.db = db

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
            select(
                func.coalesce(
                    func.sum(UsageEvent.quantity),
                    0,
                )
            ).where(
                UsageEvent.tenant_id == tenant.id,
                UsageEvent.usage_type == usage_type.value,
                UsageEvent.created_at >= month_start,
            )
        )

        return int(result or 0)

    def get_plan(
        self,
        tenant: Tenant,
    ) -> Plan:
        subscription = self.db.scalar(
            select(Subscription)
            .where(
                Subscription.tenant_id == tenant.id,
                Subscription.status == "active",
            )
            .order_by(
                Subscription.created_at.desc()
            )
        )

        if subscription is None:
            raise HTTPException(
                status_code=402,
                detail="No active subscription found.",
            )

        plan = self.db.get(
            Plan,
            subscription.plan_id,
        )

        if plan is None:
            raise HTTPException(
                status_code=500,
                detail="Subscription plan not found.",
            )

        return plan

    def get_current_cost(
        self,
        tenant: Tenant,
    ) -> int:
        month_start = datetime.utcnow().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        events = self.db.scalars(
            select(UsageEvent).where(
                UsageEvent.tenant_id == tenant.id,
                UsageEvent.created_at >= month_start,
            )
        ).all()

        return sum(
            CostService.calculate_event_cost(event)
            for event in events
            if event.usage_type == UsageType.AI_TOKEN.value
        )

    def get_summary(
        self,
        tenant: Tenant,
    ) -> dict:
        plan = self.get_plan(tenant)

        api_calls = self.get_current_usage(
            tenant,
            UsageType.API_CALL,
        )

        ai_tokens = self.get_current_usage(
            tenant,
            UsageType.AI_TOKEN,
        )

        cost = self.get_current_cost(tenant)

        return {
            "api_calls": {
                "used": api_calls,
                "limit": plan.api_call_limit,
            },
            "ai_tokens": {
                "used": ai_tokens,
                "limit": plan.ai_token_limit,
            },
            "cost": cost,
        }