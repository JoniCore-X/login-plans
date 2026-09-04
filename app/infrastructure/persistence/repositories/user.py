from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.mappers.user import (
    user_to_domain,
    user_to_model,
)
from app.infrastructure.persistence.models.user import UserModel


class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, user: User) -> None:
        model = user_to_model(user)

        self.session.add(model)

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.id == user_id,
        )

        result = await self.session.execute(statement)

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return user_to_domain(model)

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.email == email,
        )

        result = await self.session.execute(statement)

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return user_to_domain(model)

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:
        statement = select(UserModel.id).where(
            UserModel.email == email,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None
