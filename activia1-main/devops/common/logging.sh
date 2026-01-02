#!/bin/bash
# ============================================================================
# AI-Native MVP - Common Logging Functions
# ============================================================================
# Shared logging utilities for all DevOps scripts
# Source this file: source "$(dirname "$0")/../common/logging.sh"
# Note: This automatically sources colors.sh
# ============================================================================

# Get the directory of this script
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source colors if not already loaded
if [ -z "$NC" ]; then
    source "$COMMON_DIR/colors.sh"
fi

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

log_error() {
    echo -e "${RED}✗ ${NC}$1" >&2
}

log_step() {
    echo -e "${CYAN}→ ${NC}$1"
}

log_header() {
    echo ""
    echo -e "${BOLD}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
    echo ""
}

log_subheader() {
    echo ""
    echo -e "${BOLD}------------------------------------------"
    echo -e "$1"
    echo -e "------------------------------------------${NC}"
}

# Log with timestamp (useful for CI/CD)
log_timestamp() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Export functions
export -f log_info log_success log_warning log_error log_step log_header log_subheader log_timestamp
