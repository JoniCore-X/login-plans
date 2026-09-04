from app.domain.exceptions.base import DomainError


class UserAlreadyExistsError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass
