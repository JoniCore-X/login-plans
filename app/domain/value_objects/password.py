from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlainPassword:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Password cannot be empty")
