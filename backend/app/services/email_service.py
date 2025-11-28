"""Email service for sending verification and notification emails."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.smtp_host or not settings.smtp_username:
            logger.warning("SMTP not configured, skipping email send")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Prefer STARTTLS on port 587; only use implicit TLS for SMTPS (usually port 465)
            use_tls = settings.smtp_use_tls
            start_tls = settings.smtp_start_tls
            if settings.smtp_port == 587 and use_tls:
                logger.warning(
                    "SMTP_USE_TLS=True with port 587 detected, switching to STARTTLS to avoid SSL errors"
                )
                use_tls = False
                start_tls = True

            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=use_tls,
                start_tls=start_tls,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    async def send_verification_email(email: str, verification_token: str) -> bool:
        """
        Send email verification email.

        Args:
            email: User email address
            verification_token: Verification token

        Returns:
            True if email sent successfully, False otherwise
        """
        # In production, you would have a proper frontend URL
        # For now, we'll construct a simple verification link
        verification_url = (
            f"{settings.backend_url}/api/auth/verify-email?token={verification_token}"
        )

        subject = "Verify your Auto Poster account"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to Auto Poster!</h2>
                <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                <a href="{verification_url}" class="button">Verify Email Address</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p>This verification link will expire in 24 hours.</p>
                <div class="footer">
                    <p>If you didn't create an account with Auto Poster, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Auto Poster!

        Thank you for registering. Please verify your email address by visiting:

        {verification_url}

        This verification link will expire in 24 hours.

        If you didn't create an account with Auto Poster, you can safely ignore this email.
        """

        return await EmailService.send_email(email, subject, html_content, text_content)

    @staticmethod
    async def send_password_reset_email(email: str, reset_token: str) -> bool:
        """
        Send password reset email.

        Args:
            email: User email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        # This is a placeholder for future password reset functionality
        reset_url = f"{settings.backend_url}/api/auth/reset-password?token={reset_token}"

        subject = "Reset your Auto Poster password"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #EF4444;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password. Click the button below to proceed:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p>This reset link will expire in 1 hour.</p>
                <div class="footer">
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        You requested to reset your password. Visit the following link:

        {reset_url}

        This reset link will expire in 1 hour.

        If you didn't request a password reset, you can safely ignore this email.
        """

        return await EmailService.send_email(email, subject, html_content, text_content)
