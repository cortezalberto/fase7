#!/bin/bash

# ============================================================================
# AI-Native MVP - Rollback Script
# ============================================================================
# Author: Mag. Alberto Cortez
# Date: 2025-11-24
# Updated: 2025-12-30 - Added CLI arguments for CI/CD compatibility
# Updated: 2025-12-30 - Optimized with common library
# ============================================================================
#
# Usage (Interactive):
#   ./rollback.sh
#
# Usage (CI/CD - non-interactive):
#   ./rollback.sh --backend              # Rollback backend to previous
#   ./rollback.sh --frontend             # Rollback frontend to previous
#   ./rollback.sh --backend --revision 3 # Rollback backend to revision 3
#   ./rollback.sh --history              # Show deployment history
#   ./rollback.sh --cleanup              # Delete all resources (requires --confirm)
#   ./rollback.sh --cleanup --confirm    # Actually delete all resources
#
# ============================================================================

set -e

# ============================================================================
# Source Common Libraries
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$SCRIPT_DIR/../../common"

# Source common libraries (with fallback for standalone execution)
if [ -f "$COMMON_DIR/logging.sh" ]; then
    source "$COMMON_DIR/logging.sh"
    source "$COMMON_DIR/k8s-utils.sh"
else
    # Fallback: define minimal functions
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
fi

# Configuration (OPT-019: Configurable namespace)
NAMESPACE="${NAMESPACE:-ai-native-staging}"

# Parse command line arguments
BACKEND=false
FRONTEND=false
CLEANUP=false
HISTORY=false
CONFIRM=false
REVISION=""

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend           Rollback backend deployment"
    echo "  --frontend          Rollback frontend deployment"
    echo "  --revision N        Rollback to specific revision N"
    echo "  --history           Show deployment history"
    echo "  --cleanup           Delete all resources (requires --confirm)"
    echo "  --confirm           Confirm destructive operations"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  NAMESPACE           Target namespace (default: ai-native-staging)"
    echo ""
    echo "Examples:"
    echo "  $0 --backend                    # Rollback backend to previous version"
    echo "  $0 --frontend --revision 2      # Rollback frontend to revision 2"
    echo "  $0 --history                    # Show all deployment history"
    echo "  $0 --cleanup --confirm          # Delete all resources"
    echo "  NAMESPACE=ai-native-prod $0 --backend  # Rollback in production"
    echo ""
}

rollback_deployment() {
    local deployment=$1
    local revision=$2

    # Verify deployment exists before attempting rollback (OPT: Using common function if available)
    if type deployment_exists &>/dev/null; then
        if ! deployment_exists "$deployment" "$NAMESPACE"; then
            log_error "Deployment '$deployment' not found in namespace '$NAMESPACE'"
            return 1
        fi
    else
        if ! kubectl get deployment "$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_error "Deployment '$deployment' not found in namespace '$NAMESPACE'"
            return 1
        fi
    fi

    log_info "Rolling back $deployment..."

    if [ -n "$revision" ]; then
        kubectl rollout undo "deployment/$deployment" -n "$NAMESPACE" --to-revision="$revision"
    else
        kubectl rollout undo "deployment/$deployment" -n "$NAMESPACE"
    fi

    log_info "Waiting for rollback to complete..."
    kubectl rollout status "deployment/$deployment" -n "$NAMESPACE" --timeout=180s

    log_success "$deployment rollback complete"
    echo ""
    echo "Current pods:"
    kubectl get pods -n "$NAMESPACE" -l "app=$deployment" -o wide
}

show_history() {
    echo "=========================================="
    echo "Deployment History"
    echo "=========================================="
    echo ""
    echo "Namespace: $NAMESPACE"
    echo ""
    echo "Backend:"
    if kubectl get deployment ai-native-backend -n "$NAMESPACE" >/dev/null 2>&1; then
        kubectl rollout history deployment/ai-native-backend -n "$NAMESPACE"
    else
        echo "  No backend deployment found"
    fi
    echo ""
    echo "Frontend:"
    if kubectl get deployment ai-native-frontend -n "$NAMESPACE" >/dev/null 2>&1; then
        kubectl rollout history deployment/ai-native-frontend -n "$NAMESPACE"
    else
        echo "  No frontend deployment found"
    fi
    echo ""
    echo "To see details of a specific revision:"
    echo "  kubectl rollout history deployment/ai-native-backend -n $NAMESPACE --revision=N"
}

cleanup_resources() {
    if [ "$CONFIRM" = false ]; then
        log_error "Cleanup requires --confirm flag"
        echo ""
        echo "This will DELETE ALL RESOURCES including:"
        echo "  - All pods (backend, frontend, PostgreSQL, Redis)"
        echo "  - All data in PostgreSQL (PERMANENT DATA LOSS)"
        echo "  - All ConfigMaps and Secrets"
        echo ""
        echo "Run with --confirm to proceed:"
        echo "  $0 --cleanup --confirm"
        exit 1
    fi

    log_warning "Deleting all resources in namespace '$NAMESPACE'..."
    echo ""

    # Delete in reverse order to respect dependencies
    kubectl delete -f "$SCRIPT_DIR/10-pod-disruption-budgets.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/09-network-policies.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/08-ingress.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/07-frontend.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/06-backend.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/05-redis.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/04-postgresql.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete -f "$SCRIPT_DIR/02-configmap.yaml" --ignore-not-found=true 2>/dev/null || true
    kubectl delete secret ai-native-secrets -n "$NAMESPACE" --ignore-not-found=true 2>/dev/null || true

    # Delete PVCs (persistent volume claims)
    log_info "Deleting PersistentVolumeClaims..."
    kubectl delete pvc -n "$NAMESPACE" --all 2>/dev/null || true

    log_success "All resources deleted"
    echo ""
    echo "To redeploy:"
    echo "  cd $SCRIPT_DIR && ./deploy.sh"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            BACKEND=true
            shift
            ;;
        --frontend)
            FRONTEND=true
            shift
            ;;
        --revision)
            REVISION="$2"
            shift 2
            ;;
        --history)
            HISTORY=true
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "AI-Native MVP - Rollback Tool"
echo "=========================================="
echo ""

# Handle non-interactive mode (CI/CD)
if [ "$BACKEND" = true ] || [ "$FRONTEND" = true ] || [ "$CLEANUP" = true ] || [ "$HISTORY" = true ]; then
    # Non-interactive mode
    if [ "$HISTORY" = true ]; then
        show_history
        exit 0
    fi

    if [ "$CLEANUP" = true ]; then
        cleanup_resources
        exit 0
    fi

    if [ "$BACKEND" = true ]; then
        rollback_deployment "ai-native-backend" "$REVISION"
    fi

    if [ "$FRONTEND" = true ]; then
        rollback_deployment "ai-native-frontend" "$REVISION"
    fi

    exit 0
fi

# Interactive mode (original behavior)
echo "Select rollback option:"
echo ""
echo "1) Rollback backend deployment (to previous version)"
echo "2) Rollback frontend deployment (to previous version)"
echo "3) Delete all resources (DANGER: full cleanup)"
echo "4) Rollback to specific backend revision"
echo "5) Rollback to specific frontend revision"
echo "6) Show deployment history"
echo "7) Exit"
echo ""
read -p "Enter option (1-7): " OPTION

case $OPTION in
    1)
        rollback_deployment "ai-native-backend" ""
        ;;

    2)
        rollback_deployment "ai-native-frontend" ""
        ;;

    3)
        echo ""
        echo -e "${RED}WARNING: This will DELETE ALL RESOURCES in namespace '$NAMESPACE'${NC}"
        echo "This includes:"
        echo "  - All pods (backend, frontend, PostgreSQL, Redis)"
        echo "  - All data in PostgreSQL (PERMANENT DATA LOSS)"
        echo "  - All ConfigMaps and Secrets"
        echo "  - Ingress configuration"
        echo ""
        read -p "Are you ABSOLUTELY SURE? Type 'DELETE' to confirm: " CONFIRM_INPUT

        if [ "$CONFIRM_INPUT" = "DELETE" ]; then
            CONFIRM=true
            cleanup_resources
        else
            echo ""
            echo "Deletion cancelled."
        fi
        ;;

    4)
        echo ""
        echo "Backend deployment history:"
        kubectl rollout history deployment/ai-native-backend -n "$NAMESPACE"
        echo ""
        read -p "Enter revision number to rollback to: " REVISION

        if [ -n "$REVISION" ]; then
            rollback_deployment "ai-native-backend" "$REVISION"
        else
            log_error "Invalid revision number."
        fi
        ;;

    5)
        echo ""
        echo "Frontend deployment history:"
        kubectl rollout history deployment/ai-native-frontend -n "$NAMESPACE"
        echo ""
        read -p "Enter revision number to rollback to: " REVISION

        if [ -n "$REVISION" ]; then
            rollback_deployment "ai-native-frontend" "$REVISION"
        else
            log_error "Invalid revision number."
        fi
        ;;

    6)
        show_history
        ;;

    7)
        echo "Exiting..."
        exit 0
        ;;

    *)
        log_error "Invalid option"
        exit 1
        ;;
esac

echo ""
