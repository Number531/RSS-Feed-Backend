"""
Email service for sending transactional emails.

Handles SMTP configuration, email template rendering, and sending
verification emails with proper error handling.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS
    
    def _is_configured(self) -> bool:
        """
        Check if SMTP is properly configured.
        
        Returns:
            True if SMTP settings are configured, False otherwise
        """
        return bool(
            self.smtp_host 
            and self.smtp_user 
            and self.smtp_password
        )
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Create email message with HTML and optional text fallback.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            
        Returns:
            Configured MIMEMultipart message
        """
        message = MIMEMultipart("alternative")
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add text part if provided
        if text_body:
            text_part = MIMEText(text_body, "plain")
            message.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        return message
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._is_configured():
            logger.warning(
                "SMTP not configured, cannot send email",
                extra={"to": to_email, "subject": subject}
            )
            return False
        
        try:
            # Create message
            message = self._create_message(to_email, subject, html_body, text_body)
            
            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            # Login and send
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(message)
            server.quit()
            
            logger.info(
                f"Email sent successfully to {to_email}",
                extra={"to": to_email, "subject": subject}
            )
            return True
            
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error sending email: {e}",
                extra={"to": to_email, "subject": subject, "error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending email: {e}",
                extra={"to": to_email, "subject": subject, "error": str(e)}
            )
            return False
    
    async def send_verification_email(
        self,
        to_email: str,
        username: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification email to user.
        
        Args:
            to_email: User's email address
            username: User's username
            verification_token: Verification token for URL
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Build verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        # Email subject
        subject = "Verify your email address"
        
        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify your email</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin-bottom: 20px;">
                <h1 style="color: #1a1a1a; margin-top: 0;">Welcome to {settings.APP_NAME}!</h1>
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Hi <strong>{username}</strong>,
                </p>
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Thank you for registering! Please verify your email address to activate your account.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: 500;">
                        Verify Email Address
                    </a>
                </div>
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Or copy and paste this link into your browser:
                </p>
                <p style="font-size: 14px; color: #007bff; word-break: break-all;">
                    {verification_url}
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="font-size: 13px; color: #999;">
                    This link will expire in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hour(s). 
                    If you didn't create an account, you can safely ignore this email.
                </p>
            </div>
            <p style="font-size: 12px; color: #999; text-align: center;">
                &copy; 2024 {settings.APP_NAME}. All rights reserved.
            </p>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_body = f"""
Welcome to {settings.APP_NAME}!

Hi {username},

Thank you for registering! Please verify your email address to activate your account.

Verification link:
{verification_url}

This link will expire in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hour(s).

If you didn't create an account, you can safely ignore this email.

---
{settings.APP_NAME}
        """.strip()
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )


# Global email service instance
email_service = EmailService()
