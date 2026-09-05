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
        input_tokens=request.input_tokens,
        cached_input_tokens=request.cached_input_tokens,
        output_tokens=request.output_tokens,
        reasoning_tokens=request.reasoning_tokens,
    )

    return GenerateResponse(
        usage_event_id=usage_event.id,
        tenant_id=usage_event.tenant_id,
        usage_type=usage_event.usage_type,
        quantity=usage_event.quantity,
        input_tokens=usage_event.input_tokens,
        cached_input_tokens=usage_event.cached_input_tokens,
        output_tokens=usage_event.output_tokens,
        reasoning_tokens=usage_event.reasoning_tokens,
        idempotency_key=usage_event.idempotency_key,
        status="recorded",
    )