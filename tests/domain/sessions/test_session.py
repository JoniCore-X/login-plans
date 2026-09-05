from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domain.sessions.entities import Session
from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.exceptions import (
    InvalidSessionStateTransition,
)
from app.domain.sessions.value_objects import SessionCredentialHash
from app.domain.users.value_objects import UserId


def test_session_is_created_active() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=24)
    session_id = UUID("00000000-0000-0000-0000-000000000001")
    user_id = UserId(UUID("00000000-0000-0000-0000-000000000002"))
    credential_hash = SessionCredentialHash("a" * 64)
    family_id = uuid4()

    session = Session.create(
        session_id=session_id,
        user_id=user_id,
        credential_hash=credential_hash,
        family_id=family_id,
        now=now,
        expires_at=expires_at,
    )

    assert session.id.value == session_id
    assert session.user_id == user_id
    assert session.credential_hash == credential_hash
    assert session.family_id == family_id
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
        credential_hash=SessionCredentialHash("a" * 64),
        now=now,
        expires_at=expires_at,
    )

    assert session.is_active(now=expires_at) is False


def test_active_session_can_be_rotated() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=1)
    rotated_at = now + timedelta(minutes=30)

    session = Session.create(
        session_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000002")),
        credential_hash=SessionCredentialHash("a" * 64),
        family_id=uuid4(),
        now=now,
        expires_at=expires_at,
    )

    session.rotate(now=rotated_at)

    assert session.status == SessionStatus.ROTATED
    assert session.was_rotated() is True
    assert session.revoked_at == rotated_at
    assert session.is_active(now=now) is False


def test_rotating_non_active_session_is_rejected() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=1)

    session = Session.create(
        session_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000002")),
        credential_hash=SessionCredentialHash("a" * 64),
        now=now,
        expires_at=expires_at,
    )

    session.rotate(now=now)

    with pytest.raises(InvalidSessionStateTransition):
        session.rotate(now=now)


def test_revoked_session_is_not_active() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = now + timedelta(hours=1)
    revoked_at = now + timedelta(minutes=30)

    session = Session.create(
        session_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000002")),
        credential_hash=SessionCredentialHash("a" * 64),
        now=now,
        expires_at=expires_at,
    )

    session.revoke(now=revoked_at)

    assert session.status == SessionStatus.REVOKED
    assert session.revoked_at == revoked_at
    assert session.is_active(now=now) is False
