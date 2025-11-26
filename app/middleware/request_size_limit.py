"""
Request size limit middleware to prevent DoS attacks via large payloads.

Rejects requests exceeding the configured maximum size before they are
fully read into memory, protecting against memory exhaustion attacks.
"""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces maximum request body size.
    
    Protects against:
    - Memory exhaustion from large payloads
    - DoS attacks via oversized requests
    - Accidental upload of massive files
    
    Returns 413 Payload Too Large if request exceeds limit.
    """
    
    def __init__(self, app: ASGIApp, max_size: int = None):
        """
        Initialize request size limit middleware.
        
        Args:
            app: ASGI application
            max_size: Maximum request size in bytes (defaults to settings.MAX_REQUEST_SIZE)
        """
        super().__init__(app)
        self.max_size = max_size or settings.MAX_REQUEST_SIZE
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size and reject if too large."""
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                content_length_int = int(content_length)
                
                # Reject if exceeds max size
                if content_length_int > self.max_size:
                    # Calculate human-readable sizes
                    max_size_mb = self.max_size / (1024 * 1024)
                    actual_size_mb = content_length_int / (1024 * 1024)
                    
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "message": f"Request body too large. Maximum size: {max_size_mb:.1f}MB, received: {actual_size_mb:.1f}MB",
                            "max_size_bytes": self.max_size,
                            "actual_size_bytes": content_length_int,
                        },
                    )
            except ValueError:
                # Invalid Content-Length header - let it through
                # (will fail with 400 Bad Request later)
                pass
        
        # Continue processing request
        return await call_next(request)
