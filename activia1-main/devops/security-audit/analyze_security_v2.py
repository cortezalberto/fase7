#!/usr/bin/env python3
"""
AI-Native MVP - Security Audit Analyzer (Modular Version)

Cortez44: Refactored from monolithic analyze-security.py (494 lines)

This version uses modular analyzers for better maintainability:
- analyzers/zap_analyzer.py: OWASP ZAP analysis
- analyzers/trivy_analyzer.py: Trivy vulnerability analysis
- analyzers/kubesec_analyzer.py: Kubernetes security analysis
- analyzers/trufflehog_analyzer.py: Secrets detection analysis
- analyzers/report_generator.py: Report generation

Usage:
    python analyze_security_v2.py [reports_dir]
    python analyze_security_v2.py ./reports
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyzers import (
    SecurityFindings,
    ZapAnalyzer,
    TrivyAnalyzer,
    KubesecAnalyzer,
    TrufflehogAnalyzer,
    ReportGenerator,
)


class SecurityAuditRunner:
    """Orchestrates security analysis using modular analyzers."""

    def __init__(self, reports_dir: str = "./reports"):
        self.reports_dir = Path(reports_dir)
        self.findings = SecurityFindings()

    def run_all_analyzers(self) -> SecurityFindings:
        """Run all security analyzers and aggregate findings."""
        print()
        print("Starting security analysis...")
        print()

        # Run ZAP analyzer
        zap = ZapAnalyzer(self.reports_dir)
        zap_findings = zap.analyze()
        self._merge_findings(zap_findings)

        # Run Trivy analyzer
        trivy = TrivyAnalyzer(self.reports_dir)
        trivy_findings = trivy.analyze()
        self._merge_findings(trivy_findings)

        # Run Kubesec analyzer
        kubesec = KubesecAnalyzer(self.reports_dir)
        kubesec_findings = kubesec.analyze()
        self._merge_findings(kubesec_findings)

        # Run TruffleHog analyzer
        trufflehog = TrufflehogAnalyzer(self.reports_dir)
        trufflehog_findings = trufflehog.analyze()
        self._merge_findings(trufflehog_findings)

        print()
        return self.findings

    def _merge_findings(self, new_findings: SecurityFindings) -> None:
        """Merge findings from an analyzer into the main findings."""
        self.findings.critical.extend(new_findings.critical)
        self.findings.high.extend(new_findings.high)
        self.findings.medium.extend(new_findings.medium)
        self.findings.low.extend(new_findings.low)
        self.findings.informational.extend(new_findings.informational)

    def generate_reports(self) -> None:
        """Generate all security reports."""
        generator = ReportGenerator(self.findings)
        generator.generate_full_report()

    def run_full_analysis(self) -> None:
        """Run complete security analysis pipeline."""
        self.run_all_analyzers()
        self.generate_reports()


def main():
    print()
    print("=" * 70)
    print("AI-NATIVE MVP - SECURITY AUDIT ANALYZER (v2.0 Modular)")
    print("=" * 70)

    reports_dir = sys.argv[1] if len(sys.argv) > 1 else "./reports"

    if not Path(reports_dir).exists():
        print(f"❌ Error: Reports directory not found: {reports_dir}")
        print()
        print("Usage: python analyze_security_v2.py [reports_dir]")
        print()
        print("Example:")
        print("  python analyze_security_v2.py ./reports")
        sys.exit(1)

    runner = SecurityAuditRunner(reports_dir)
    runner.run_full_analysis()

    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
