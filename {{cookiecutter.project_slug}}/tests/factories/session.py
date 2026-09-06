import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.sessions.entities import Session
from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.value_objects import (
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.value_objects import UserId


def session_factory(
    *,
    session_id: UUID | None = None,
    user_id: UUID | None = None,
    credential_hash: str | None = None,
    family_id: UUID | None = None,
    status: SessionStatus = SessionStatus.ACTIVE,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
) -> Session:
    now = datetime.now(UTC)

    return Session(
        id=SessionId(session_id or uuid4()),
        user_id=UserId(user_id or uuid4()),
        credential_hash=SessionCredentialHash(
            credential_hash
            or hashlib.sha256(
                str(uuid4()).encode("utf-8"),
            ).hexdigest(),
        ),
        family_id=family_id or uuid4(),
        status=status,
        created_at=created_at or now,
        expires_at=expires_at or (now + timedelta(hours=24)),
        revoked_at=revoked_at,
    )
