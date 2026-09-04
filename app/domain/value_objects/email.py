from dataclasses import dataclass

from app.domain.exceptions.user import InvalidEmailError


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()

        if not normalized:
            raise InvalidEmailError(
                "Email cannot be empty",
            )

        if "@" not in normalized:
            raise InvalidEmailError(
                "Invalid email",
            )

        object.__setattr__(
            self,
            "value",
            normalized,
        )
