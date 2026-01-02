"""
Security Audit Analyzers Package

Cortez44: Modularized from analyze-security.py (494 lines)

This package provides modular security analysis components:
- base.py: BaseAnalyzer abstract class and common utilities
- zap_analyzer.py: OWASP ZAP report analysis
- trivy_analyzer.py: Trivy vulnerability report analysis
- kubesec_analyzer.py: Kubesec Kubernetes security analysis
- trufflehog_analyzer.py: TruffleHog secrets detection analysis
- report_generator.py: Report generation and formatting
"""

from .base import BaseAnalyzer, SecurityFindings
from .zap_analyzer import ZapAnalyzer
from .trivy_analyzer import TrivyAnalyzer
from .kubesec_analyzer import KubesecAnalyzer
from .trufflehog_analyzer import TrufflehogAnalyzer
from .report_generator import ReportGenerator

__all__ = [
    'BaseAnalyzer',
    'SecurityFindings',
    'ZapAnalyzer',
    'TrivyAnalyzer',
    'KubesecAnalyzer',
    'TrufflehogAnalyzer',
    'ReportGenerator',
]
