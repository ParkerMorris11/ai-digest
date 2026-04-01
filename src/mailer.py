"""Gmail SMTP sender for AI Digest."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import Config
from .fetchers import SSL_CONTEXT


logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 465


def send_email(
    config: Config,
    subject: str,
    html_body: str,
    plain_body: str,
) -> bool:
    """Send a multipart/alternative email via Gmail SMTP over SSL.

    Returns True on success, False on failure.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.gmail_address
    msg["To"] = config.recipient_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info("Sending email to %s...", config.recipient_email)
    try:
        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, context=SSL_CONTEXT) as server:
            server.login(config.gmail_address, config.gmail_app_password)
            server.sendmail(config.gmail_address, config.recipient_email, msg.as_string())
        logger.info("Email sent successfully.")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. Verify your Gmail address and App Password."
        )
    except smtplib.SMTPException as exc:
        logger.error("Failed to send email: %s", exc)
    return False
