from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password_hash import PasswordHash


def test_user_can_be_created() -> None:
    email = Email("user@example.com")
    password_hash = PasswordHash("hashed-password")

    user = User.create(
        email=email,
        password_hash=password_hash,
    )

    assert user.email.value == "user@example.com"
    assert user.password_hash.value == "hashed-password"
