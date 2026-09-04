from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()

        if not normalized:
            raise ValueError("Email cannot be empty")

        if "@" not in normalized:
            raise ValueError("Invalid email")

        object.__setattr__(self, "value", normalized)
