#!/bin/bash

# ============================================================================
# Setup Nginx Ingress Controller and Cert-Manager
# ============================================================================
# Author: Mag. Alberto Cortez
# Date: 2025-11-24
# Updated: 2025-12-30 - Optimized with common library (OPT-001)
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
    # Fallback: define minimal colors
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
fi

# Configuration - set via environment variables or use defaults
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-admin@example.com}"
DOMAIN="${DOMAIN:-example.com}"

echo "=========================================="
echo "Ingress Controller Setup"
echo "=========================================="
echo ""

# Validate required configuration
if [ "$LETSENCRYPT_EMAIL" = "admin@example.com" ]; then
    echo -e "${YELLOW}⚠ WARNING: Using default email for Let's Encrypt${NC}"
    echo "  Set LETSENCRYPT_EMAIL environment variable for certificate notifications"
    echo ""
fi

if [ "$DOMAIN" = "example.com" ]; then
    echo -e "${YELLOW}⚠ WARNING: Using default domain${NC}"
    echo "  Set DOMAIN environment variable for your actual domain"
    echo ""
fi

# Check prerequisites
command -v helm >/dev/null 2>&1 || { echo -e "${RED}ERROR: helm is not installed${NC}"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}ERROR: kubectl is not installed${NC}"; exit 1; }

# Add Helm repos
echo "Step 1: Adding Helm repositories..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo update
echo -e "${GREEN}✓ Helm repos added${NC}"
echo ""

# Install Nginx Ingress Controller
echo "Step 2: Installing Nginx Ingress Controller..."
if helm list -n ingress-nginx | grep -q ingress-nginx; then
    echo -e "${YELLOW}⚠ Nginx Ingress already installed${NC}"
else
    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.replicaCount=2 \
        --set controller.service.type=LoadBalancer \
        --set controller.metrics.enabled=true \
        --set controller.podAnnotations."prometheus\.io/scrape"=true \
        --set controller.podAnnotations."prometheus\.io/port"=10254

    echo -e "${YELLOW}⏳ Waiting for Nginx Ingress to be ready...${NC}"
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s

    echo -e "${GREEN}✓ Nginx Ingress installed${NC}"
fi
echo ""

# Get LoadBalancer IP
echo "Step 3: Getting LoadBalancer IP..."
EXTERNAL_IP=""
while [ -z "$EXTERNAL_IP" ]; do
    echo "Waiting for external IP..."
    EXTERNAL_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    [ -z "$EXTERNAL_IP" ] && sleep 5
done
echo -e "${GREEN}✓ LoadBalancer IP: $EXTERNAL_IP${NC}"
echo ""

# Install Cert-Manager
echo "Step 4: Installing Cert-Manager..."
if kubectl get namespace cert-manager >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Cert-Manager namespace already exists${NC}"
else
    helm install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true \
        --set prometheus.enabled=true

    echo -e "${YELLOW}⏳ Waiting for Cert-Manager to be ready...${NC}"
    kubectl wait --namespace cert-manager \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/instance=cert-manager \
        --timeout=120s

    echo -e "${GREEN}✓ Cert-Manager installed${NC}"
fi
echo ""

# Create ClusterIssuer
echo "Step 5: Creating ClusterIssuers..."

# Staging ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: ${LETSENCRYPT_EMAIL}
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Production ClusterIssuer (for future use)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${LETSENCRYPT_EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

echo -e "${GREEN}✓ ClusterIssuers created${NC}"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "LoadBalancer IP: $EXTERNAL_IP"
echo "Let's Encrypt Email: $LETSENCRYPT_EMAIL"
echo "Domain: $DOMAIN"
echo ""
echo "Next steps:"
echo "1. Configure DNS records:"
echo "   api-staging.ai-native.$DOMAIN → $EXTERNAL_IP"
echo "   app-staging.ai-native.$DOMAIN → $EXTERNAL_IP"
echo ""
echo "2. Wait for DNS propagation (can take 5-60 minutes)"
echo ""
echo "3. Verify DNS:"
echo "   nslookup api-staging.ai-native.$DOMAIN"
echo ""
echo "4. Deploy application (with DOMAIN set):"
echo "   DOMAIN=$DOMAIN ./deploy.sh"
echo ""
echo "Environment variables used:"
echo "  LETSENCRYPT_EMAIL - Email for certificate notifications"
echo "  DOMAIN - Your domain (e.g., myuniversity.edu)"
echo ""