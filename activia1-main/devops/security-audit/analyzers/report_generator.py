"""
Report Generator - Generates security audit reports

Cortez44: Extracted from analyze-security.py (494 lines)
"""

from collections import defaultdict
from typing import Dict, List, Any

from .base import SecurityFindings, SecurityFinding, SEVERITY_EMOJI, PRIORITY_EMOJI


class ReportGenerator:
    """Generates formatted security audit reports."""

    def __init__(self, findings: SecurityFindings):
        self.findings = findings

    def print_summary(self) -> None:
        """Print executive summary."""
        print()
        print("=" * 70)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 70)
        print()

        total = self.findings.total_count()
        print(f"Total Findings: {total}")
        print()

        # Count by severity
        findings_dict = self.findings.to_dict()
        for severity, items in findings_dict.items():
            if items:
                emoji = SEVERITY_EMOJI.get(severity, '⚪')
                print(f"{emoji} {severity.upper()}: {len(items)}")

        print()

        # Count by tool
        tool_counts = self._count_by_tool()
        print("Findings by Tool:")
        for tool, count in sorted(tool_counts.items()):
            print(f"  • {tool}: {count}")

        print()

    def _count_by_tool(self) -> Dict[str, int]:
        """Count findings by tool."""
        tool_counts: Dict[str, int] = defaultdict(int)
        findings_dict = self.findings.to_dict()
        for findings_list in findings_dict.values():
            for finding in findings_list:
                tool_counts[finding.tool] += 1
        return dict(tool_counts)

    def print_critical_findings(self) -> None:
        """Print critical and high severity findings."""
        print("=" * 70)
        print("CRITICAL & HIGH SEVERITY FINDINGS")
        print("=" * 70)
        print()

        critical_and_high = self.findings.critical + self.findings.high

        if not critical_and_high:
            print("✅ No critical or high severity findings!")
            print()
            return

        for i, finding in enumerate(critical_and_high, 1):
            severity_emoji = '🔴' if finding.risk == 'critical' else '🟠'

            print(f"{severity_emoji} Finding #{i}: {finding.name}")
            print(f"   Tool: {finding.tool}")
            print(f"   Severity: {finding.risk.upper()}")

            if finding.description:
                desc = finding.description[:200]
                if len(finding.description) > 200:
                    desc += "..."
                print(f"   Description: {desc}")

            if finding.solution:
                sol = finding.solution[:150]
                if len(finding.solution) > 150:
                    sol += "..."
                print(f"   Solution: {sol}")

            if finding.fixed_version:
                print(f"   Fixed in: {finding.fixed_version}")

            if finding.file:
                print(f"   File: {finding.file}")

            print()

    def generate_owasp_top10_mapping(self) -> None:
        """Map findings to OWASP Top 10 2021."""
        print("=" * 70)
        print("OWASP TOP 10 2021 MAPPING")
        print("=" * 70)
        print()

        owasp_mapping = self._create_owasp_mapping()

        for category, mapped_findings in owasp_mapping.items():
            if mapped_findings:
                print(f"✗ {category}: {len(mapped_findings)} finding(s)")
            else:
                print(f"✓ {category}: No issues")

        print()

    def _create_owasp_mapping(self) -> Dict[str, List[SecurityFinding]]:
        """Create OWASP Top 10 mapping from findings."""
        owasp_mapping: Dict[str, List[SecurityFinding]] = {
            'A01:2021 – Broken Access Control': [],
            'A02:2021 – Cryptographic Failures': [],
            'A03:2021 – Injection': [],
            'A04:2021 – Insecure Design': [],
            'A05:2021 – Security Misconfiguration': [],
            'A06:2021 – Vulnerable and Outdated Components': [],
            'A07:2021 – Identification and Authentication Failures': [],
            'A08:2021 – Software and Data Integrity Failures': [],
            'A09:2021 – Security Logging and Monitoring Failures': [],
            'A10:2021 – Server-Side Request Forgery (SSRF)': []
        }

        findings_dict = self.findings.to_dict()
        for findings_list in findings_dict.values():
            for finding in findings_list:
                self._map_finding_to_owasp(finding, owasp_mapping)

        return owasp_mapping

    def _map_finding_to_owasp(
        self,
        finding: SecurityFinding,
        mapping: Dict[str, List[SecurityFinding]]
    ) -> None:
        """Map a single finding to OWASP categories."""
        name = finding.name.lower()

        if 'injection' in name or 'sql' in name or 'xss' in name:
            mapping['A03:2021 – Injection'].append(finding)
        elif 'access control' in name or 'authorization' in name:
            mapping['A01:2021 – Broken Access Control'].append(finding)
        elif 'crypto' in name or 'encryption' in name or 'secret' in name:
            mapping['A02:2021 – Cryptographic Failures'].append(finding)
        elif 'authentication' in name or 'session' in name:
            mapping['A07:2021 – Identification and Authentication Failures'].append(finding)
        elif 'ssrf' in name:
            mapping['A10:2021 – Server-Side Request Forgery (SSRF)'].append(finding)
        elif finding.tool == 'Trivy':
            mapping['A06:2021 – Vulnerable and Outdated Components'].append(finding)
        elif finding.tool == 'Kubesec':
            mapping['A05:2021 – Security Misconfiguration'].append(finding)

    def generate_recommendations(self) -> None:
        """Generate prioritized remediation recommendations."""
        print("=" * 70)
        print("REMEDIATION RECOMMENDATIONS")
        print("=" * 70)
        print()

        recommendations = self._build_recommendations()

        if recommendations:
            for rec in recommendations:
                emoji = PRIORITY_EMOJI.get(rec['priority'], '⚪')
                print(f"{emoji} {rec['category']} ({rec['count']} finding(s))")
                print(f"   Priority: {rec['priority']}")
                print(f"   Actions:")
                for action in rec['actions']:
                    print(f"      • {action}")
                print()
        else:
            print("✅ No major security issues found!")
            print()

    def _build_recommendations(self) -> List[Dict[str, Any]]:
        """Build list of recommendations based on findings."""
        recommendations = []

        # Critical findings
        if self.findings.critical:
            recommendations.append({
                'priority': 'IMMEDIATE',
                'category': 'Critical Vulnerabilities',
                'count': len(self.findings.critical),
                'actions': [
                    'Review and remove all secrets from Git history',
                    'Rotate compromised credentials immediately',
                    'Implement secrets management (HashiCorp Vault, AWS Secrets Manager)',
                    'Enable Git hooks to prevent future commits with secrets'
                ]
            })

        # High severity
        if self.findings.high:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'High Severity Vulnerabilities',
                'count': len(self.findings.high),
                'actions': [
                    'Update vulnerable dependencies to patched versions',
                    'Implement input validation and sanitization',
                    'Review and fix security misconfigurations',
                    'Enable security headers (CSP, HSTS, X-Frame-Options)'
                ]
            })

        # Kubernetes security
        kubesec_findings = self.findings.get_by_tool('Kubesec')
        if kubesec_findings:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Kubernetes Security',
                'count': len(kubesec_findings),
                'actions': [
                    'Add security contexts to all pods (runAsNonRoot: true)',
                    'Implement network policies for pod isolation',
                    'Enable Pod Security Standards (restricted)',
                    'Use read-only root filesystems where possible',
                    'Drop unnecessary capabilities (CAP_NET_RAW, etc.)'
                ]
            })

        # Container security
        trivy_findings = self.findings.get_by_tool('Trivy')
        if trivy_findings:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Container Security',
                'count': len(trivy_findings),
                'actions': [
                    'Update base images to latest secure versions',
                    'Use minimal base images (Alpine, Distroless)',
                    'Scan images in CI/CD pipeline',
                    'Implement image signing and verification',
                    'Remove unnecessary packages from containers'
                ]
            })

        return recommendations

    def generate_compliance_report(self) -> None:
        """Generate compliance status report."""
        print("=" * 70)
        print("COMPLIANCE STATUS")
        print("=" * 70)
        print()

        compliance_checks = self._run_compliance_checks()

        total_checks = len(compliance_checks)
        passed_checks = sum(1 for passed in compliance_checks.values() if passed)

        print(f"Compliance Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.0f}%)")
        print()

        for check, passed in compliance_checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {check}")

        print()

        if passed_checks == total_checks:
            print("🎉 System is compliant with security best practices!")
        elif passed_checks >= total_checks * 0.8:
            print("⚠️  Minor compliance issues found. Review recommendations.")
        else:
            print("❌ Major compliance issues found. Immediate action required.")

        print()

    def _run_compliance_checks(self) -> Dict[str, bool]:
        """Run compliance checks and return results."""
        trufflehog_findings = self.findings.get_by_tool('TruffleHog')
        kubesec_findings = self.findings.get_by_tool('Kubesec')

        trivy_critical_high = [
            f for f in self.findings.get_by_tool('Trivy')
            if f.risk in ['critical', 'high']
        ]

        return {
            'No critical vulnerabilities': len(self.findings.critical) == 0,
            'No high-severity vulnerabilities': len(self.findings.high) == 0,
            'No secrets in repository': len(trufflehog_findings) == 0,
            'Kubernetes security best practices': len(kubesec_findings) < 5,
            'No outdated dependencies': len(trivy_critical_high) == 0,
        }

    def generate_full_report(self) -> None:
        """Generate all report sections."""
        self.print_summary()
        self.print_critical_findings()
        self.generate_owasp_top10_mapping()
        self.generate_recommendations()
        self.generate_compliance_report()
