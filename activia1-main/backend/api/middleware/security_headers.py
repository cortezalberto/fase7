"""
Security Headers Middleware - OWASP recommended security headers.

FIX Cortez83 HIGH-SEC-001: Add security headers middleware

Provides:
- setup_security_headers: Configures security headers for all responses
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff - Prevents MIME type sniffing
    - X-Frame-Options: DENY - Prevents clickjacking attacks
    - X-XSS-Protection: 1; mode=block - Legacy XSS protection (deprecated but still useful)
    - Referrer-Policy: strict-origin-when-cross-origin - Controls referrer information
    - Content-Security-Policy: Restricts resource loading
    - Permissions-Policy: Restricts browser features
    - Strict-Transport-Security: Enforces HTTPS (when enabled)
    """

    def __init__(self, app, enable_hsts: bool = False):
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (relaxed for API, stricter for frontend)
        # Allow same-origin scripts and connections
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp

        # Permissions Policy (disable unused browser features)
        permissions = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        response.headers["Permissions-Policy"] = permissions

        # HSTS - Only enable in production with HTTPS
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


def setup_security_headers(app: FastAPI, enable_hsts: bool = False) -> None:
    """
    Configure security headers middleware for the application.

    Args:
        app: FastAPI application instance
        enable_hsts: Whether to enable HSTS (only enable with HTTPS)
    """
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)
    logger.info(
        "Security headers middleware configured",
        extra={"hsts_enabled": enable_hsts}
    )
