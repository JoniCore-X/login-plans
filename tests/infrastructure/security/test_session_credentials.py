from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
)
from app.infrastructure.security.session_credentials import (
    SecureSessionCredentialGenerator,
)


def test_generate_produces_credential() -> None:
    generator = SecureSessionCredentialGenerator()

    credential = generator.generate()

    assert isinstance(credential, SessionCredential)
    assert len(credential.value) > 32


def test_generate_produces_different_values() -> None:
    generator = SecureSessionCredentialGenerator()

    credential_a = generator.generate()
    credential_b = generator.generate()

    assert credential_a != credential_b


def test_hash_is_deterministic() -> None:
    generator = SecureSessionCredentialGenerator()
    credential = SessionCredential("some-credential")

    first = generator.hash(credential)
    second = generator.hash(credential)

    assert first == second
    assert isinstance(first, SessionCredentialHash)
    assert len(first.value) == 64


def test_verify_accepts_correct_credential() -> None:
    generator = SecureSessionCredentialGenerator()
    credential = generator.generate()
    credential_hash = generator.hash(credential)

    assert generator.verify(
        credential,
        credential_hash,
    )


def test_verify_rejects_wrong_credential() -> None:
    generator = SecureSessionCredentialGenerator()
    credential = generator.generate()
    wrong_credential = generator.generate()
    credential_hash = generator.hash(credential)

    assert not generator.verify(
        wrong_credential,
        credential_hash,
    )


def test_stored_hash_is_not_raw_credential() -> None:
    generator = SecureSessionCredentialGenerator()
    credential = generator.generate()

    credential_hash = generator.hash(credential)

    assert credential_hash.value != credential.value
