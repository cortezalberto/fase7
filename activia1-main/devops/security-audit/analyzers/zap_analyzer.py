"""
OWASP ZAP Analyzer - Analyzes ZAP security scan reports

Cortez44: Extracted from analyze-security.py (494 lines)
"""

import json
from pathlib import Path
from typing import Optional

from .base import BaseAnalyzer, SecurityFindings, SecurityFinding


class ZapAnalyzer(BaseAnalyzer):
    """Analyzes OWASP ZAP JSON reports."""

    def __init__(self, reports_dir: Path, report_name: Optional[str] = None):
        super().__init__(reports_dir)
        self.report_name = report_name

    def get_report_path(self) -> Path:
        """Get the path to the ZAP report file."""
        if self.report_name:
            return self.reports_dir / self.report_name

        # Try different ZAP report names
        possible_names = [
            "zap-security-report.json",
            "zap-baseline-report.json",
            "zap-full-report.json"
        ]

        for name in possible_names:
            path = self.reports_dir / name
            if path.exists():
                return path

        return self.reports_dir / "zap-security-report.json"

    def analyze(self) -> SecurityFindings:
        """Analyze ZAP report and return findings."""
        report_path = self.get_report_path()

        if not report_path.exists():
            self.log_not_found("ZAP")
            return self.findings

        self.log_analysis_start("OWASP ZAP")

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        site = data.get('site', [{}])
        if isinstance(site, list) and site:
            site = site[0]
        elif not isinstance(site, dict):
            site = {}

        alerts = site.get('alerts', [])

        for alert in alerts:
            risk_desc = alert.get('riskdesc', '')
            risk = risk_desc.split()[0].lower() if risk_desc else 'informational'

            finding = SecurityFinding(
                tool='OWASP ZAP',
                name=alert.get('name', 'Unknown'),
                risk=risk,
                confidence=alert.get('confidence', 'Unknown'),
                description=alert.get('desc', ''),
                solution=alert.get('solution', ''),
                references=alert.get('reference', ''),
                cweid=alert.get('cweid', ''),
                wascid=alert.get('wascid', ''),
                instances=len(alert.get('instances', []))
            )

            self.findings.add(finding)

        self.log_findings_count(len(alerts), "unique alerts")
        return self.findings
