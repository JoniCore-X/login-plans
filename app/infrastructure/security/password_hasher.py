from argon2 import PasswordHasher as Argon2PasswordHasherLibrary
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.application.ports.password_hasher import PasswordHasher
from app.domain.value_objects.password import PlainPassword
from app.domain.value_objects.password_hash import PasswordHash


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2PasswordHasherLibrary()

    def hash(
        self,
        password: PlainPassword,
    ) -> PasswordHash:
        hashed_password = self._hasher.hash(
            password.value,
        )

        return PasswordHash(hashed_password)

    def verify(
        self,
        password: PlainPassword,
        password_hash: PasswordHash,
    ) -> bool:
        try:
            return self._hasher.verify(
                password_hash.value,
                password.value,
            )

        except VerifyMismatchError:
            return False

        except (VerificationError, InvalidHashError):
            return False
