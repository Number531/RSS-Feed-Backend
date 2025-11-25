"""
Microsoft Graph API authentication using OAuth 2.0.

Handles token acquisition and refresh for application permissions
using the client credentials flow (daemon app).
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import msal

from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphAuthManager:
    """
    Manages OAuth 2.0 authentication for Microsoft Graph API.
    
    Uses MSAL (Microsoft Authentication Library) for token management
    with automatic caching and refresh.
    """
    
    def __init__(self):
        """Initialize Graph API authentication manager."""
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        # MSAL confidential client application
        self._app: Optional[msal.ConfidentialClientApplication] = None
        self._token_cache = {}
        self._token_expiry: Optional[datetime] = None
    
    def _is_configured(self) -> bool:
        """
        Check if Graph API credentials are properly configured.
        
        Returns:
            True if all required credentials are set, False otherwise
        """
        return bool(
            self.client_id
            and self.client_secret
            and self.tenant_id
        )
    
    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        """
        Get or create MSAL application instance.
        
        Returns:
            Configured MSAL confidential client application
        """
        if not self._app:
            self._app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )
        return self._app
    
    def _is_token_valid(self) -> bool:
        """
        Check if current token is still valid.
        
        Returns:
            True if token exists and hasn't expired (with 5 min buffer)
        """
        if not self._token_cache or not self._token_expiry:
            return False
        
        # Add 5 minute buffer to avoid using token right before expiry
        buffer = timedelta(minutes=5)
        return datetime.utcnow() < (self._token_expiry - buffer)
    
    def get_access_token(self) -> Optional[str]:
        """
        Get valid access token for Microsoft Graph API.
        
        Automatically handles token caching and refresh. Uses application
        permissions (client credentials flow) for daemon scenarios.
        
        Returns:
            Valid access token string, or None if authentication fails
        """
        if not self._is_configured():
            logger.error("Microsoft Graph API credentials not configured")
            return None
        
        # Return cached token if still valid
        if self._is_token_valid():
            return self._token_cache.get("access_token")
        
        try:
            app = self._get_msal_app()
            
            # First, check token cache
            result = app.acquire_token_silent(
                scopes=self.scopes,
                account=None  # Application permissions don't use accounts
            )
            
            # If no cached token, acquire new token
            if not result:
                logger.info("Acquiring new access token from Microsoft Graph API")
                result = app.acquire_token_for_client(scopes=self.scopes)
            
            # Check for errors
            if "error" in result:
                logger.error(
                    f"Failed to acquire token: {result.get('error')} - {result.get('error_description')}",
                    extra={
                        "error": result.get("error"),
                        "description": result.get("error_description")
                    }
                )
                return None
            
            # Cache token and expiry
            self._token_cache = result
            expires_in = result.get("expires_in", 3600)  # Default 1 hour
            self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info(
                "Successfully acquired access token",
                extra={"expires_in": expires_in}
            )
            
            return result.get("access_token")
            
        except Exception as e:
            logger.error(
                f"Unexpected error acquiring access token: {e}",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    def clear_cache(self) -> None:
        """Clear cached token. Useful for testing or forced refresh."""
        self._token_cache = {}
        self._token_expiry = None
        logger.info("Token cache cleared")


# Global auth manager instance
graph_auth_manager = GraphAuthManager()
