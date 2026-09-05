from abc import ABC, abstractmethod

from app.domain.users.value_objects import PasswordHash, PlainPassword


class PasswordHasher(ABC):
    @abstractmethod
    def hash(
        self,
        password: PlainPassword,
    ) -> PasswordHash: ...

    @abstractmethod
    def verify(
        self,
        password: PlainPassword,
        password_hash: PasswordHash,
    ) -> bool: ...
