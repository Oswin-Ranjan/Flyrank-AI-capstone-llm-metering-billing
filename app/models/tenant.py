from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    usage_events = relationship(
        "UsageEvent",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )