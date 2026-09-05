from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SessionId:
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SessionCredential:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Session credential cannot be empty")


@dataclass(frozen=True, slots=True)
class SessionCredentialHash:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Session credential hash cannot be empty")
