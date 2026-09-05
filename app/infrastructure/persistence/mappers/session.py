from app.domain.sessions.entities import Session
from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.value_objects import SessionId
from app.domain.users.value_objects import UserId
from app.infrastructure.persistence.models.session import SessionModel


def session_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,
        user_id=session.user_id.value,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )


def session_to_domain(model: SessionModel) -> Session:
    return Session(
        id=SessionId(model.id),
        user_id=UserId(model.user_id),
        status=SessionStatus(model.status),
        created_at=model.created_at,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
    )
