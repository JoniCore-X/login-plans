from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.exceptions import InvalidSessionStateTransition
from app.domain.sessions.value_objects import (
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.value_objects import UserId


@dataclass(slots=True)
class Session:
    id: SessionId
    user_id: UserId
    credential_hash: SessionCredentialHash
    family_id: UUID
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        session_id: UUID,
        user_id: UserId,
        credential_hash: SessionCredentialHash,
        family_id: UUID | None = None,
        now: datetime,
        expires_at: datetime,
    ) -> "Session":
        return cls(
            id=SessionId(session_id),
            user_id=user_id,
            credential_hash=credential_hash,
            family_id=family_id or uuid4(),
            status=SessionStatus.ACTIVE,
            created_at=now,
            expires_at=expires_at,
        )

    def rotate(self, *, now: datetime) -> None:
        if self.status != SessionStatus.ACTIVE:
            raise InvalidSessionStateTransition(
                "Only an active session can be rotated.",
            )

        self.status = SessionStatus.ROTATED
        self.revoked_at = now

    def revoke(self, *, now: datetime) -> None:
        self.status = SessionStatus.REVOKED
        self.revoked_at = now

    def is_active(self, *, now: datetime) -> bool:
        if self.status != SessionStatus.ACTIVE:
            return False

        return now < self.expires_at

    def was_rotated(self) -> bool:
        return self.status == SessionStatus.ROTATED
