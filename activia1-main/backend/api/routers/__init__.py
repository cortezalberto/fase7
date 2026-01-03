"""
API Routers
Todos los endpoints REST del sistema AI-Native

Cortez66: health modularized to health/ package
"""
# Cortez66: Import from modularized health package
from .health import router as health_router
from .sessions import router as sessions_router
from .interactions import router as interactions_router
from .traces import router as traces_router
from .risks import router as risks_router
from .activities import router as activities_router

__all__ = [
    "health_router",
    "sessions_router",
    "interactions_router",
    "traces_router",
    "risks_router",
    "activities_router",
]