import structlog

from app.application.ports.email_sender import EmailSender

logger = structlog.get_logger(__name__)


class ConsoleEmailSender(EmailSender):
    def __init__(
        self,
        is_production: bool = False,
    ) -> None:
        self.is_production = is_production

    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None:
        if not self.is_production:
            print(
                f"\n{'=' * 60}\n"
                f"VERIFICATION TOKEN FOR: {to}\n"
                f"TOKEN: {token}\n"
                f"{'=' * 60}\n",
            )

        await logger.ainfo(
            "verification_email_sent",
            email=to,
            token=token if not self.is_production else "***",
        )
