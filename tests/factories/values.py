from uuid import uuid4

from app.domain.value_objects.email import Email
from app.domain.value_objects.password import PlainPassword
from app.domain.value_objects.password_hash import PasswordHash


def email_factory(
    value: str | None = None,
) -> Email:
    if value is None:
        value = f"{uuid4()}@example.com"

    return Email(value)


def password_hash_factory(
    value: str = "test-password-hash",
) -> PasswordHash:
    return PasswordHash(value)


def plain_password_factory(
    value: str = "Strong-password-123!",
) -> PlainPassword:
    return PlainPassword(value)
