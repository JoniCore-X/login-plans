from abc import ABC, abstractmethod

from app.domain.value_objects.password_hash import PasswordHash


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> PasswordHash: ...

    @abstractmethod
    def verify(
        self,
        password: str,
        password_hash: PasswordHash,
    ) -> bool: ...
