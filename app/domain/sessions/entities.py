from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.value_objects import SessionId
from app.domain.users.value_objects import UserId


@dataclass(slots=True)
class Session:
    id: SessionId
    user_id: UserId
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
        now: datetime,
        expires_at: datetime,
    ) -> "Session":
        return cls(
            id=SessionId(session_id),
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            created_at=now,
            expires_at=expires_at,
        )

    def revoke(self, *, now: datetime) -> None:
        self.status = SessionStatus.REVOKED
        self.revoked_at = now

    def is_active(self, *, now: datetime) -> bool:
        if self.status != SessionStatus.ACTIVE:
            return False

        return now < self.expires_at
