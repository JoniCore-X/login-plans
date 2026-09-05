from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.domain.users.entities import User
from app.domain.users.enums import UserStatus
from app.domain.users.exceptions import (
    InvalidUserStateTransition,
)


def test_user_is_created_active() -> None:
    now = datetime.now(UTC)
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    user = User.create(
        user_id=user_id,
        email="USER@example.com",
        password_hash="hashed-password",
        now=now,
    )

    assert user.id.value == user_id
    assert user.email.value == "user@example.com"
    assert user.password_hash.value == "hashed-password"
    assert user.status == UserStatus.ACTIVE
    assert user.created_at == now
    assert user.updated_at == now


def test_user_can_be_suspended() -> None:
    created_at = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    suspended_at = datetime(
        2026,
        1,
        2,
        tzinfo=UTC,
    )

    user = User.create(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        email="user@example.com",
        password_hash="hashed-password",
        now=created_at,
    )

    user.suspend(now=suspended_at)

    assert user.status == UserStatus.SUSPENDED
    assert user.updated_at == suspended_at
    assert user.can_authenticate() is False


def test_suspending_already_suspended_user_is_rejected() -> None:
    now = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    user = User.create(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        email="user@example.com",
        password_hash="hashed-password",
        now=now,
    )

    user.suspend(now=now)

    with pytest.raises(InvalidUserStateTransition):
        user.suspend(now=now)


def test_suspended_user_can_be_activated() -> None:
    created_at = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    activated_at = datetime(
        2026,
        1,
        3,
        tzinfo=UTC,
    )

    user = User.create(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        email="user@example.com",
        password_hash="hashed-password",
        now=created_at,
    )

    user.suspend(now=created_at)
    user.activate(now=activated_at)

    assert user.status == UserStatus.ACTIVE
    assert user.can_authenticate() is True
    assert user.updated_at == activated_at
