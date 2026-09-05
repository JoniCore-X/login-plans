from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.users.ports import UserRepository
from app.domain.users.entities import User
from app.domain.users.value_objects import Email, UserId
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
        user_id: UserId,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.id == user_id.value,
        )

        result = await self.session.execute(statement)

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return user_to_domain(model)

    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.email == email.value,
        )

        result = await self.session.execute(statement)

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return user_to_domain(model)
