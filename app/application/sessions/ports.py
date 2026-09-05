from abc import ABC, abstractmethod

from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import (
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.value_objects import UserId


class SessionRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        session_id: SessionId,
    ) -> Session | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UserId,
    ) -> list[Session]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_credential_hash(
        self,
        credential_hash: SessionCredentialHash,
    ) -> Session | None:
        raise NotImplementedError

    @abstractmethod
    async def add(
        self,
        session: Session,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke(
        self,
        session: Session,
    ) -> None:
        raise NotImplementedError
