# GitHub Configuration

This directory contains the complete GitHub automation infrastructure for the AI-Native MVP project. The configuration has been designed following industry best practices for continuous integration, delivery, and project governance, incorporating lessons learned from 59+ code audits performed on this codebase.

## Overview

The AI-Native MVP implements a sophisticated CI/CD pipeline that validates not only traditional software quality metrics but also the specialized requirements of an AI-powered educational platform. The system evaluates cognitive tutoring agents, professional role simulators, and N4-level cognitive traceability—all of which require comprehensive automated testing to ensure pedagogical integrity and technical correctness.

The GitHub configuration addresses three fundamental concerns: **quality assurance** through automated testing and linting, **security** through dependency scanning and vulnerability detection, and **operational excellence** through automated deployment and project management workflows.

---

## Directory Structure

```
.github/
├── ISSUE_TEMPLATE/           # Structured issue templates
│   ├── bug_report.yml        # Bug reports with severity and component selection
│   ├── feature_request.yml   # Feature proposals with priority classification
│   ├── documentation.yml     # Documentation improvement requests
│   ├── question.yml          # Technical questions and clarifications
│   └── config.yml            # Issue template configuration
├── workflows/                # GitHub Actions automation
│   ├── ci-modular.yml        # Primary CI/CD pipeline (recommended)
│   ├── ci.yml                # Legacy monolithic pipeline (preserved)
│   ├── security-modular.yml  # Security scanning pipeline
│   ├── security.yml          # Legacy security pipeline (preserved)
│   ├── stale.yml             # Automated issue/PR lifecycle management
│   ├── release.yml           # Automated release generation
│   ├── labeler.yml           # Automatic PR categorization
│   └── reusable-*.yml        # Composable workflow components
├── CODEOWNERS                # Automatic code review assignment
├── SECURITY.md               # Security policy and vulnerability reporting
├── FUNDING.yml               # Sponsorship and funding configuration
├── dependabot.yml            # Automated dependency management
├── labeler.yml               # PR labeling rules definition
├── pull_request_template.md  # Standardized PR template
└── README.md                 # This documentation
```

---

## Continuous Integration and Delivery

### Pipeline Architecture

The CI/CD pipeline follows a modular architecture introduced in Cortez44 and refined through Cortez45. Rather than maintaining a single monolithic workflow file, the pipeline decomposes into reusable workflow components that can be composed, tested, and maintained independently.

The primary pipeline (`ci-modular.yml`) orchestrates fourteen distinct stages, making it one of the most comprehensive CI/CD pipelines for an educational AI platform:

**Stage 1: Linting** validates code style and quality across both Python and TypeScript codebases. The Python backend undergoes Black formatting verification, isort import ordering, and Flake8 static analysis. The React frontend is validated through ESLint with the project's custom rule configuration and TypeScript strict mode compilation.

**Stage 2: Backend Testing** executes the complete pytest suite against a PostgreSQL 15 and Redis 7.2 service container environment. Tests validate 26+ API routers, 14 database model modules, 12 repository implementations, and 6 AI agent configurations. The minimum coverage threshold of 70% ensures that critical cognitive tutoring and risk analysis pathways remain protected by automated verification.

**Stage 3: Frontend Testing** runs the Vitest test suite for React 19 components, validating UI behavior, hook implementations, and service integrations. The training feature components (Cortez55/56) receive particular attention given their integration with the V1 and V2 backend endpoints.

**Stage 4: Security Scanning** employs a defense-in-depth approach using multiple complementary tools. Bandit performs Python-specific vulnerability detection, Trivy scans container images for known CVEs, and TruffleHog searches for accidentally committed secrets. The security-modular workflow eliminates redundant tooling (pip-audit overlapping with Safety, Gitleaks duplicating TruffleHog) identified during the Cortez45 audit.

**Stage 5: Database Migrations** validates that all database migration scripts execute successfully against a fresh PostgreSQL instance. This includes N4 dimensions, Cortez audit fixes, simulator events, and exercise tables migrations. Schema integrity is verified after all migrations complete.

**Stage 6: Exercise Catalog Validation** verifies the Digital Trainer exercise JSON files for schema compliance, required metadata presence (id, title for each exercise), and seeding script syntax. This ensures that the training content is deployable before reaching production.

**Stage 7: LLM Provider Health Check** validates that LLM provider modules are correctly configured and can be instantiated. The mock provider is tested by default in CI, but the workflow supports testing Gemini, Ollama, and other providers when API keys are provided.

**Stage 8: API Contract Testing** generates the current OpenAPI schema and validates it against the OpenAPI specification. The workflow detects breaking changes by comparing against a baseline schema and verifies that critical endpoints (health, auth, sessions, training) remain present.

**Stage 9: Performance Regression Testing** runs k6 load tests against the API to detect performance regressions. The workflow validates P95 response times against configurable baselines and runs algorithm benchmarks to verify O(n log n) trace processing performance.

**Stage 10: E2E Training Flow** executes end-to-end tests for the complete Digital Trainer student workflow: session start, exercise retrieval, code submission (V1), AI correction, hint requests, and session state verification. Both V1 (Cortez56) and V2 (Cortez50) endpoints are tested.

**Stage 11-12: Container Image Building** produces Docker images for both backend and frontend components. Images are scanned with Trivy before being pushed to the GitHub Container Registry, ensuring that vulnerabilities are caught before deployment.

**Stage 13-14: Kubernetes Deployment** handles environment-specific deployments. The `develop` branch deploys to the staging namespace, while `main` triggers production deployment. Both environments use the same Kubernetes manifests with environment-specific ConfigMaps and Secrets.

### Reusable Workflow Components

The pipeline's modular nature stems from twelve reusable workflow files, each handling a specific concern:

**reusable-lint.yml** encapsulates all linting operations. It accepts Python and Node.js version inputs along with configurable paths for backend and frontend directories. This component runs independently of external services, making it suitable for fast feedback on code style.

**reusable-test-backend.yml** manages the complete backend test environment. It provisions PostgreSQL and Redis service containers, configures environment variables for test isolation (including setting `LLM_PROVIDER=mock` to avoid external LLM dependencies), and executes pytest with coverage reporting. The workflow uploads results to Codecov and preserves HTML coverage reports as artifacts.

**reusable-test-frontend.yml** handles frontend testing with Vitest. It supports configurable working directories and optional coverage collection, producing test result artifacts for debugging failed runs.

**reusable-security.yml** coordinates security scanning tools. It accepts a scan path parameter to focus analysis on specific directories and configurable Trivy severity thresholds. The TruffleHog integration can be toggled for repositories with known false-positive patterns.

**reusable-migrations.yml** validates database migrations against a fresh PostgreSQL instance. It runs the complete migration sequence and verifies schema integrity, ensuring database changes are deployable.

**reusable-exercises.yml** validates the Digital Trainer exercise catalog. It checks JSON schema compliance, verifies required fields, validates seeding script syntax, and confirms repository imports work correctly.

**reusable-llm-health.yml** performs health checks on LLM provider configurations. It validates module imports, factory creation, and interface implementation. For providers with API keys, it can perform actual connectivity tests.

**reusable-api-contract.yml** generates and validates OpenAPI schemas. It detects breaking changes by comparing against baseline versions and verifies critical endpoint presence. The generated schema is uploaded as an artifact for review.

**reusable-performance.yml** runs load tests and algorithm benchmarks. It uses k6 for HTTP load testing with configurable virtual users and duration, and runs Python benchmarks to verify algorithm complexity guarantees.

**reusable-e2e-training.yml** executes end-to-end tests for the Digital Trainer workflow. It tests session creation, code submission, AI correction, hint requests, and session state retrieval across both V1 and V2 endpoints.

**reusable-build.yml** manages Docker image construction. It supports multi-platform builds, configurable Dockerfile locations, and optional image scanning. The push behavior can be controlled to prevent image publication during pull request validation.

**reusable-deploy.yml** orchestrates Kubernetes deployments. It requires environment and namespace inputs, accepts the path to Kubernetes manifests, and supports configurable rollout timeouts. The workflow applies manifests using kubectl and monitors rollout status to ensure healthy deployments.

### Pipeline Execution Flow

When a developer pushes to `develop` or creates a pull request, the pipeline executes in the following order:

1. Linting runs immediately, providing sub-minute feedback on code style
2. Backend and frontend tests run in parallel after linting succeeds
3. Security scanning runs in parallel with testing
4. Image building begins only after all tests and scans pass
5. Deployment proceeds automatically for qualifying branches

This parallel execution strategy minimizes total pipeline duration while maintaining the dependency chain that prevents deploying untested or insecure code.

---

## Security Infrastructure

### Vulnerability Management

The security pipeline runs on two triggers: weekly scheduled execution (every Monday at 3 AM UTC) and immediately upon changes to dependency files (`requirements.txt`, `package.json`, `Dockerfile`). This dual-trigger approach balances between continuous monitoring for newly disclosed vulnerabilities and immediate feedback when dependencies change.

The scanning strategy employs three complementary tools:

**Bandit** performs Python-specific security analysis, identifying common vulnerability patterns such as SQL injection risks, hardcoded credentials, and insecure random number generation. The tool is configured with medium confidence thresholds to minimize false positives while catching significant issues.

**Trivy** scans Docker images for known vulnerabilities using the National Vulnerability Database and vendor-specific advisories. The scanner is configured to fail the pipeline only on CRITICAL and HIGH severity findings, allowing teams to address medium and low findings during regular maintenance cycles.

**TruffleHog** searches the repository history for accidentally committed secrets. Unlike pattern-based secret detection, TruffleHog uses entropy analysis and verified secret patterns to identify actual credentials rather than benign high-entropy strings.

### Security Policy

The `SECURITY.md` file documents the project's security posture and provides clear guidance for vulnerability reporting. The policy specifies supported versions, contact methods for responsible disclosure, and expected response timelines. Security researchers are encouraged to report findings through GitHub's private vulnerability reporting feature rather than public issue creation.

---

## Project Automation

### Dependency Management

Dependabot automates dependency updates across four package ecosystems:

**Python dependencies** (pip) receive weekly updates every Monday at 9 AM UTC. Minor and patch updates are grouped into single pull requests to reduce review overhead, while major updates create individual PRs for careful evaluation.

**JavaScript dependencies** (npm) follow the same weekly schedule. React-related packages are grouped together, as are build tools and linting utilities, recognizing that these dependency clusters often need coordinated updates.

**Docker base images** update every Tuesday, offset from language package updates to distribute review workload across the week.

**GitHub Actions** update every Wednesday, ensuring that workflow files benefit from the latest action versions while avoiding conflicts with other update types.

### Issue and Pull Request Lifecycle

The **stale workflow** automatically manages the lifecycle of issues and pull requests. Issues without activity for 60 days receive a "stale" label and a comment explaining the situation. If no further activity occurs within 14 days, the issue is automatically closed. Pull requests follow a more aggressive timeline—stale after 30 days, closed after 7—reflecting the time-sensitive nature of code changes.

Certain labels exempt items from stale processing: `pinned` for intentionally long-lived items, `security` for vulnerability-related issues, `critical` for high-priority work, and `in-progress` for actively developed items.

### Automatic Labeling

The **labeler workflow** categorizes pull requests based on changed files, enabling efficient triage and review assignment. Labels reflect the architectural boundaries of the codebase:

- `backend` applies when changes affect `backend/` or `requirements.txt`
- `frontend` applies for `frontEnd/` modifications
- `ai-agents` applies specifically for changes to `backend/agents/` or `backend/llm/`
- `database` applies for `backend/database/` or migration files
- `devops` applies for `devops/` or `.github/workflows/` changes
- `security` applies for authentication or authorization file changes
- `documentation` applies for markdown files or the `docs/` directory
- `tests` applies for test file modifications

Size labels (`size/XS` through `size/XL`) automatically categorize PRs by the number of changed lines, helping reviewers allocate appropriate time.

### Code Ownership

The `CODEOWNERS` file defines automatic reviewer assignment based on file paths. This ensures that domain experts review changes in their areas of expertise:

- Backend team members review all `backend/` changes
- AI team members (in addition to backend team) review agent-related changes
- Frontend team members review `frontEnd/` changes
- DevOps team members review infrastructure and workflow changes
- Security team members review authentication, authorization, and security policy changes
- Project leads review organization-level files including `CLAUDE.md`

### Release Automation

The **release workflow** triggers on version tags matching the `v*.*.*` pattern. When triggered, it:

1. Generates a changelog from commits since the previous tag
2. Creates a GitHub Release with the changelog as release notes
3. Builds Docker images tagged with the version number
4. Pushes versioned images to the container registry

This automation ensures that releases are reproducible and well-documented without manual intervention.

---

## CI/CD Gap Analysis (Cortez59) - IMPLEMENTED

Based on comprehensive backend analysis identifying 26+ routers, 14 model modules, 12 repositories, 6 AI agents, and 11 database migrations, all identified gaps have been addressed with dedicated reusable workflows.

### Implementation Status

| Gap Identified | Workflow Created | Status |
|----------------|------------------|--------|
| Database Migration Validation | `reusable-migrations.yml` | ✅ IMPLEMENTED |
| Exercise Catalog Validation | `reusable-exercises.yml` | ✅ IMPLEMENTED |
| LLM Provider Health Check | `reusable-llm-health.yml` | ✅ IMPLEMENTED |
| API Contract Testing | `reusable-api-contract.yml` | ✅ IMPLEMENTED |
| Performance Regression Testing | `reusable-performance.yml` | ✅ IMPLEMENTED |
| E2E Training Flow Validation | `reusable-e2e-training.yml` | ✅ IMPLEMENTED |

### Current Coverage (14 Stages)

The pipeline now validates:
- Code style and linting (Python + TypeScript)
- Unit and integration tests with database services
- Security scanning (Bandit, Trivy, TruffleHog)
- Database migrations against fresh PostgreSQL
- Exercise catalog JSON schema and metadata
- LLM provider module configuration
- OpenAPI schema validity and breaking changes
- API performance under load (k6)
- Algorithm complexity benchmarks
- E2E Digital Trainer workflows (V1 + V2)
- Docker image building with vulnerability scanning
- Kubernetes deployment with rollout monitoring

### Workflow Details

**reusable-migrations.yml** validates database migrations by:
- Running all migration scripts against fresh PostgreSQL
- Verifying N4 dimensions, Cortez audit fixes, simulator events, and exercises tables
- Checking schema integrity after all migrations complete

**reusable-exercises.yml** validates the exercise catalog by:
- Parsing all JSON files in the exercises directory
- Verifying required fields (id, title) for each exercise
- Validating seeding script syntax (seed_exercises.py, seed_secuenciales.py)
- Confirming ExerciseRepository and ExerciseDB imports work

**reusable-llm-health.yml** validates LLM providers by:
- Importing LLMProviderFactory and provider modules
- Creating provider instances through the factory
- Verifying interface implementation (generate method)
- Optional connectivity tests when API keys are provided

**reusable-api-contract.yml** validates API contracts by:
- Generating OpenAPI schema from FastAPI app
- Validating schema against OpenAPI specification
- Comparing against baseline for breaking changes
- Verifying critical endpoints presence (health, auth, sessions, training)

**reusable-performance.yml** validates performance by:
- Running k6 load tests with configurable concurrent users
- Measuring P95 response times against baseline
- Running bisect-based algorithm benchmarks
- Generating performance summary reports

**reusable-e2e-training.yml** validates training flows by:
- Creating test user and obtaining authentication token
- Testing GET /training/lenguajes endpoint
- Testing POST /training/iniciar session creation
- Testing POST /training/submit-ejercicio code submission
- Testing POST /training/corregir-ia AI correction
- Testing POST /training/pista hint request
- Testing GET /training/sesion/{id}/estado session state
- Optional V2 endpoint tests when feature flags enabled

---

## Issue Templates

The project provides four structured issue templates that guide contributors toward providing necessary information:

### Bug Report

The bug report template captures severity classification (Critical/High/Medium/Low), affected component selection from a predefined list (Backend API, Frontend UI, AI Agents, Database, Training System, Simulators, Authentication, DevOps), environment details, and structured reproduction steps. This information accelerates triage and resolution.

### Feature Request

Feature requests document the problem statement motivating the feature, proposed solutions, affected components, and which user types would benefit (Students, Teachers, Administrators, Developers). This template helps prioritize work based on user impact.

### Documentation

Documentation requests specify the type of issue (missing, outdated, incorrect, or unclear documentation), the exact location of the problem, suggested changes, and target audience. This enables documentation contributions from non-developers.

### Question

The question template captures the question category, relevant context, environment information, and what the asker has already attempted. This reduces back-and-forth by frontloading necessary information.

---

## Configuration Reference

### Required Repository Secrets

| Secret | Purpose | Required For |
|--------|---------|--------------|
| `KUBE_CONFIG_STAGING` | Base64-encoded kubeconfig for staging cluster | Staging deployment |
| `KUBE_CONFIG_PRODUCTION` | Base64-encoded kubeconfig for production cluster | Production deployment |
| `CODECOV_TOKEN` | Codecov upload authentication | Coverage reporting (optional) |

The `GITHUB_TOKEN` is automatically provided by GitHub Actions and requires no configuration.

### Environment Variables

The test workflows configure these environment variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Test database access |
| `REDIS_URL` | Redis connection string | Test cache access |
| `LLM_PROVIDER` | `mock` | Avoid external LLM dependencies |
| `ENVIRONMENT` | `testing` | Activate test configurations |
| `JWT_SECRET_KEY` | Test value | Authentication in tests |

---

## Migration Guide

### Transitioning to Modular Workflows

Organizations currently using the legacy `ci.yml` can migrate to the modular approach:

1. Verify all reusable workflows exist in `.github/workflows/`
2. Rename `ci.yml` to `ci-legacy.yml` for preservation
3. Rename `ci-modular.yml` to `ci.yml` to activate it
4. Monitor initial pipeline runs for unexpected behavior
5. Remove `ci-legacy.yml` after confirming successful operation

The same process applies to the security workflows (`security.yml` → `security-modular.yml`).

### Workflow Version Maintenance

Reusable workflows should be reviewed quarterly for:
- GitHub Actions runner updates (Ubuntu version changes)
- setup-python/setup-node action updates
- Security tool version updates
- Kubernetes deployment pattern evolution

Version pins (e.g., `actions/checkout@v4`) should be updated to incorporate security patches and new features.

---

## Audit History

This configuration has evolved through multiple code audits:

| Audit | Contribution |
|-------|--------------|
| Cortez44 | Extracted reusable workflows from monolithic ci.yml |
| Cortez45 | Added issue templates, PR template, dependabot, CODEOWNERS |
| Cortez45 | Created security-modular.yml eliminating redundant tools |
| Cortez45 | Added stale, release, and labeler automation workflows |
| Cortez59 | Professional documentation rewrite and gap analysis |
| Cortez59+ | Implemented all 6 identified gaps with new workflows |

### Cortez59+ Implementation Summary

The following workflows were added to address all identified CI/CD gaps:

```
.github/workflows/
├── reusable-migrations.yml     # Database migration validation
├── reusable-exercises.yml      # Exercise catalog validation
├── reusable-llm-health.yml     # LLM provider health checks
├── reusable-api-contract.yml   # OpenAPI schema validation
├── reusable-performance.yml    # Performance regression testing
└── reusable-e2e-training.yml   # Digital Trainer E2E tests
```

The `ci-modular.yml` pipeline was expanded from 10 to 14 stages to incorporate these new validations, creating one of the most comprehensive CI/CD pipelines for an AI-powered educational platform.

---

*Documentation: Cortez59+*
*Last Updated: January 2026*
