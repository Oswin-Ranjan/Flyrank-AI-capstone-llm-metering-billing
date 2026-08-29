from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models import Plan, Tenant
from app.services.billing import BillingService


router = APIRouter(
    prefix="/billing",
    tags=["billing"],
)


@router.post("/subscription")
def create_subscription(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    plan = db.scalar(
        select(Plan).where(Plan.name == "Pro")
    )

    if plan is None:
        raise HTTPException(
            status_code=500,
            detail="Pro plan not found.",
        )

    service = BillingService(db)

    return service.create_subscription(
        tenant=tenant,
        plan=plan,
    )