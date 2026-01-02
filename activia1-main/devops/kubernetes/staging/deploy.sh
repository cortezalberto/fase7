#!/bin/bash

# ============================================================================
# AI-Native MVP - Staging Deployment Script
# ============================================================================
# Author: Mag. Alberto Cortez
# Date: 2025-11-24
# Updated: 2025-12-30 - Added secrets validation, NetworkPolicies, PDBs
# Updated: 2025-12-30 - Optimized with common library, parallel deployments
# ============================================================================

set -e  # Exit on error

# ============================================================================
# Source Common Libraries
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$SCRIPT_DIR/../../common"

# Source common libraries (with fallback for standalone execution)
if [ -f "$COMMON_DIR/logging.sh" ]; then
    source "$COMMON_DIR/logging.sh"
    source "$COMMON_DIR/k8s-utils.sh"
    source "$COMMON_DIR/shell-utils.sh"
else
    # Fallback: define minimal functions if common library not available
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
    is_ci_mode() { [ "$CI" = "true" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; }
fi

log_header "AI-Native MVP - Staging Deployment"

# ============================================================================
# Configuration (OPT-019: Configurable namespace)
# ============================================================================
NAMESPACE="${NAMESPACE:-ai-native-staging}"
CI_MODE="${CI:-false}"

# Required environment variables for deployment
BACKEND_IMAGE="${BACKEND_IMAGE:-}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-}"
DOMAIN="${DOMAIN:-example.com}"

# Parallel deployment (OPT-009: Performance optimization)
PARALLEL_DEPLOY="${PARALLEL_DEPLOY:-true}"

# ============================================================================
# Step 1: Check prerequisites
# ============================================================================
echo "Step 1: Checking prerequisites..."

# Use common library function or fallback
if type check_kubectl &>/dev/null; then
    check_kubectl || exit 1
else
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is not installed"; exit 1; }
fi

# Check Kubernetes version (OPT: D1)
if type check_k8s_version &>/dev/null; then
    check_k8s_version "1.25" || log_warning "Some features may not work on older Kubernetes versions"
fi

# Helm is optional
if command -v helm >/dev/null 2>&1; then
    log_success "Prerequisites OK (kubectl + helm)"
else
    log_warning "helm not installed (optional)"
    log_success "Prerequisites OK (kubectl only)"
fi

# Validate required environment variables for production/staging
if is_ci_mode 2>/dev/null || [ "$CI_MODE" = "true" ]; then
    # In CI/CD mode, require explicit image tags
    if [ -z "$BACKEND_IMAGE" ]; then
        log_error "BACKEND_IMAGE environment variable is required in CI/CD mode"
        echo "  Example: export BACKEND_IMAGE=ghcr.io/your-org/ai-native-backend:v1.0.0"
        exit 1
    fi
    if [ -z "$FRONTEND_IMAGE" ]; then
        log_error "FRONTEND_IMAGE environment variable is required in CI/CD mode"
        echo "  Example: export FRONTEND_IMAGE=ghcr.io/your-org/ai-native-frontend:v1.0.0"
        exit 1
    fi
    log_success "Image variables validated"
else
    # In interactive mode, warn about missing images
    [ -z "$BACKEND_IMAGE" ] && log_warning "BACKEND_IMAGE not set - using default from manifest"
    [ -z "$FRONTEND_IMAGE" ] && log_warning "FRONTEND_IMAGE not set - using default from manifest"
fi

# Warn about default domain
[ "$DOMAIN" = "example.com" ] && log_warning "DOMAIN not set - using 'example.com' (set DOMAIN for actual deployment)"

# Verify storage class exists (OPT-003: Use common function or inline)
if type verify_storage_class &>/dev/null; then
    verify_storage_class "standard" || true
else
    if ! kubectl get storageclass standard >/dev/null 2>&1; then
        log_warning "StorageClass 'standard' not found - PVCs may fail to provision"
        kubectl get storageclass --no-headers 2>/dev/null | awk '{print "    - " $1}' || echo "    (none found)"
    fi
fi
echo ""

# ============================================================================
# Step 2: Verify cluster access
# ============================================================================
echo "Step 2: Verifying cluster access..."
kubectl cluster-info >/dev/null 2>&1 || { log_error "Cannot connect to Kubernetes cluster"; exit 1; }
log_success "Cluster accessible"
echo ""

# ============================================================================
# Step 3: Create namespace and base resources
# ============================================================================
echo "Step 3: Creating namespace and base resources..."
kubectl apply -f "$SCRIPT_DIR/01-namespace.yaml"
log_success "Namespace created"
echo ""

# ============================================================================
# Step 4: Create ConfigMap
# ============================================================================
echo "Step 4: Creating ConfigMap..."
kubectl apply -f "$SCRIPT_DIR/02-configmap.yaml"
log_success "ConfigMap created"
echo ""

# ============================================================================
# Step 5: Validate and check secrets
# ============================================================================
echo "Step 5: Checking secrets..."

validate_secret() {
    local secret_name=$1
    local key=$2
    local value

    value=$(kubectl get secret "$secret_name" -n "$NAMESPACE" -o jsonpath="{.data.$key}" 2>/dev/null | base64 -d 2>/dev/null || echo "")

    # Check for placeholder values
    if [[ "$value" == *"CHANGE_ME"* ]] || [[ "$value" == *"CHANGE_THIS"* ]] || [[ "$value" == *"placeholder"* ]]; then
        log_error "Secret key '$key' contains placeholder value!"
        return 1
    fi

    # Check minimum length for security keys
    if [[ "$key" == "JWT_SECRET_KEY" ]] || [[ "$key" == "SECRET_KEY" ]]; then
        if [[ ${#value} -lt 32 ]]; then
            log_error "Secret key '$key' is too short (minimum 32 characters)"
            return 1
        fi
    fi

    return 0
}

# Function to print secret creation instructions (OPT-004: Deduplicated)
print_secret_instructions() {
    echo ""
    echo "  JWT_SECRET=\$(python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo "  SECRET_KEY=\$(python -c \"import secrets; print(secrets.token_urlsafe(32))\")"
    echo "  POSTGRES_PASSWORD=\$(python -c \"import secrets; print(secrets.token_urlsafe(16))\")"
    echo "  REDIS_PASSWORD=\$(python -c \"import secrets; print(secrets.token_urlsafe(16))\")"
    echo ""
    echo "  kubectl create secret generic ai-native-secrets \\"
    echo "    --namespace=$NAMESPACE \\"
    echo "    --from-literal=JWT_SECRET_KEY=\"\$JWT_SECRET\" \\"
    echo "    --from-literal=SECRET_KEY=\"\$SECRET_KEY\" \\"
    echo "    --from-literal=DATABASE_URL=\"postgresql://ai_native:\$POSTGRES_PASSWORD@ai-native-postgresql:5432/ai_native\" \\"
    echo "    --from-literal=POSTGRES_PASSWORD=\"\$POSTGRES_PASSWORD\" \\"
    echo "    --from-literal=REDIS_PASSWORD=\"\$REDIS_PASSWORD\" \\"
    echo "    --from-literal=OPENAI_API_KEY=\"\${OPENAI_API_KEY:-}\" \\"
    echo "    --from-literal=GEMINI_API_KEY=\"\${GEMINI_API_KEY:-}\""
    echo ""
}

if kubectl get secret ai-native-secrets -n "$NAMESPACE" >/dev/null 2>&1; then
    log_info "Secrets exist. Validating..."

    SECRETS_VALID=true

    # Validate required secrets
    for key in JWT_SECRET_KEY DATABASE_URL POSTGRES_PASSWORD REDIS_PASSWORD; do
        if ! validate_secret "ai-native-secrets" "$key"; then
            SECRETS_VALID=false
        fi
    done

    if [ "$SECRETS_VALID" = false ]; then
        log_error "Secrets validation failed!"
        echo ""
        echo "Please recreate secrets with secure values:"
        echo ""
        echo "  kubectl delete secret ai-native-secrets -n $NAMESPACE"
        print_secret_instructions
        exit 1
    fi

    log_success "Secrets validated"
else
    log_error "Secrets not found!"
    echo ""
    echo "Please create secrets:"
    print_secret_instructions
    exit 1
fi
echo ""

# ============================================================================
# Step 6-7: Deploy PostgreSQL and Redis (OPT-009: Parallel deployment)
# ============================================================================
if [ "$PARALLEL_DEPLOY" = "true" ]; then
    echo "Step 6-7: Deploying PostgreSQL and Redis in parallel..."

    # Apply both manifests
    kubectl apply -f "$SCRIPT_DIR/04-postgresql.yaml" &
    PG_PID=$!
    kubectl apply -f "$SCRIPT_DIR/05-redis.yaml" &
    REDIS_PID=$!

    # Wait for kubectl apply to complete
    wait $PG_PID $REDIS_PID

    log_info "Waiting for PostgreSQL and Redis to be ready (parallel)..."

    # Wait for both pods in parallel (OPT-010)
    kubectl wait --for=condition=ready pod -l app=postgresql -n "$NAMESPACE" --timeout=120s &
    PG_WAIT_PID=$!
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=60s &
    REDIS_WAIT_PID=$!

    # Check PostgreSQL
    if ! wait $PG_WAIT_PID; then
        log_error "PostgreSQL pod not ready"
        kubectl describe pod -l app=postgresql -n "$NAMESPACE"
        exit 1
    fi
    log_success "PostgreSQL ready"

    # Check Redis
    if ! wait $REDIS_WAIT_PID; then
        log_error "Redis pod not ready"
        kubectl describe pod -l app=redis -n "$NAMESPACE"
        exit 1
    fi
    log_success "Redis ready"
else
    # Sequential deployment (original behavior)
    echo "Step 6: Deploying PostgreSQL..."
    kubectl apply -f "$SCRIPT_DIR/04-postgresql.yaml"
    log_info "Waiting for PostgreSQL to be ready (timeout: 120s)..."
    kubectl wait --for=condition=ready pod -l app=postgresql -n "$NAMESPACE" --timeout=120s || {
        log_error "PostgreSQL pod not ready"
        kubectl describe pod -l app=postgresql -n "$NAMESPACE"
        exit 1
    }
    log_success "PostgreSQL ready"
    echo ""

    echo "Step 7: Deploying Redis..."
    kubectl apply -f "$SCRIPT_DIR/05-redis.yaml"
    log_info "Waiting for Redis to be ready (timeout: 60s)..."
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=60s || {
        log_error "Redis pod not ready"
        kubectl describe pod -l app=redis -n "$NAMESPACE"
        exit 1
    }
    log_success "Redis ready"
fi
echo ""

# ============================================================================
# Step 8: Deploy Backend
# ============================================================================
echo "Step 8: Deploying Backend..."
kubectl apply -f "$SCRIPT_DIR/06-backend.yaml"
log_info "Waiting for Backend to be ready (timeout: 180s)..."
kubectl wait --for=condition=ready pod -l app=ai-native-backend -n "$NAMESPACE" --timeout=180s || {
    log_error "Backend pods not ready"
    kubectl describe pod -l app=ai-native-backend -n "$NAMESPACE"
    exit 1
}
log_success "Backend ready"
echo ""

# ============================================================================
# Step 9: Deploy Frontend
# ============================================================================
echo "Step 9: Deploying Frontend..."
kubectl apply -f "$SCRIPT_DIR/07-frontend.yaml"
log_info "Waiting for Frontend to be ready (timeout: 120s)..."
kubectl wait --for=condition=ready pod -l app=ai-native-frontend -n "$NAMESPACE" --timeout=120s || {
    log_error "Frontend pods not ready"
    kubectl describe pod -l app=ai-native-frontend -n "$NAMESPACE"
    exit 1
}
log_success "Frontend ready"
echo ""

# ============================================================================
# Step 10: Deploy Ingress
# ============================================================================
echo "Step 10: Deploying Ingress..."
kubectl apply -f "$SCRIPT_DIR/08-ingress.yaml"
log_success "Ingress created"
echo ""

# ============================================================================
# Step 11: Apply Network Policies (Security)
# ============================================================================
echo "Step 11: Applying Network Policies..."
if [ -f "$SCRIPT_DIR/09-network-policies.yaml" ]; then
    kubectl apply -f "$SCRIPT_DIR/09-network-policies.yaml"
    log_success "Network Policies applied"
else
    log_warning "Network Policies file not found (09-network-policies.yaml)"
fi
echo ""

# ============================================================================
# Step 12: Apply Pod Disruption Budgets (High Availability)
# ============================================================================
echo "Step 12: Applying Pod Disruption Budgets..."
if [ -f "$SCRIPT_DIR/10-pod-disruption-budgets.yaml" ]; then
    kubectl apply -f "$SCRIPT_DIR/10-pod-disruption-budgets.yaml"
    log_success "Pod Disruption Budgets applied"
else
    log_warning "PDB file not found (10-pod-disruption-budgets.yaml)"
fi
echo ""

# ============================================================================
# Deployment Summary
# ============================================================================
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
echo "Namespace: $NAMESPACE"
echo ""
echo "Pods:"
kubectl get pods -n "$NAMESPACE" -o wide
echo ""
echo "Services:"
kubectl get svc -n "$NAMESPACE"
echo ""
echo "Ingress:"
kubectl get ingress -n "$NAMESPACE"
echo ""
echo "PersistentVolumeClaims:"
kubectl get pvc -n "$NAMESPACE"
echo ""

echo -e "${GREEN}=========================================="
echo "✅ Staging Deployment Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure DNS to point to Ingress LoadBalancer IP"
echo "2. Wait for SSL/TLS certificate to be issued"
echo "3. Test health endpoint: kubectl port-forward svc/ai-native-backend 8000:8000 -n $NAMESPACE"
echo "4. Then: curl http://localhost:8000/api/v1/health"
echo ""
echo "Monitoring:"
echo "- View logs: kubectl logs -f -l app=ai-native-backend -n $NAMESPACE"
echo "- Check metrics: kubectl top pods -n $NAMESPACE"
echo "- Describe pod: kubectl describe pod <pod-name> -n $NAMESPACE"
echo ""
echo "Security:"
echo "- Network Policies: kubectl get networkpolicy -n $NAMESPACE"
echo "- Pod Disruption Budgets: kubectl get pdb -n $NAMESPACE"
echo ""
