import smtplib

import pytest

from app.core.exceptions import MailDeliveryError
from app.infrastructure.services.mail import SMTPMailService
from tests.utils import run


class _FakeSMTP:
    sent_messages = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def send_message(self, message):
        self.sent_messages.append((self.host, self.port, self.timeout, message))


def test_smtp_mail_service_sends_registration_code(monkeypatch):
    _FakeSMTP.sent_messages = []
    monkeypatch.setattr("app.infrastructure.services.mail.smtp_mail_service.smtplib.SMTP", _FakeSMTP)

    service = SMTPMailService(
        host="mail",
        port=1025,
        mail_from="no-reply@schemion.local",
        timeout_seconds=7,
    )

    run(service.send_registration_confirmation("user@example.com", "123456"))

    host, port, timeout, message = _FakeSMTP.sent_messages[0]
    assert (host, port, timeout) == ("mail", 1025, 7)
    assert message["From"] == "no-reply@schemion.local"
    assert message["To"] == "user@example.com"
    assert message["Subject"] == "Registration confirmation"
    assert message.get_content() == "Code: 123456\n"


def test_smtp_mail_service_wraps_smtp_errors(monkeypatch):
    class BrokenSMTP(_FakeSMTP):
        def send_message(self, message):
            raise smtplib.SMTPException("boom")

    monkeypatch.setattr("app.infrastructure.services.mail.smtp_mail_service.smtplib.SMTP", BrokenSMTP)

    service = SMTPMailService(
        host="mail",
        port=1025,
        mail_from="no-reply@schemion.local",
        timeout_seconds=7,
    )

    with pytest.raises(MailDeliveryError):
        run(service.send_registration_confirmation("user@example.com", "123456"))
