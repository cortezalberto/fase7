#!/bin/bash
# ============================================================================
# AI-Native MVP - Kubernetes Utility Functions
# ============================================================================
# Shared Kubernetes utilities for all DevOps scripts
# Source this file: source "$(dirname "$0")/../common/k8s-utils.sh"
# Note: This automatically sources logging.sh and colors.sh
# ============================================================================

# Get the directory of this script
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source logging if not already loaded
if ! type log_info &>/dev/null; then
    source "$COMMON_DIR/logging.sh"
fi

# ============================================================================
# Kubernetes Validation Functions
# ============================================================================

# Check if kubectl is installed and configured
check_kubectl() {
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl is not installed"
        echo "  Install: https://kubernetes.io/docs/tasks/tools/"
        return 1
    fi

    if ! kubectl cluster-info &>/dev/null; then
        log_error "kubectl is not configured or cluster is unreachable"
        return 1
    fi

    return 0
}

# Check Kubernetes version (requires minimum version)
check_k8s_version() {
    local min_version="${1:-1.25}"
    local current_version

    current_version=$(kubectl version --client -o json 2>/dev/null | grep -o '"gitVersion": "[^"]*"' | head -1 | cut -d'"' -f4 | sed 's/v//')

    if [ -z "$current_version" ]; then
        log_warning "Could not determine Kubernetes client version"
        return 0
    fi

    # Simple version comparison (major.minor)
    local current_major=$(echo "$current_version" | cut -d'.' -f1)
    local current_minor=$(echo "$current_version" | cut -d'.' -f2)
    local min_major=$(echo "$min_version" | cut -d'.' -f1)
    local min_minor=$(echo "$min_version" | cut -d'.' -f2)

    if [ "$current_major" -lt "$min_major" ] || \
       ([ "$current_major" -eq "$min_major" ] && [ "$current_minor" -lt "$min_minor" ]); then
        log_warning "Kubernetes version $current_version is below recommended $min_version"
        return 1
    fi

    return 0
}

# Verify namespace exists
verify_namespace() {
    local namespace="$1"

    if kubectl get namespace "$namespace" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Create namespace if it doesn't exist
ensure_namespace() {
    local namespace="$1"

    if ! verify_namespace "$namespace"; then
        log_info "Creating namespace: $namespace"
        kubectl create namespace "$namespace"
    fi
}

# Verify storage class exists
verify_storage_class() {
    local storage_class="${1:-standard}"

    if kubectl get storageclass "$storage_class" &>/dev/null; then
        return 0
    else
        log_warning "Storage class '$storage_class' not found"
        log_info "Available storage classes:"
        kubectl get storageclass -o name 2>/dev/null | sed 's/storageclass.storage.k8s.io\//  - /'
        return 1
    fi
}

# Wait for pod to be ready
wait_for_pod() {
    local selector="$1"
    local namespace="$2"
    local timeout="${3:-120}"

    log_info "Waiting for pod with selector '$selector' (timeout: ${timeout}s)..."

    if kubectl wait --for=condition=ready pod -l "$selector" -n "$namespace" --timeout="${timeout}s" 2>/dev/null; then
        log_success "Pod is ready"
        return 0
    else
        log_error "Timeout waiting for pod"
        return 1
    fi
}

# Wait for multiple pods in parallel
wait_for_pods_parallel() {
    local namespace="$1"
    local timeout="${2:-120}"
    shift 2
    local selectors=("$@")
    local pids=()
    local failed=0

    for selector in "${selectors[@]}"; do
        kubectl wait --for=condition=ready pod -l "$selector" -n "$namespace" --timeout="${timeout}s" 2>/dev/null &
        pids+=($!)
    done

    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done

    return $failed
}

# Get pod name by selector (returns first pod)
get_pod_name() {
    local selector="$1"
    local namespace="$2"

    kubectl get pods -l "$selector" -n "$namespace" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

# Check if deployment exists
deployment_exists() {
    local deployment="$1"
    local namespace="$2"

    kubectl get deployment "$deployment" -n "$namespace" &>/dev/null
}

# Check if statefulset exists
statefulset_exists() {
    local statefulset="$1"
    local namespace="$2"

    kubectl get statefulset "$statefulset" -n "$namespace" &>/dev/null
}

# ============================================================================
# CI/CD Detection
# ============================================================================

# Detect if running in CI/CD environment
is_ci_mode() {
    # Check common CI environment variables
    if [ "$CI" = "true" ] || \
       [ -n "$CI_COMMIT_SHA" ] || \
       [ -n "$GITHUB_ACTIONS" ] || \
       [ -n "$GITLAB_CI" ] || \
       [ -n "$JENKINS_URL" ] || \
       [ -n "$CIRCLECI" ] || \
       [ -n "$TRAVIS" ]; then
        return 0
    fi
    return 1
}

# Get value from env or prompt (CI-friendly)
get_value_or_prompt() {
    local var_name="$1"
    local prompt_message="$2"
    local default_value="$3"
    local current_value="${!var_name}"

    if [ -n "$current_value" ]; then
        echo "$current_value"
        return 0
    fi

    if is_ci_mode; then
        if [ -n "$default_value" ]; then
            echo "$default_value"
            return 0
        else
            log_error "$var_name is required in CI mode"
            return 1
        fi
    fi

    read -p "$prompt_message" input_value
    echo "${input_value:-$default_value}"
}

# ============================================================================
# Retry Logic
# ============================================================================

# Retry a command with exponential backoff
retry_with_backoff() {
    local max_attempts="${1:-5}"
    local timeout="${2:-1}"
    shift 2
    local cmd=("$@")
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if "${cmd[@]}"; then
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            log_warning "Attempt $attempt failed. Retrying in ${timeout}s..."
            sleep $timeout
            timeout=$((timeout * 2))
        fi

        attempt=$((attempt + 1))
    done

    log_error "Command failed after $max_attempts attempts"
    return 1
}

# Export functions
export -f check_kubectl check_k8s_version verify_namespace ensure_namespace
export -f verify_storage_class wait_for_pod wait_for_pods_parallel get_pod_name
export -f deployment_exists statefulset_exists is_ci_mode get_value_or_prompt
export -f retry_with_backoff
