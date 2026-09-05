from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.domain.sessions.entities import Session
from app.domain.sessions.enums import SessionStatus
from app.domain.users.value_objects import UserId


def test_session_is_created_active() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=24)
    session_id = UUID("00000000-0000-0000-0000-000000000001")
    user_id = UserId(UUID("00000000-0000-0000-0000-000000000002"))

    session = Session.create(
        session_id=session_id,
        user_id=user_id,
        now=now,
        expires_at=expires_at,
    )

    assert session.id.value == session_id
    assert session.user_id == user_id
    assert session.status == SessionStatus.ACTIVE
    assert session.created_at == now
    assert session.expires_at == expires_at
    assert session.revoked_at is None
    assert session.is_active(now=now) is True


def test_session_is_not_active_after_expiry() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=1)

    session = Session.create(
        session_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000002")),
        now=now,
        expires_at=expires_at,
    )

    assert session.is_active(now=expires_at) is False


def test_revoked_session_is_not_active() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=1)
    revoked_at = now + timedelta(minutes=30)

    session = Session.create(
        session_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000002")),
        now=now,
        expires_at=expires_at,
    )

    session.revoke(now=revoked_at)

    assert session.status == SessionStatus.REVOKED
    assert session.revoked_at == revoked_at
    assert session.is_active(now=now) is False
