from abc import ABC, abstractmethod

from app.domain.repositories.unit_of_work import UnitOfWork


class UnitOfWorkFactory(ABC):
    @abstractmethod
    def create(self) -> UnitOfWork: ...
