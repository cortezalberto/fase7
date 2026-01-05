"""
Middleware para la API REST

FIX Cortez83: Added security_headers module
"""
from .error_handler import setup_exception_handlers
from .logging import setup_logging_middleware
from .security_headers import setup_security_headers

__all__ = [
    "setup_exception_handlers",
    "setup_logging_middleware",
    "setup_security_headers",
]