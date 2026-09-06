import httpx
import structlog

from app.application.ports.email_sender import EmailSender

logger = structlog.get_logger(__name__)

_RESEND_API_URL = "https://api.resend.com/emails"


class ResendEmailSender(EmailSender):
    def __init__(
        self,
        api_key: str,
        from_email: str,
        verify_base_url: str,
    ) -> None:
        self.api_key = api_key
        self.from_email = from_email
        self.verify_base_url = verify_base_url

    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None:
        verification_url = f"{self.verify_base_url}?token={token}"

        payload = {
            "from": self.from_email,
            "to": [to],
            "subject": "Verify your email",
            "html": (
                "<h1>Verify your email</h1>"
                "<p>Click the link below to verify your account:</p>"
                f'<a href="{verification_url}">{verification_url}</a>'
                "<p>This link expires in 24 hours.</p>"
            ),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                _RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            response.raise_for_status()

        await logger.ainfo(
            "verification_email_sent",
            email=to,
            provider="resend",
        )
