# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## DevOps Overview

This directory contains the complete DevOps infrastructure for the AI-Native MVP project including Kubernetes deployments, monitoring, security auditing, load testing, and operational scripts.

**Last Updated:** Cortez94 DevOps Update (January 2026)
- Updated to PostgreSQL 16, Redis 7.4, Nginx 1.27
- Python 3.12, Node 22 LTS
- React 19 + Vite 6.4 support
- Prometheus 2.54, Grafana 11.3
- Added Mistral API support
- Enhanced Docker build caching
- Non-root container security

**Previous:** Cortez40 Optimization Audit (December 2025) - 32 optimizations applied: common library for ~400 lines deduplication, 2:1 resource ratio, parallel deployment support.

## Quick Commands

```bash
# Navigate to devops directory
cd activia1-main/devops

# Kubernetes Deployment (staging)
cd kubernetes/staging
./deploy.sh                              # Interactive deployment
PARALLEL_DEPLOY=true ./deploy.sh         # 50% faster with parallel
NAMESPACE=ai-native-prod ./deploy.sh     # Deploy to production

# Rollback
./rollback.sh --backend                  # Rollback backend (CI/CD)
./rollback.sh --frontend --revision 3    # Rollback to specific revision
./rollback.sh --history                  # Show deployment history

# Verification & Monitoring
./verify.sh                              # Verify all components
./monitor.sh                             # Interactive monitoring dashboard
./init-database.sh                       # Initialize PostgreSQL schema

# Security Audit
cd ../security-audit
./run-security-scan.sh                   # Interactive security scans

# Load Testing
cd ../load-testing
./run-load-test.sh                       # Interactive load tests
```

## Architecture

### Directory Structure

```
devops/
├── common/                    # Shared shell libraries (OPT-001)
│   ├── colors.sh              # Color definitions
│   ├── logging.sh             # log_info, log_success, log_warning, log_error
│   ├── k8s-utils.sh           # wait_for_pod, retry_with_backoff, is_ci_mode
│   └── shell-utils.sh         # portable_sed, has_jq, cleanup traps
├── kubernetes/staging/        # Kubernetes manifests (numbered order)
│   ├── 01-namespace.yaml      # Namespace, ResourceQuota, LimitRange
│   ├── 02-configmap.yaml      # Non-sensitive configuration
│   ├── 03-secrets.yaml.example # Secret template (NEVER commit actual)
│   ├── 04-postgresql.yaml     # PostgreSQL StatefulSet + config
│   ├── 05-redis.yaml          # Redis Deployment (LRU, AOF)
│   ├── 06-backend.yaml        # Backend + HPA + RBAC
│   ├── 07-frontend.yaml       # Frontend (Nginx)
│   ├── 08-ingress.yaml        # Ingress + TLS (Cert-Manager)
│   ├── 09-network-policies.yaml # Pod isolation policies
│   ├── 10-pod-disruption-budgets.yaml
│   └── *.sh                   # Operational scripts
├── monitoring/                # Prometheus + Grafana + Alertmanager
│   ├── prometheus.yml         # Scrape config (API, PostgreSQL, Redis)
│   ├── alerts/prometheus-alerts.yml # Alert rules
│   ├── alertmanager/          # Alert routing (Slack, email)
│   └── grafana/provisioning/  # Datasources and dashboards
├── security-audit/            # OWASP ZAP, Trivy, Kubesec, TruffleHog
├── load-testing/              # Artillery load tests
└── scripts/                   # Python utilities (migrations, secrets)
```

### Kubernetes Deployment Flow

```
01-namespace.yaml → 02-configmap.yaml → secrets (kubectl create) →
04-postgresql.yaml → 05-redis.yaml → 06-backend.yaml → 07-frontend.yaml →
08-ingress.yaml → 09-network-policies.yaml → 10-pod-disruption-budgets.yaml
```

### Resource Configuration (OPT-015 to OPT-018)

All resources use 2:1 limit-to-request ratio for predictable scheduling:

| Component | Requests | Limits |
|-----------|----------|--------|
| Backend | 500m / 1Gi | 1000m / 2Gi |
| Frontend | 100m / 256Mi | 200m / 512Mi |
| PostgreSQL | 500m / 2Gi | 1000m / 4Gi |

## Critical Rules

### Using Common Library

All scripts source from `devops/common/` with fallback for standalone execution:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$SCRIPT_DIR/../../common"

if [ -f "$COMMON_DIR/logging.sh" ]; then
    source "$COMMON_DIR/logging.sh"
    source "$COMMON_DIR/k8s-utils.sh"
else
    # Fallback definitions
    RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
    log_info() { echo -e "${BLUE:-}[INFO]${NC} $1"; }
fi
```

### Configurable Namespace (OPT-019)

All scripts support namespace override via environment variable:

```bash
NAMESPACE="${NAMESPACE:-ai-native-staging}"

# Usage:
NAMESPACE=ai-native-prod ./deploy.sh
```

### CI/CD Mode Detection

Scripts detect CI environment and skip interactive prompts:

```bash
# In scripts (from k8s-utils.sh)
if is_ci_mode; then
    # Non-interactive behavior
fi

# CLI flags for CI/CD
./rollback.sh --backend              # No prompts
./rollback.sh --cleanup --confirm    # Destructive requires --confirm
```

### Portable Shell (BSD/GNU)

Use common library functions for cross-platform compatibility:

```bash
# CORRECT: Use portable_sed_inplace from shell-utils.sh
portable_sed_inplace 's/old/new/' file.txt

# INCORRECT: Direct sed -i (fails on macOS)
sed -i 's/old/new/' file.txt
```

### jq Optional Handling

Scripts gracefully degrade when jq is not installed:

```bash
# From shell-utils.sh
if has_jq; then
    echo "$json" | jq '.field'
else
    log_warning "jq not available"
    echo "$json"
fi
```

### Secrets Management

NEVER commit secrets. Use kubectl create:

```bash
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
POSTGRES_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(16))")

kubectl create secret generic ai-native-secrets \
  --namespace=ai-native-staging \
  --from-literal=JWT_SECRET_KEY="$JWT_SECRET" \
  --from-literal=DATABASE_URL="postgresql://ai_native:$POSTGRES_PASSWORD@ai-native-postgresql:5432/ai_native" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
```

## Monitoring Configuration

### Prometheus Scrape Targets

- `ai-native-api:8000/metrics` - Backend metrics
- `postgres-exporter:9187` - PostgreSQL metrics
- `redis-exporter:9121` - Redis metrics
- `alertmanager:9093` - Alertmanager

### Alert Severity Routing

```yaml
# Critical → email + Slack (immediate)
# Warning → Slack only (batched 5m)
# Info → logged only
```

### Key Prometheus Queries

```promql
# API error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# LLM latency p99
histogram_quantile(0.99, ai_native_llm_call_duration_seconds_bucket)

# PostgreSQL connections
pg_stat_activity_count / pg_settings_max_connections

# Redis hit rate
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)
```

## Security Scanning

### Quick Security Scan (CI/CD)

```bash
./run-security-scan.sh
# Option 2: Quick scan (OWASP ZAP baseline) - 5 min
```

### Full Security Audit

```bash
./run-security-scan.sh
# Option 1: Full scan (ZAP + Trivy + Kubesec + TruffleHog) - 45 min
```

### Tool-Specific Scans

| Option | Tool | Duration | Use Case |
|--------|------|----------|----------|
| 2 | OWASP ZAP baseline | 5 min | CI/CD |
| 3 | Trivy | 2 min | Container CVEs |
| 4 | Kubesec | 1 min | K8s manifests |
| 5 | TruffleHog | 3 min | Secrets in Git |

## Load Testing

### SLA Targets

- Mean response time: < 1000 ms
- p95: < 2000 ms
- p99: < 5000 ms
- Error rate: < 5%

### Test Types

| Option | Duration | RPS | Use Case |
|--------|----------|-----|----------|
| 1 | 1 min | 10 | Smoke test |
| 2 | 5 min | 30 | Normal load |
| 3 | 10 min | 20→100 | Stress test |
| 4 | 15 min | 5→200 | Full test |
| 5 | 2.5 min | 10→200→10 | Spike test |

### Monitor During Load Test

```bash
# Terminal 1: Load test
./run-load-test.sh

# Terminal 2: HPA scaling
watch kubectl get hpa -n ai-native-staging

# Terminal 3: Pod metrics
watch kubectl top pods -n ai-native-staging
```

## Troubleshooting

### Pod Not Starting

```bash
kubectl describe pod <pod-name> -n ai-native-staging
kubectl logs <pod-name> -n ai-native-staging --previous
```

### Database Connection Issues

```bash
kubectl exec -it postgresql-0 -n ai-native-staging -- psql -U ai_native -d ai_native
```

### Certificate Not Ready

```bash
kubectl describe certificate ai-native-staging-tls -n ai-native-staging
kubectl get certificaterequest -n ai-native-staging
```

### HPA Not Scaling

```bash
kubectl describe hpa ai-native-backend-hpa -n ai-native-staging
# Check if metrics-server is installed
kubectl top pods -n ai-native-staging
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NAMESPACE` | ai-native-staging | Target Kubernetes namespace |
| `PARALLEL_DEPLOY` | false | Enable parallel PostgreSQL/Redis deploy |
| `DOMAIN` | example.com | Domain for ingress hosts |
| `LETSENCRYPT_EMAIL` | admin@example.com | Email for certificate notifications |
| `BACKEND_IMAGE` | ghcr.io/.../backend:latest | Backend container image |
| `FRONTEND_IMAGE` | ghcr.io/.../frontend:latest | Frontend container image |

## Related Documentation

- Main project: `../CLAUDE.md`
- Kubernetes staging: `kubernetes/staging/README.md`
- Load testing: `load-testing/README.md`
- Security audit: `security-audit/README.md`
- Optimizations: `OPTIMIZATIONS_APPLIED.md`
