"""
Training Router Package - Digital Training Mode (Exam Mode)

Cortez46: Extracted from monolithic training.py (1,620 lines)
Cortez50: Added integration_endpoints.py for T-IA-Cog and N4 traceability

This package provides modular training functionality:
- schemas.py: Pydantic models for training (extended Cortez50)
- session_storage.py: Redis/memory session management
- helpers.py: Utility functions
- endpoints.py: API route handlers (original endpoints)
- integration_endpoints.py: V2 endpoints with agent integration (Cortez50)

Usage:
    from backend.api.routers.training import router, integration_router
"""

from .endpoints import router
from .integration_endpoints import router as integration_router

__all__ = ["router", "integration_router"]
