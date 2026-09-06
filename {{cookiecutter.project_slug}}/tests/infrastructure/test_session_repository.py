import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.sessions.enums import SessionStatus
from app.infrastructure.persistence.repositories.session import (
    PostgresSessionRepository,
)
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)
from tests.factories import session_factory, user_factory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_repository_can_persist_session(
    test_session: AsyncSession,
) -> None:
    user_repository = PostgresUserRepository(
        test_session,
    )
    session_repository = PostgresSessionRepository(
        test_session,
    )

    user = user_factory()

    await user_repository.add(user)

    await test_session.flush()

    session = session_factory(
        user_id=user.id.value,
    )

    await session_repository.add(session)

    await test_session.flush()

    stored_session = await session_repository.get_by_id(
        session.id,
    )

    assert stored_session is not None
    assert stored_session.id == session.id
    assert stored_session.user_id == user.id
    assert stored_session.status == SessionStatus.ACTIVE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_repository_finds_session_by_credential_hash(
    test_session: AsyncSession,
) -> None:
    from app.domain.sessions.value_objects import SessionCredentialHash

    user_repository = PostgresUserRepository(
        test_session,
    )
    session_repository = PostgresSessionRepository(
        test_session,
    )

    user = user_factory()

    await user_repository.add(user)

    await test_session.flush()

    session = session_factory(
        user_id=user.id.value,
    )

    await session_repository.add(session)

    await test_session.flush()

    found = await session_repository.get_by_credential_hash(
        SessionCredentialHash(
            session.credential_hash.value,
        ),
    )

    assert found is not None
    assert found.id == session.id

    missing = await session_repository.get_by_credential_hash(
        SessionCredentialHash("0" * 64),
    )

    assert missing is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_repository_can_revoke_session(
    test_session: AsyncSession,
) -> None:
    from datetime import UTC, datetime

    user_repository = PostgresUserRepository(
        test_session,
    )
    session_repository = PostgresSessionRepository(
        test_session,
    )

    user = user_factory()

    await user_repository.add(user)

    await test_session.flush()

    session = session_factory(
        user_id=user.id.value,
    )

    await session_repository.add(session)

    await test_session.flush()

    session.revoke(
        now=datetime.now(UTC),
    )

    await session_repository.revoke(session)

    await test_session.flush()

    stored_session = await session_repository.get_by_id(
        session.id,
    )

    assert stored_session is not None
    assert stored_session.status == SessionStatus.REVOKED
    assert stored_session.revoked_at is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_repository_lists_sessions_by_user(
    test_session: AsyncSession,
) -> None:
    user_repository = PostgresUserRepository(
        test_session,
    )
    session_repository = PostgresSessionRepository(
        test_session,
    )

    user = user_factory()

    await user_repository.add(user)

    await test_session.flush()

    first = session_factory(user_id=user.id.value)
    second = session_factory(user_id=user.id.value)

    await session_repository.add(first)
    await session_repository.add(second)

    await test_session.flush()

    sessions = await session_repository.get_by_user_id(
        user.id,
    )

    assert len(sessions) == 2
    assert all(session.user_id == user.id for session in sessions)
