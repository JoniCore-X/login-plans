from abc import ABC, abstractmethod

from app.domain.value_objects.password import PlainPassword
from app.domain.value_objects.password_hash import PasswordHash


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
