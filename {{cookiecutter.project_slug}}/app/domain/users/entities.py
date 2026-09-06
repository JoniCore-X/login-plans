import hmac
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.events import (
    DomainEvent,
    EmailVerified,
    PasswordChanged,
)
from app.domain.users.enums import UserStatus
from app.domain.users.exceptions import (
    InvalidUserStateTransition,
    InvalidVerificationTokenError,
)
from app.domain.users.value_objects import (
    Email,
    PasswordHash,
    UserId,
)


@dataclass(slots=True)
class User:
    id: UserId
    email: Email
    password_hash: PasswordHash
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    email_verified_at: datetime | None = None
    verification_token_hash: str | None = None
    verification_token_expires_at: datetime | None = None
    _events: list[DomainEvent] = field(
        default_factory=list,
        repr=False,
    )

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events

    def change_password(
        self,
        *,
        new_hash: PasswordHash,
        now: datetime,
    ) -> None:
        self.password_hash = new_hash
        self.updated_at = now

        self.register_event(
            PasswordChanged(
                occurred_at=now,
                user_id=self.id.value,
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        email: str,
        password_hash: str,
        now: datetime,
    ) -> "User":
        return cls(
            id=UserId(user_id),
            email=Email(email),
            password_hash=PasswordHash(password_hash),
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def suspend(self, *, now: datetime) -> None:
        if self.status == UserStatus.SUSPENDED:
            raise InvalidUserStateTransition(
                "User is already suspended.",
            )

        self.status = UserStatus.SUSPENDED
        self.updated_at = now

    def deactivate(self, *, now: datetime) -> None:
        if self.status == UserStatus.INACTIVE:
            raise InvalidUserStateTransition(
                "User is already inactive.",
            )

        self.status = UserStatus.INACTIVE
        self.updated_at = now

    def activate(self, *, now: datetime) -> None:
        if self.status == UserStatus.ACTIVE:
            raise InvalidUserStateTransition(
                "User is already active.",
            )

        self.status = UserStatus.ACTIVE
        self.updated_at = now

    def start_email_verification(
        self,
        *,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        self.verification_token_hash = token_hash
        self.verification_token_expires_at = expires_at

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    def verify_email(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> None:
        if self.is_email_verified:
            raise InvalidVerificationTokenError(
                "Email is already verified.",
            )

        if (
            self.verification_token_hash is None
            or self.verification_token_expires_at is None
        ):
            raise InvalidVerificationTokenError(
                "Invalid verification token.",
            )

        if not hmac.compare_digest(
            self.verification_token_hash,
            token_hash,
        ):
            raise InvalidVerificationTokenError(
                "Invalid verification token.",
            )

        if now > self.verification_token_expires_at:
            raise InvalidVerificationTokenError(
                "Verification token has expired.",
            )

        self.email_verified_at = now
        self.verification_token_hash = None
        self.verification_token_expires_at = None
        self.updated_at = now

        self.register_event(
            EmailVerified(
                occurred_at=now,
                user_id=self.id.value,
            ),
        )

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def can_authenticate(self) -> bool:
        return self.status == UserStatus.ACTIVE
