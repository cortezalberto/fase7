#!/bin/bash

# ============================================================================
# AI-Native MVP - Database Initialization Script (Modular Version)
# ============================================================================
# Cortez44: Refactored from init-database.sh (402 lines)
#
# This version uses modular SQL files from ./sql/ directory:
#   00-extensions.sql     - Database extensions
#   01-sessions.sql       - Sessions table
#   02-activities.sql     - Activities table
#   03-cognitive-traces.sql - Cognitive traces table
#   04-risks.sql          - Risks table
#   05-evaluations.sql    - Evaluations table
#   06-trace-sequences.sql - Trace sequences table
#   07-student-profiles.sql - Student profiles table
#   08-sprint6-tables.sql - Sprint 6 tables
#   09-triggers.sql       - Database triggers
#   10-sample-data.sql    - Sample data (optional)
# ============================================================================

set -e

# ============================================================================
# Source Common Libraries
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$SCRIPT_DIR/../../common"
SQL_DIR="$SCRIPT_DIR/sql"

# Source common libraries (with fallback for standalone execution)
if [ -f "$COMMON_DIR/logging.sh" ]; then
    source "$COMMON_DIR/logging.sh"
    source "$COMMON_DIR/k8s-utils.sh"
    source "$COMMON_DIR/shell-utils.sh"
    setup_cleanup_trap
else
    # Fallback: define minimal functions
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
    log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
    log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
    log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
fi

echo "=========================================="
echo "Database Initialization - Modular Version"
echo "=========================================="
echo ""

# Configuration
NAMESPACE="${NAMESPACE:-ai-native-staging}"
POSTGRES_POD="postgresql-0"
DB_NAME="ai_native"
DB_USER="ai_native"
INCLUDE_SAMPLE_DATA="${INCLUDE_SAMPLE_DATA:-false}"

# ============================================================================
# Step 1: Check prerequisites
# ============================================================================
echo "Step 1: Checking prerequisites..."

command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is not installed"; exit 1; }
log_success "kubectl is installed"

if [ ! -d "$SQL_DIR" ]; then
    log_error "SQL directory not found: $SQL_DIR"
    exit 1
fi
log_success "SQL directory found"
echo ""

# ============================================================================
# Step 2: Verify PostgreSQL pod
# ============================================================================
echo "Step 2: Verifying PostgreSQL pod..."

if ! kubectl get pod $POSTGRES_POD -n $NAMESPACE >/dev/null 2>&1; then
    log_error "PostgreSQL pod not found"
    echo "Make sure you've deployed PostgreSQL first:"
    echo "  kubectl apply -f 04-postgresql.yaml"
    exit 1
fi

echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod/$POSTGRES_POD -n $NAMESPACE --timeout=120s || {
    log_error "PostgreSQL pod not ready"
    kubectl describe pod $POSTGRES_POD -n $NAMESPACE
    exit 1
}
log_success "PostgreSQL is ready"
echo ""

# ============================================================================
# Step 3: Execute SQL modules
# ============================================================================
echo "Step 3: Executing SQL modules..."

# Function to execute SQL file
execute_sql_file() {
    local sql_file=$1
    local filename=$(basename "$sql_file")

    echo -n "  Executing $filename... "

    if kubectl exec -i $POSTGRES_POD -n $NAMESPACE -- psql -U $DB_USER -d $DB_NAME < "$sql_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Execute SQL files in order (excluding sample data by default)
SQL_FILES=(
    "00-extensions.sql"
    "01-sessions.sql"
    "02-activities.sql"
    "03-cognitive-traces.sql"
    "04-risks.sql"
    "05-evaluations.sql"
    "06-trace-sequences.sql"
    "07-student-profiles.sql"
    "08-sprint6-tables.sql"
    "09-triggers.sql"
)

FAILED=false
for sql_file in "${SQL_FILES[@]}"; do
    if [ -f "$SQL_DIR/$sql_file" ]; then
        if ! execute_sql_file "$SQL_DIR/$sql_file"; then
            log_error "Failed to execute $sql_file"
            FAILED=true
        fi
    else
        log_warning "SQL file not found: $sql_file"
    fi
done

if [ "$FAILED" = true ]; then
    log_error "Some SQL files failed to execute"
    exit 1
fi

log_success "All SQL modules executed"
echo ""

# ============================================================================
# Step 4: Verify tables
# ============================================================================
echo "Step 4: Verifying tables..."
TABLE_COUNT=$(kubectl exec -i $POSTGRES_POD -n $NAMESPACE -- psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
log_success "Tables created: $TABLE_COUNT"
echo ""

# ============================================================================
# Step 5: Sample data (optional)
# ============================================================================
if [ "$INCLUDE_SAMPLE_DATA" = "true" ] || [ "$1" = "--with-sample-data" ]; then
    echo "Step 5: Creating sample data..."
    if [ -f "$SQL_DIR/10-sample-data.sql" ]; then
        execute_sql_file "$SQL_DIR/10-sample-data.sql"
        log_success "Sample data created"
    else
        log_warning "Sample data file not found"
    fi
    echo ""
else
    echo "Step 5: Skipping sample data (use --with-sample-data to include)"
    echo ""
fi

# ============================================================================
# Summary
# ============================================================================
echo "=========================================="
echo "Database Initialization Complete!"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Namespace: $NAMESPACE"
echo ""
echo "Tables created:"
echo "  - sessions"
echo "  - activities"
echo "  - cognitive_traces"
echo "  - risks"
echo "  - evaluations"
echo "  - trace_sequences"
echo "  - student_profiles"
echo "  - interview_sessions (Sprint 6)"
echo "  - incident_simulations (Sprint 6)"
echo ""
echo "Next steps:"
echo "  1. Deploy backend: kubectl apply -f 06-backend.yaml"
echo "  2. Verify backend logs: kubectl logs -f -l app=ai-native-backend -n $NAMESPACE"
echo "  3. Test API: curl http://\$INGRESS_IP/api/v1/health"
echo ""
