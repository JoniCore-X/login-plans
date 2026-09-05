from uuid import UUID

from tests.factories import user_factory


def test_user_can_be_created() -> None:
    user = user_factory(
        email="user@example.com",
        password_hash="hashed-password",
    )

    assert user.email.value == "user@example.com"
    assert user.password_hash.value == "hashed-password"
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None


def test_user_factory_can_create_deterministic_user() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    user = user_factory(
        user_id=user_id,
        email="deterministic@example.com",
        password_hash="deterministic-hash",
    )

    assert user.id == user_id
    assert user.email.value == "deterministic@example.com"
    assert user.password_hash.value == "deterministic-hash"
