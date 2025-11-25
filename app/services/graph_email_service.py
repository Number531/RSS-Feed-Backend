"""
Microsoft Graph API email service for sending transactional emails.

Uses OAuth 2.0 with application permissions for secure, scalable email delivery.
Provides the same interface as SMTP email service for easy migration.
"""

import logging
from typing import Optional
import requests

from app.core.config import settings
from app.core.graph_auth import graph_auth_manager
from app.utils.email_templates import (
    get_verification_email_html,
    get_verification_email_text,
)

logger = logging.getLogger(__name__)


class GraphEmailService:
    """Service for sending emails via Microsoft Graph API."""
    
    def __init__(self):
        """Initialize Graph API email service."""
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.sender_email = settings.MICROSOFT_SENDER_EMAIL
        self.from_name = settings.SMTP_FROM_NAME  # Reuse from SMTP config
    
    def _is_configured(self) -> bool:
        """
        Check if Graph API is properly configured.
        
        Returns:
            True if Graph API settings are configured, False otherwise
        """
        return bool(self.sender_email and graph_auth_manager._is_configured())
    
    def _create_message_payload(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> dict:
        """
        Create Microsoft Graph API message payload.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            
        Returns:
            Dictionary payload for Graph API sendMail endpoint
        """
        # Determine content type and body
        if html_body and text_body:
            # Prefer HTML but include text as alternative
            content_type = "HTML"
            body_content = html_body
        elif html_body:
            content_type = "HTML"
            body_content = html_body
        else:
            content_type = "Text"
            body_content = text_body or ""
        
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type,
                    "content": body_content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ],
                "from": {
                    "emailAddress": {
                        "address": self.sender_email,
                        "name": self.from_name
                    }
                }
            },
            "saveToSentItems": "false"  # Don't clutter sent items for transactional emails
        }
        
        return payload
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send email via Microsoft Graph API.
        
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
                "Microsoft Graph API not configured, cannot send email",
                extra={"to": to_email, "subject": subject}
            )
            return False
        
        # Get access token
        access_token = graph_auth_manager.get_access_token()
        if not access_token:
            logger.error(
                "Failed to acquire access token for Microsoft Graph API",
                extra={"to": to_email, "subject": subject}
            )
            return False
        
        try:
            # Create message payload
            payload = self._create_message_payload(to_email, subject, html_body, text_body)
            
            # Graph API endpoint for sending mail
            url = f"{self.graph_endpoint}/users/{self.sender_email}/sendMail"
            
            # Send request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Check response
            if response.status_code == 202:
                # 202 Accepted - Email queued successfully
                logger.info(
                    f"Email sent successfully via Graph API to {to_email}",
                    extra={"to": to_email, "subject": subject, "status_code": 202}
                )
                return True
            else:
                # Log error details
                error_data = response.json() if response.content else {}
                logger.error(
                    f"Graph API error sending email: {response.status_code}",
                    extra={
                        "to": to_email,
                        "subject": subject,
                        "status_code": response.status_code,
                        "error": error_data.get("error", {})
                    }
                )
                return False
                
        except requests.exceptions.Timeout:
            logger.error(
                "Timeout sending email via Graph API",
                extra={"to": to_email, "subject": subject}
            )
            return False
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request error sending email via Graph API: {e}",
                extra={"to": to_email, "subject": subject, "error": str(e)}
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending email via Graph API: {e}",
                extra={"to": to_email, "subject": subject, "error": str(e)},
                exc_info=True
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
        
        Uses customizable HTML template from app/templates/email_verification.html.
        Edit that file to match your website's aesthetic.
        
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
        
        # Render HTML from template
        try:
            html_body = get_verification_email_html(
                app_name=settings.APP_NAME,
                username=username,
                verification_url=verification_url,
                expiry_hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS,
            )
        except FileNotFoundError as e:
            logger.error(f"Email template not found: {e}")
            # Fallback to basic HTML if template is missing
            html_body = f"""
            <html>
            <body>
                <h1>Welcome to {settings.APP_NAME}!</h1>
                <p>Hi {username},</p>
                <p>Please verify your email: <a href=\"{verification_url}\">Click here</a></p>
            </body>
            </html>
            """
        
        # Plain text fallback
        text_body = get_verification_email_text(
            app_name=settings.APP_NAME,
            username=username,
            verification_url=verification_url,
            expiry_hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS,
        )
        
        return await self.send_email(to_email, subject, html_body, text_body)


# Global Graph API email service instance
graph_email_service = GraphEmailService()
