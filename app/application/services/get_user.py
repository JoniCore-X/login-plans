from app.application.dto.user import UserDTO
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.queries.get_user import GetUserQuery
from app.domain.exceptions.user import UserNotFoundError


class GetUserService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory

    async def execute(
        self,
        query: GetUserQuery,
    ) -> UserDTO:
        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            user = await unit_of_work.users.get_by_id(
                query.user_id,
            )

            if user is None:
                raise UserNotFoundError(
                    "User not found",
                )

            return UserDTO(
                id=user.id,
                email=user.email.value,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
