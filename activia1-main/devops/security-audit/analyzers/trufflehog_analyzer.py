"""
TruffleHog Analyzer - Analyzes secret detection reports

Cortez44: Extracted from analyze-security.py (494 lines)
"""

import json
from pathlib import Path

from .base import BaseAnalyzer, SecurityFindings, SecurityFinding


class TrufflehogAnalyzer(BaseAnalyzer):
    """Analyzes TruffleHog JSON reports for secrets detection."""

    def get_report_path(self) -> Path:
        """Get the path to the TruffleHog report file."""
        return self.reports_dir / "trufflehog-report.json"

    def analyze(self) -> SecurityFindings:
        """Analyze TruffleHog report and return findings."""
        report_path = self.get_report_path()

        if not report_path.exists():
            self.log_not_found("TruffleHog")
            return self.findings

        self.log_analysis_start("TruffleHog")

        secrets_found = 0

        with open(report_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    secret = json.loads(line)
                    secrets_found += 1

                    # Extract file and commit from nested structure
                    source_metadata = secret.get('SourceMetadata', {})
                    data = source_metadata.get('Data', {})
                    git_data = data.get('Git', {})

                    file_path = git_data.get('file', 'Unknown file')
                    commit = git_data.get('commit', '')

                    finding = SecurityFinding(
                        tool='TruffleHog',
                        name=f"Secret detected: {secret.get('DetectorName', 'Unknown')}",
                        risk='critical',
                        description=f"Potential secret found in {file_path}",
                        file=file_path,
                        commit=commit
                    )
                    self.findings.add(finding)

                except json.JSONDecodeError:
                    continue

        if secrets_found > 0:
            print(f"  ❌ Found {secrets_found} secrets!")
        else:
            print(f"  ✓ No secrets detected")

        return self.findings
