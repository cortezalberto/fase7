# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Use GitHub's private vulnerability reporting:
   - Go to the Security tab → "Report a vulnerability"
   - Or create a private security advisory
3. Alternatively, contact the project maintainers directly via GitHub
4. Include the following information:
   - Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
   - Location of the affected code (file path, line numbers if known)
   - Step-by-step instructions to reproduce the issue
   - Potential impact of the vulnerability
   - Any suggested fixes (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Assessment**: Within 7 days, we will provide an initial assessment
- **Resolution Timeline**: Critical vulnerabilities will be addressed within 30 days
- **Disclosure**: We follow responsible disclosure practices

### Security Measures in Place

This project implements several security measures:

#### Backend Security
- JWT-based authentication with secure token handling
- Input validation using Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM
- Rate limiting on sensitive endpoints
- Custom exceptions for consistent error handling (Cortez33)
- UUID validation before database access (Cortez33)
- LLM concurrency control with semaphores (Cortez34)
- Metrics endpoint protection with API key (Cortez34)

#### Frontend Security
- XSS prevention through React's built-in escaping
- CSRF protection
- Secure localStorage handling with try-catch (Cortez32)
- AbortController for async cleanup (Cortez30)

#### Infrastructure Security
- Docker container security hardening
- Kubernetes NetworkPolicies (Cortez37)
- Redis password protection and dangerous commands disabled
- PostgreSQL role-based access control
- Nginx security headers (CSP, HSTS, X-Frame-Options)
- Trivy vulnerability scanning in CI/CD

#### CI/CD Security
- Automated security scans (Bandit, Safety, TruffleHog)
- CodeQL analysis for code scanning
- Dependency vulnerability alerts via Dependabot
- Secret detection in commits

### Security Contacts

<!-- FIX Cortez49: Updated to use GitHub's built-in security features -->
- **Primary**: Use GitHub's private vulnerability reporting (Security tab)
- **Alternative**: Contact repository maintainers via GitHub profile
- **Note**: Configure SECURITY_EMAIL secret in repository settings for email notifications

### Recognition

We appreciate the security research community. Reporters of valid vulnerabilities may be:
- Acknowledged in our security advisories (with permission)
- Listed in our Hall of Fame (if one is established)

Thank you for helping keep AI-Native MVP secure!
