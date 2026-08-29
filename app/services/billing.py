import razorpay
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Plan, Subscription, Tenant


class BillingService:
    def __init__(self, db: Session):
        self.db = db

        self.client = razorpay.Client(
            auth=(
                settings.razorpay_key_id,
                settings.razorpay_key_secret,
            )
        )

    def create_subscription(
        self,
        tenant: Tenant,
        plan: Plan,
    ) -> dict:
        if plan.name != "Pro":
            raise HTTPException(
                status_code=400,
                detail="Only the Pro plan can be purchased.",
            )

        existing_subscription = self.db.scalar(
            select(Subscription)
            .where(
                Subscription.tenant_id == tenant.id,
                Subscription.plan_id == plan.id,
                Subscription.status.in_(
                    ["created", "authenticated", "active"]
                ),
            )
        )

        if existing_subscription:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Tenant already has a pending or active "
                    "Pro subscription."
                ),
            )

        try:
            razorpay_subscription = self.client.subscription.create(
                {
                    "plan_id": settings.razorpay_pro_plan_id,
                    "total_count": 12,
                    "quantity": 1,
                    "customer_notify": True,
                    "notes": {
                        "tenant_id": str(tenant.id),
                        "plan_id": str(plan.id),
                    },
                }
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail="Unable to create Razorpay subscription.",
            ) from exc

        local_subscription = Subscription(
            tenant_id=tenant.id,
            plan_id=plan.id,
            provider_subscription_id=razorpay_subscription["id"],
            provider_customer_id=razorpay_subscription.get(
                "customer_id"
            ),
            status=razorpay_subscription["status"],
        )

        self.db.add(local_subscription)
        self.db.commit()
        self.db.refresh(local_subscription)

        return {
            "subscription_id": razorpay_subscription["id"],
            "status": razorpay_subscription["status"],
            "short_url": razorpay_subscription.get("short_url"),
        }