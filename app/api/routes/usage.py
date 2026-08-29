from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models import Tenant
from app.schemas import GenerateRequest, GenerateResponse
from app.services.metering import MeteringService


router = APIRouter(
    tags=["usage"],
)


@router.post("/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    if not idempotency_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key cannot be empty.",
        )

    service = MeteringService(db)

    usage_event = service.record_usage(
        tenant=tenant,
        usage_type=request.usage_type,
        quantity=request.quantity,
        idempotency_key=idempotency_key,
    )

    return GenerateResponse(
        usage_event_id=usage_event.id,
        tenant_id=usage_event.tenant_id,
        usage_type=usage_event.usage_type,
        quantity=usage_event.quantity,
        idempotency_key=usage_event.idempotency_key,
        status="recorded",
    )