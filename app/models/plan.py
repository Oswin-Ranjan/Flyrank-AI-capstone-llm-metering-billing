from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    api_call_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ai_token_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    provider_plan_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
    )