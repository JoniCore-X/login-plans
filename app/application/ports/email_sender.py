from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None:
        raise NotImplementedError
