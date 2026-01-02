#!/bin/bash
# ============================================================================
# AI-Native MVP - Shell Utility Functions
# ============================================================================
# Shared shell utilities for all DevOps scripts
# Source this file: source "$(dirname "$0")/../common/shell-utils.sh"
# ============================================================================

# Get the directory of this script
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source logging if not already loaded
if ! type log_info &>/dev/null; then
    source "$COMMON_DIR/logging.sh"
fi

# ============================================================================
# Portable sed (macOS vs Linux)
# ============================================================================

# Portable in-place sed that works on both macOS (BSD) and Linux (GNU)
portable_sed_inplace() {
    local pattern="$1"
    local file="$2"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$pattern" "$file"
    else
        sed -i "$pattern" "$file"
    fi
}

# Portable sed with backup file creation
portable_sed_with_backup() {
    local pattern="$1"
    local file="$2"
    local backup_ext="${3:-.bak}"

    cp "$file" "${file}${backup_ext}"
    if sed "$pattern" "${file}${backup_ext}" > "${file}.tmp" 2>/dev/null; then
        mv "${file}.tmp" "$file"
        return 0
    else
        mv "${file}${backup_ext}" "$file"
        rm -f "${file}.tmp"
        return 1
    fi
}

# ============================================================================
# JSON Processing (jq optional)
# ============================================================================

# Check if jq is available
has_jq() {
    command -v jq &>/dev/null
}

# Format JSON (uses jq if available, otherwise cat)
format_json() {
    if has_jq; then
        jq '.' 2>/dev/null || cat
    else
        cat
    fi
}

# Extract JSON field (uses jq if available)
json_get() {
    local field="$1"
    if has_jq; then
        jq -r "$field" 2>/dev/null
    else
        log_warning "jq not available, cannot extract field: $field"
        cat
    fi
}

# ============================================================================
# Command Checking
# ============================================================================

# Check if command exists
command_exists() {
    command -v "$1" &>/dev/null
}

# Require command or exit
require_command() {
    local cmd="$1"
    local install_hint="${2:-}"

    if ! command_exists "$cmd"; then
        log_error "$cmd is required but not installed"
        if [ -n "$install_hint" ]; then
            echo "  Install: $install_hint"
        fi
        exit 1
    fi
}

# Check command and warn if missing (non-fatal)
check_optional_command() {
    local cmd="$1"
    local purpose="${2:-}"

    if ! command_exists "$cmd"; then
        log_warning "$cmd not installed${purpose:+ ($purpose)}"
        return 1
    fi
    return 0
}

# ============================================================================
# Cleanup and Traps
# ============================================================================

# Array to hold cleanup functions
declare -a CLEANUP_FUNCTIONS=()

# Register a cleanup function
register_cleanup() {
    CLEANUP_FUNCTIONS+=("$1")
}

# Run all cleanup functions
run_cleanup() {
    for func in "${CLEANUP_FUNCTIONS[@]}"; do
        $func 2>/dev/null || true
    done
}

# Setup EXIT trap for cleanup
setup_cleanup_trap() {
    trap run_cleanup EXIT
}

# ============================================================================
# Temporary Files
# ============================================================================

# Create a temporary file and register for cleanup
create_temp_file() {
    local prefix="${1:-tmp}"
    local tmpfile
    tmpfile=$(mktemp "/tmp/${prefix}.XXXXXX")
    register_cleanup "rm -f '$tmpfile'"
    echo "$tmpfile"
}

# Create a temporary directory and register for cleanup
create_temp_dir() {
    local prefix="${1:-tmpdir}"
    local tmpdir
    tmpdir=$(mktemp -d "/tmp/${prefix}.XXXXXX")
    register_cleanup "rm -rf '$tmpdir'"
    echo "$tmpdir"
}

# ============================================================================
# Input Validation
# ============================================================================

# Check if variable is set and non-empty
is_set() {
    [ -n "${!1:-}" ]
}

# Require variable to be set
require_var() {
    local var_name="$1"
    local error_msg="${2:-$var_name is required}"

    if ! is_set "$var_name"; then
        log_error "$error_msg"
        exit 1
    fi
}

# Validate URL format
is_valid_url() {
    local url="$1"
    [[ "$url" =~ ^https?:// ]]
}

# Export functions
export -f portable_sed_inplace portable_sed_with_backup
export -f has_jq format_json json_get
export -f command_exists require_command check_optional_command
export -f register_cleanup run_cleanup setup_cleanup_trap
export -f create_temp_file create_temp_dir
export -f is_set require_var is_valid_url
