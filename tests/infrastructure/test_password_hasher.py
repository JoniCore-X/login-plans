from app.infrastructure.security.password_hasher import (
    Argon2PasswordHasher,
)


def test_password_can_be_hashed_and_verified() -> None:
    hasher = Argon2PasswordHasher()

    password = "correct-password"

    password_hash = hasher.hash(password)

    assert password_hash.value != password
    assert password_hash.value.startswith("$argon2id$")

    assert hasher.verify(
        password,
        password_hash,
    )


def test_wrong_password_is_rejected() -> None:
    hasher = Argon2PasswordHasher()

    password_hash = hasher.hash(
        "correct-password",
    )

    assert not hasher.verify(
        "wrong-password",
        password_hash,
    )


def test_same_password_generates_different_hashes() -> None:
    hasher = Argon2PasswordHasher()

    first_hash = hasher.hash(
        "same-password",
    )

    second_hash = hasher.hash(
        "same-password",
    )

    assert first_hash.value != second_hash.value
