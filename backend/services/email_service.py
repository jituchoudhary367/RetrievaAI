"""
services/email_service.py

Email delivery via SMTP (default), SES, or SendGrid.
"""

import logging
from abc import ABC, abstractmethod
from email.message import EmailMessage
import smtplib

from app.config import get_settings
from services.email_templates import render_verification_email, render_password_reset_email

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> None:
        pass


class SmtpEmailSender(EmailSender):
    def __init__(self):
        self.settings = get_settings().email

    def send(self, to: str, subject: str, html_body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.settings.from_name} <{self.settings.from_address}>"
        msg["To"] = to
        msg.set_content("Please enable HTML to view this email.")
        msg.add_alternative(html_body, subtype='html')

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.send_message(msg)
        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to}: {e}")
            # in a real app, we might retry or queue this
            pass


class SesEmailSender(EmailSender):
    def __init__(self):
        try:
            import boto3
            self.client = boto3.client('ses', region_name=get_settings().email.ses_region)
        except ImportError:
            raise ImportError("boto3 is not installed. Please install it to use SES.")
        
        self.settings = get_settings().email

    def send(self, to: str, subject: str, html_body: str) -> None:
        try:
            self.client.send_email(
                Source=f"{self.settings.from_name} <{self.settings.from_address}>",
                Destination={'ToAddresses': [to]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_body}}
                }
            )
        except Exception as e:
            logger.error(f"Failed to send email via SES to {to}: {e}")


class SendgridEmailSender(EmailSender):
    def __init__(self):
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            self.sendgrid = sendgrid
            self.Mail = Mail
            self.sg = sendgrid.SendGridAPIClient(api_key=get_settings().email.sendgrid_api_key)
        except ImportError:
            raise ImportError("sendgrid is not installed. Please install it to use SendGrid.")
        
        self.settings = get_settings().email

    def send(self, to: str, subject: str, html_body: str) -> None:
        message = self.Mail(
            from_email=(self.settings.from_address, self.settings.from_name),
            to_emails=to,
            subject=subject,
            html_content=html_body
        )
        try:
            self.sg.send(message)
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {to}: {e}")


class EmailService:
    def __init__(self):
        self.settings = get_settings()
        provider = self.settings.email.provider.lower()
        if provider == "ses":
            self.sender = SesEmailSender()
        elif provider == "sendgrid":
            self.sender = SendgridEmailSender()
        else:
            self.sender = SmtpEmailSender()

    def send_verification_email(self, to: str, token: str) -> None:
        base_url = self.settings.frontend_base_url.rstrip("/")
        link = f"{base_url}/verify-email?token={token}"
        subject, html_body = render_verification_email(link)
        self.sender.send(to, subject, html_body)

    def send_password_reset_email(self, to: str, token: str) -> None:
        base_url = self.settings.frontend_base_url.rstrip("/")
        link = f"{base_url}/reset-password?token={token}"
        subject, html_body = render_password_reset_email(link)
        self.sender.send(to, subject, html_body)
