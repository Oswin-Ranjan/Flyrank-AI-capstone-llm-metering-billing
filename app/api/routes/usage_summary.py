from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models import Tenant
from app.schemas.usage import UsageResponse
from app.services.usage import UsageService


router = APIRouter(
    prefix="/usage",
    tags=["usage"],
)


@router.get("", response_model=UsageResponse)
def get_usage(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    service = UsageService(db)

    return service.get_summary(tenant)