import pytest

from app.domain.users.value_objects import (
    PlainPassword,
    WeakPasswordError,
)


def test_accepts_strong_password() -> None:
    password = PlainPassword("C0mpl3x!P@ssw0rd2026")

    assert password.value == "C0mpl3x!P@ssw0rd2026"


def test_rejects_empty_or_whitespace() -> None:
    with pytest.raises(WeakPasswordError, match="empty"):
        PlainPassword("")

    with pytest.raises(WeakPasswordError, match="empty"):
        PlainPassword("   ")


def test_rejects_short_password() -> None:
    with pytest.raises(
        WeakPasswordError,
        match="12 characters",
    ):
        PlainPassword("Short1!abc")


def test_rejects_common_password_case_insensitive() -> None:
    with pytest.raises(WeakPasswordError, match="common"):
        PlainPassword("123456789012")

    with pytest.raises(WeakPasswordError, match="common"):
        PlainPassword("123456789012")


def test_rejects_purely_numeric() -> None:
    with pytest.raises(WeakPasswordError, match="mix"):
        PlainPassword("987654321098")


def test_rejects_purely_alphabetic() -> None:
    with pytest.raises(WeakPasswordError, match="mix"):
        PlainPassword("abcdefghijkl")


def test_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        PlainPassword(123456789012)  # type: ignore[arg-type]
