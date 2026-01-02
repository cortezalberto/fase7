#!/bin/bash
# ============================================================================
# AI-Native MVP - Common Color Definitions
# ============================================================================
# Shared color codes for all DevOps scripts
# Source this file: source "$(dirname "$0")/../common/colors.sh"
# ============================================================================

# Terminal colors (ANSI escape codes)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'  # No Color / Reset

# Export for subshells
export RED GREEN YELLOW BLUE CYAN MAGENTA BOLD NC
