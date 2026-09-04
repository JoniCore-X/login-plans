from argon2 import PasswordHasher as Argon2PasswordHasherLibrary
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.application.ports.password_hasher import PasswordHasher
from app.domain.value_objects.password_hash import PasswordHash


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = Argon2PasswordHasherLibrary()

    def hash(self, password: str) -> PasswordHash:
        hashed_password = self._hasher.hash(password)

        return PasswordHash(hashed_password)

    def verify(
        self,
        password: str,
        password_hash: PasswordHash,
    ) -> bool:
        try:
            return self._hasher.verify(
                password_hash.value,
                password,
            )

        except VerifyMismatchError:
            return False

        except (VerificationError, InvalidHashError):
            return False
