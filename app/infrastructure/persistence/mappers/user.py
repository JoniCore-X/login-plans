from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password_hash import PasswordHash
from app.infrastructure.persistence.models.user import UserModel


def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email.value,
        password_hash=user.password_hash.value,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
