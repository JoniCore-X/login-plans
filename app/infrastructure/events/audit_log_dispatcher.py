import dataclasses
import json
import logging
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.event_dispatcher import EventDispatcher
from app.domain.events import DomainEvent
from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)

logger = logging.getLogger(__name__)


def _serialize_event(event: DomainEvent) -> dict[str, Any]:
    raw = dataclasses.asdict(event)
    payload: dict[str, Any] = json.loads(
        json.dumps(raw, default=str),
    )
    return payload


def _extract_user_id(event: DomainEvent) -> UUID | None:
    user_id = getattr(event, "user_id", None)

    if user_id is None:
        return None

    if isinstance(user_id, UUID):
        return user_id

    value = getattr(user_id, "value", None)
    return value if isinstance(value, UUID) else None


class AuditLogDispatcher(EventDispatcher):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def dispatch(
        self,
        events: list[DomainEvent],
    ) -> None:
        if not events:
            return

        context = structlog.contextvars.get_contextvars()
        request_id = context.get("request_id")

        try:
            async with self._session_factory() as session:
                for event in events:
                    session.add(
                        AuditLogModel(
                            event_type=event.event_type,
                            user_id=_extract_user_id(event),
                            request_id=request_id,
                            payload=_serialize_event(event),
                            occurred_at=event.occurred_at,
                        ),
                    )

                await session.commit()
        except Exception:
            logger.exception("Failed to persist audit log")
