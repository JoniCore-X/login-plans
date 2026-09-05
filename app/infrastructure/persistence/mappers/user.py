from app.domain.users.entities import User
from app.domain.users.enums import UserStatus
from app.domain.users.value_objects import (
    Email,
    PasswordHash,
    UserId,
)
from app.infrastructure.persistence.models.user import UserModel


def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id.value,
        email=user.email.value,
        password_hash=user.password_hash.value,
        status=user.status.value,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def user_to_domain(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
        status=UserStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
