from app.application.ports.password_hasher import PasswordHasher
from app.bootstrap.container import ApplicationContainer
from app.core.config import get_settings
from app.infrastructure.security import Argon2PasswordHasher


def test_container_uses_password_hasher() -> None:
    settings = get_settings()

    password_hasher = Argon2PasswordHasher()

    container = ApplicationContainer(
        settings=settings,
        password_hasher=password_hasher,
    )

    assert isinstance(
        container.password_hasher,
        PasswordHasher,
    )

    assert isinstance(
        container.password_hasher,
        Argon2PasswordHasher,
    )
