from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Plan, Tenant, Subscription


def seed():
    db = SessionLocal()

    try:
        # -------------------------
        # Plans
        # -------------------------
        free_plan = db.scalar(
            select(Plan).where(Plan.name == "Free")
        )

        if not free_plan:
            free_plan = Plan(
                name="Free",
                api_call_limit=1000,
                ai_token_limit=100000,
            )
            db.add(free_plan)

        pro_plan = db.scalar(
            select(Plan).where(Plan.name == "Pro")
        )

        if not pro_plan:
            pro_plan = Plan(
            name="Pro",
            api_call_limit=10000,
            ai_token_limit=1000000,
            provider_plan_id=settings.razorpay_pro_plan_id,
        )
            db.add(pro_plan)
        else:
            pro_plan.provider_plan_id = settings.razorpay_pro_plan_id

        db.flush()

        # -------------------------
        # Demo tenant
        # -------------------------
        tenant = db.scalar(
            select(Tenant).where(
                Tenant.name == "Demo Tenant"
            )
        )

        if not tenant:
            tenant = Tenant(
                name="Demo Tenant",
            )
            db.add(tenant)
            db.flush()

        # -------------------------
        # Free subscription
        # -------------------------
        subscription = db.scalar(
            select(Subscription).where(
                Subscription.tenant_id == tenant.id
            )
        )

        if not subscription:
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_id=free_plan.id,
                status="active",
            )
            db.add(subscription)

        db.commit()

        print("Database seeded successfully.")
        print(f"Free Plan ID: {free_plan.id}")
        print(f"Pro Plan ID: {pro_plan.id}")
        print(f"Demo Tenant ID: {tenant.id}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()