from tests.factories import user_factory


def test_user_can_be_created() -> None:
    user = user_factory(
        email="user@example.com",
        password_hash="hashed-password",
    )

    assert user.email.value == "user@example.com"
    assert user.password_hash.value == "hashed-password"
