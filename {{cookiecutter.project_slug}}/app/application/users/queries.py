from dataclasses import dataclass

from app.domain.users.value_objects import UserId


@dataclass(frozen=True, slots=True)
class GetUserQuery:
    user_id: UserId
