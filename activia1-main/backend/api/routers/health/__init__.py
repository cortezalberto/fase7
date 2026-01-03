"""
Health Check Router Package

Cortez66: Modularized from single health.py (758 lines)

Structure:
- probes.py: Kubernetes liveness/readiness probes (lightweight)
- diagnostics.py: Deep health checks with metrics (heavyweight)
- utils.py: Shared utilities (memory, gc stats)
"""
from fastapi import APIRouter

from .probes import router as probes_router
from .diagnostics import router as diagnostics_router

# Main router that includes all sub-routers
router = APIRouter(prefix="/health", tags=["Health"])

# Include probe endpoints (lightweight)
router.include_router(probes_router)

# Include diagnostics endpoints (heavyweight)
router.include_router(diagnostics_router)

__all__ = ["router"]
