import logging

from app.application.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None:
        logger.info(
            "Verification email for %s: /api/v1/auth/verify-email?token=%s",
            to,
            token,
        )
