from abc import ABC, abstractmethod

from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
)


class SessionCredentialGenerator(ABC):
    @abstractmethod
    def generate(self) -> SessionCredential:
        raise NotImplementedError

    @abstractmethod
    def hash(
        self,
        credential: SessionCredential,
    ) -> SessionCredentialHash:
        raise NotImplementedError

    @abstractmethod
    def verify(
        self,
        credential: SessionCredential,
        credential_hash: SessionCredentialHash,
    ) -> bool:
        raise NotImplementedError
