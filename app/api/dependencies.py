from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Tenant


def get_current_tenant(
    x_tenant_id: int = Header(..., alias="X-Tenant-ID"),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.scalar(
        select(Tenant).where(Tenant.id == x_tenant_id)
    )

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return tenant