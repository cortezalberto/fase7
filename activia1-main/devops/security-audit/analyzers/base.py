"""
Base Analyzer - Abstract base class and common utilities

Cortez44: Extracted from analyze-security.py (494 lines)
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@dataclass
class SecurityFinding:
    """Represents a single security finding."""
    tool: str
    name: str
    risk: str
    description: str = ""
    solution: str = ""
    references: Any = None
    confidence: str = ""
    cweid: str = ""
    wascid: str = ""
    instances: int = 0
    installed_version: str = ""
    fixed_version: str = ""
    cvss_score: Any = None
    selector: str = ""
    score: int = 0
    file: str = ""
    commit: str = ""


@dataclass
class SecurityFindings:
    """Container for all security findings organized by severity."""
    critical: List[SecurityFinding] = field(default_factory=list)
    high: List[SecurityFinding] = field(default_factory=list)
    medium: List[SecurityFinding] = field(default_factory=list)
    low: List[SecurityFinding] = field(default_factory=list)
    informational: List[SecurityFinding] = field(default_factory=list)

    def add(self, finding: SecurityFinding) -> None:
        """Add a finding to the appropriate severity list."""
        severity = finding.risk.lower()
        if severity == 'critical':
            self.critical.append(finding)
        elif severity == 'high':
            self.high.append(finding)
        elif severity == 'medium':
            self.medium.append(finding)
        elif severity == 'low':
            self.low.append(finding)
        else:
            self.informational.append(finding)

    def total_count(self) -> int:
        """Get total number of findings."""
        return (len(self.critical) + len(self.high) + len(self.medium) +
                len(self.low) + len(self.informational))

    def to_dict(self) -> Dict[str, List[SecurityFinding]]:
        """Convert to dictionary format."""
        return {
            'critical': self.critical,
            'high': self.high,
            'medium': self.medium,
            'low': self.low,
            'informational': self.informational
        }

    def get_by_tool(self, tool_name: str) -> List[SecurityFinding]:
        """Get all findings from a specific tool."""
        all_findings = (self.critical + self.high + self.medium +
                       self.low + self.informational)
        return [f for f in all_findings if f.tool == tool_name]


class BaseAnalyzer(ABC):
    """Abstract base class for security analyzers."""

    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.findings = SecurityFindings()

    @abstractmethod
    def analyze(self) -> SecurityFindings:
        """Analyze security reports and return findings."""
        pass

    @abstractmethod
    def get_report_path(self) -> Path:
        """Get the path to the report file."""
        pass

    def report_exists(self) -> bool:
        """Check if the report file exists."""
        return self.get_report_path().exists()

    def log_not_found(self, report_name: str) -> None:
        """Log when a report is not found."""
        print(f"⚠️  {report_name} report not found: {self.get_report_path()}")

    def log_analysis_start(self, tool_name: str) -> None:
        """Log the start of analysis."""
        print(f"Analyzing {tool_name} report...")

    def log_findings_count(self, count: int, item_type: str = "findings") -> None:
        """Log the number of findings."""
        print(f"  Found {count} {item_type}")


# Severity emoji mapping
SEVERITY_EMOJI = {
    'critical': '🔴',
    'high': '🟠',
    'medium': '🟡',
    'low': '🟢',
    'informational': '🔵'
}

# Priority emoji mapping
PRIORITY_EMOJI = {
    'IMMEDIATE': '🔴',
    'HIGH': '🟠',
    'MEDIUM': '🟡',
    'LOW': '🟢'
}
