from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    user_id: UUID
    email: str


@dataclass(frozen=True)
class PasswordChanged(DomainEvent):
    user_id: UUID


@dataclass(frozen=True)
class SessionRotated(DomainEvent):
    session_id: UUID
    family_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class SessionRevoked(DomainEvent):
    session_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class ReplayAttackDetected(DomainEvent):
    session_id: UUID
    family_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class PlanCreated(DomainEvent):
    plan_id: UUID
    user_id: UUID
    name: str


@dataclass(frozen=True)
class PlanUpdated(DomainEvent):
    plan_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class PlanPublished(DomainEvent):
    plan_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class PlanArchived(DomainEvent):
    plan_id: UUID
    user_id: UUID
