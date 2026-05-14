import asyncio
import smtplib
from email.message import EmailMessage

from app.core.exceptions import MailDeliveryError
from app.core.interfaces.mail_interface import IMailService


class SMTPMailService(IMailService):
    def __init__(
            self,
            host: str,
            port: int,
            mail_from: str,
            timeout_seconds: int,
    ):
        self.host = host
        self.port = port
        self.mail_from = mail_from
        self.timeout_seconds = timeout_seconds

    async def send_registration_confirmation(self, email: str, code: str) -> None:
        message = EmailMessage()
        message["From"] = self.mail_from
        message["To"] = email
        message["Subject"] = "Registration confirmation"
        message.set_content(f"Code: {code}")

        await asyncio.to_thread(self._send_message, message)

    def _send_message(self, message: EmailMessage) -> None:
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as smtp:
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise MailDeliveryError("Could not send registration confirmation email") from exc
