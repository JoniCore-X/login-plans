import pytest

from app.domain.exceptions.user import InvalidEmailError
from app.domain.value_objects.email import Email


def test_email_is_normalized() -> None:
    email = Email("  USER@Example.COM ")

    assert email.value == "user@example.com"


def test_empty_email_is_rejected() -> None:
    with pytest.raises(InvalidEmailError):
        Email("")


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(InvalidEmailError):
        Email("invalid-email")
