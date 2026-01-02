"""
Kubesec Analyzer - Analyzes Kubernetes security scan reports

Cortez44: Extracted from analyze-security.py (494 lines)
"""

import json
from pathlib import Path

from .base import BaseAnalyzer, SecurityFindings, SecurityFinding


class KubesecAnalyzer(BaseAnalyzer):
    """Analyzes Kubesec JSON reports for Kubernetes security."""

    def get_report_path(self) -> Path:
        """Get the path to the Kubesec report file."""
        return self.reports_dir / "kubesec-report.json"

    def analyze(self) -> SecurityFindings:
        """Analyze Kubesec report and return findings."""
        report_path = self.get_report_path()

        if not report_path.exists():
            self.log_not_found("Kubesec")
            return self.findings

        self.log_analysis_start("Kubesec")

        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        manifest_count = 0
        for manifest in data:
            manifest_count += 1
            score = manifest.get('score', 0)
            object_name = manifest.get('object', 'Unknown')

            # Process critical scoring items
            scoring = manifest.get('scoring', {})
            critical_items = scoring.get('critical', [])

            for critical in critical_items:
                finding = SecurityFinding(
                    tool='Kubesec',
                    name=f"Kubernetes Security Issue in {object_name}",
                    risk='high',
                    description=critical.get('reason', ''),
                    selector=critical.get('selector', ''),
                    score=score
                )
                self.findings.add(finding)

            # Process advisory items
            advisory_items = scoring.get('advise', [])

            for advisory in advisory_items:
                finding = SecurityFinding(
                    tool='Kubesec',
                    name=f"Kubernetes Best Practice for {object_name}",
                    risk='medium',
                    description=advisory.get('reason', ''),
                    selector=advisory.get('selector', ''),
                    score=score
                )
                self.findings.add(finding)

        self.log_findings_count(manifest_count, "manifests analyzed")
        return self.findings
