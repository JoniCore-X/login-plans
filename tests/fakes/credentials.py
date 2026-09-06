from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
)


class FakeSessionCredentialGenerator(SessionCredentialGenerator):
    def __init__(self) -> None:
        self.counter = 0

    def generate(self) -> SessionCredential:
        self.counter += 1

        return SessionCredential(
            f"credential-{self.counter}",
        )

    def hash(
        self,
        credential: SessionCredential,
    ) -> SessionCredentialHash:
        return SessionCredentialHash(
            f"hash:{credential.value}",
        )

    def verify(
        self,
        credential: SessionCredential,
        credential_hash: SessionCredentialHash,
    ) -> bool:
        return credential_hash.value == (f"hash:{credential.value}")
