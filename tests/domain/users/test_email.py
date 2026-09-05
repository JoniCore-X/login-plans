import pytest

from app.domain.users.value_objects import (
    Email,
    InvalidEmailError,
)


def test_email_is_normalized() -> None:
    email = Email("  USER@Example.COM ")

    assert email.value == "user@example.com"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "invalid",
        "@example.com",
        "user@",
        "user example@example.com",
    ],
)
def test_invalid_email_is_rejected(value: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(value)


def test_email_is_immutable() -> None:
    email = Email("user@example.com")

    with pytest.raises(AttributeError):
        email.value = "other@example.com"  # type: ignore[misc]
