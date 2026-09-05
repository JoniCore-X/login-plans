import hashlib
import hmac
import secrets

from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
)


class SecureSessionCredentialGenerator(
    SessionCredentialGenerator,
):
    def generate(self) -> SessionCredential:
        token = secrets.token_urlsafe(32)

        return SessionCredential(
            value=token,
        )

    def hash(
        self,
        credential: SessionCredential,
    ) -> SessionCredentialHash:
        digest = hashlib.sha256(
            credential.value.encode("utf-8"),
        ).hexdigest()

        return SessionCredentialHash(
            value=digest,
        )

    def verify(
        self,
        credential: SessionCredential,
        credential_hash: SessionCredentialHash,
    ) -> bool:
        candidate = self.hash(
            credential,
        )

        return hmac.compare_digest(
            candidate.value,
            credential_hash.value,
        )
