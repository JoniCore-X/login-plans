from app.application.dto.user import UserDTO
from app.application.queries.get_user import GetUserQuery
from app.domain.exceptions.user import UserNotFoundError
from app.domain.repositories.unit_of_work import UnitOfWork


class GetUserService:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.unit_of_work = unit_of_work

    async def execute(
        self,
        query: GetUserQuery,
    ) -> UserDTO:
        async with self.unit_of_work:
            user = await self.unit_of_work.users.get_by_id(
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
