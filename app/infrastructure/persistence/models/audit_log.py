from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )

    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_audit_logs_user_time",
            "user_id",
            occurred_at.desc(),
        ),
    )
