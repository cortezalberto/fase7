"""
Simulators Router Package - Professional Role Simulators (S-IA-X)

Cortez46: Extracted from monolithic simulators.py (1,589 lines)

This package provides modular simulator functionality:
- core.py: Core simulator endpoints (list, interact, info) + sub-router mounting
- interview.py: Technical interview simulation endpoints (IT-IA)
- incident.py: Incident response simulation endpoints (IR-IA)
- sprint6.py: Sprint 6 advanced simulators (SM-IA, CX-IA, DSO-IA)

Sprint 3 - HU-EST-009, HU-SYS-006
Sprint 6 - HU-EST-010, HU-EST-011, HU-EST-012, HU-EST-013, HU-EST-014

Usage:
    from backend.api.routers.simulators import router
"""

from .core import router

__all__ = ["router"]
