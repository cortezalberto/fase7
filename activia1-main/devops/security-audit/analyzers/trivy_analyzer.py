"""
Trivy Analyzer - Analyzes Trivy vulnerability scan reports

Cortez44: Extracted from analyze-security.py (494 lines)
"""

import json
from pathlib import Path
from typing import List

from .base import BaseAnalyzer, SecurityFindings, SecurityFinding


class TrivyAnalyzer(BaseAnalyzer):
    """Analyzes Trivy JSON vulnerability reports."""

    def get_report_path(self) -> Path:
        """Get the path to the Trivy report file."""
        return self.reports_dir / "trivy-report.json"

    def get_all_report_paths(self) -> List[Path]:
        """Get all Trivy report files."""
        return list(self.reports_dir.glob("trivy*.json"))

    def analyze(self) -> SecurityFindings:
        """Analyze all Trivy reports and return findings."""
        report_paths = self.get_all_report_paths()

        if not report_paths:
            self.log_not_found("Trivy")
            return self.findings

        for report_path in report_paths:
            self._analyze_single_report(report_path)

        return self.findings

    def _analyze_single_report(self, report_path: Path) -> None:
        """Analyze a single Trivy report."""
        self.log_analysis_start(f"Trivy ({report_path.name})")

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('Results', [])
        vuln_count = 0

        for result in results:
            vulnerabilities = result.get('Vulnerabilities', [])
            vuln_count += len(vulnerabilities)

            for vuln in vulnerabilities:
                severity = vuln.get('Severity', 'UNKNOWN').lower()

                # Get CVSS score from nested structure
                cvss_data = vuln.get('CVSS', {})
                cvss_score = 'N/A'
                if cvss_data:
                    nvd_data = cvss_data.get('nvd', {})
                    if nvd_data:
                        cvss_score = nvd_data.get('V3Score', 'N/A')

                finding = SecurityFinding(
                    tool='Trivy',
                    name=f"{vuln.get('VulnerabilityID', 'Unknown')} in {vuln.get('PkgName', 'Unknown')}",
                    risk=severity,
                    description=vuln.get('Description', 'No description'),
                    installed_version=vuln.get('InstalledVersion', ''),
                    fixed_version=vuln.get('FixedVersion', 'Not available'),
                    references=vuln.get('References', []),
                    cvss_score=cvss_score
                )

                self.findings.add(finding)

        self.log_findings_count(vuln_count, "vulnerabilities")
