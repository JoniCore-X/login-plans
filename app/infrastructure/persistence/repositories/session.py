from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.sessions.ports import SessionRepository
from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import (
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.value_objects import UserId
from app.infrastructure.persistence.mappers.session import (
    session_to_domain,
    session_to_model,
)
from app.infrastructure.persistence.models.session import SessionModel


class PostgresSessionRepository(SessionRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        session_id: SessionId,
    ) -> Session | None:
        result = await self.session.execute(
            select(SessionModel).where(
                SessionModel.id == session_id.value,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return session_to_domain(model)

    async def get_by_credential_hash(
        self,
        credential_hash: SessionCredentialHash,
    ) -> Session | None:
        result = await self.session.execute(
            select(SessionModel).where(
                SessionModel.credential_hash == credential_hash.value,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return session_to_domain(model)

    async def get_by_user_id(
        self,
        user_id: UserId,
    ) -> list[Session]:
        result = await self.session.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id.value)
            .order_by(SessionModel.created_at.desc()),
        )

        return [session_to_domain(model) for model in result.scalars().all()]

    async def add(
        self,
        session: Session,
    ) -> None:
        self.session.add(
            session_to_model(session),
        )

    async def revoke(
        self,
        session: Session,
    ) -> None:
        model = await self.session.get(
            SessionModel,
            session.id.value,
        )

        if model is None:
            return

        model.status = session.status.value
        model.revoked_at = session.revoked_at
