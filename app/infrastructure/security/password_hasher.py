from argon2 import PasswordHasher as Argon2PasswordHasherLibrary
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.application.ports.password_hasher import PasswordHasher
from app.domain.users.value_objects import PasswordHash, PlainPassword


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

    def needs_rehash(
        self,
        password_hash: PasswordHash,
    ) -> bool:
        return self._hasher.check_needs_rehash(
            password_hash.value,
        )
