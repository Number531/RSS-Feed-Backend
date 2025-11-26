"""
Security headers middleware for production hardening.

Adds essential security headers to all HTTP responses to protect against
common web vulnerabilities (XSS, clickjacking, MIME-sniffing, etc.).
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevent MIME-sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter in browsers
    - Strict-Transport-Security: Enforce HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = settings.is_production
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevent MIME-sniffing
        # Browsers should not try to detect content type, use declared type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevent clickjacking
        # Page cannot be embedded in iframe/frame/object
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: Enable browser XSS filter
        # Modern browsers have XSS filter, enable with blocking mode
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict-Transport-Security (HSTS): Enforce HTTPS
        # Only add in production (requires HTTPS to be meaningful)
        if self.is_production:
            # max-age=31536000 = 1 year
            # includeSubDomains: Apply to all subdomains
            # preload: Allow inclusion in browser HSTS preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content-Security-Policy: Restrict resource loading
        # - default-src 'self': Only load resources from same origin by default
        # - script-src 'self' 'unsafe-inline': Allow inline scripts (needed for some frameworks)
        # - style-src 'self' 'unsafe-inline': Allow inline styles (needed for some frameworks)
        # - img-src 'self' data: https:: Allow images from same origin, data URIs, and HTTPS
        # - font-src 'self' data:: Allow fonts from same origin and data URIs
        # - connect-src 'self': Allow API calls to same origin only
        # - frame-ancestors 'none': Don't allow embedding (redundant with X-Frame-Options)
        # - base-uri 'self': Restrict base tag to same origin
        # - form-action 'self': Forms can only submit to same origin
        
        # Note: For APIs, CSP is less critical since we're not serving HTML
        # This is a permissive policy suitable for API backends serving some static content
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response
