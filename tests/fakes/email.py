from app.application.ports.email_sender import EmailSender


class FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.sent_verification_emails: list[tuple[str, str]] = []

    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None:
        self.sent_verification_emails.append((to, token))
