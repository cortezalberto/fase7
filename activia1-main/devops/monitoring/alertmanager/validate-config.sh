#!/bin/sh
# ============================================================================
# Alertmanager Configuration Validator
# ============================================================================
# FIX Cortez49: Validate SMTP and notification configuration before startup
#
# This script checks:
# 1. SMTP configuration is properly set (not defaults)
# 2. At least one notification channel is configured
# 3. Required email addresses are not example.com
#
# Usage: Run before alertmanager starts or as Docker entrypoint wrapper
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo "${RED}[ERROR]${NC} $1" >&2; }

echo "============================================"
echo "Alertmanager Configuration Validator"
echo "============================================"
echo ""

WARNINGS=0
ERRORS=0

# ============================================================================
# Check SMTP Configuration
# ============================================================================
log_info "Checking SMTP configuration..."

# Check if SMTP host is set and not default
if [ -z "$SMTP_HOST" ] || [ "$SMTP_HOST" = "smtp.gmail.com" ]; then
    log_warn "SMTP_HOST not configured or using default (smtp.gmail.com)"
    log_warn "  Set SMTP_HOST in .env for email alerts to work"
    WARNINGS=$((WARNINGS + 1))
fi

# Check SMTP credentials if using authenticated SMTP
if [ -n "$SMTP_HOST" ] && [ "$SMTP_HOST" != "smtp.gmail.com" ]; then
    if [ -z "$SMTP_USERNAME" ]; then
        log_warn "SMTP_USERNAME not set - email authentication may fail"
        WARNINGS=$((WARNINGS + 1))
    fi
    if [ -z "$SMTP_PASSWORD" ]; then
        log_warn "SMTP_PASSWORD not set - email authentication may fail"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check SMTP_FROM is not example.com
if [ -z "$SMTP_FROM" ] || echo "$SMTP_FROM" | grep -q "example.com"; then
    log_warn "SMTP_FROM not configured or using example.com"
    log_warn "  Emails will show as from: ${SMTP_FROM:-alertmanager@example.com}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# Check Email Recipients
# ============================================================================
log_info "Checking email recipients..."

if [ -z "$ALERT_EMAIL" ] || echo "$ALERT_EMAIL" | grep -q "example.com"; then
    log_warn "ALERT_EMAIL not configured or using example.com"
    log_warn "  Alerts will be sent to: ${ALERT_EMAIL:-admin@example.com}"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -z "$DBA_EMAIL" ] || echo "$DBA_EMAIL" | grep -q "example.com"; then
    log_warn "DBA_EMAIL not configured or using example.com"
    log_warn "  Database alerts will be sent to: ${DBA_EMAIL:-dba@example.com}"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# Check Slack Configuration (Optional)
# ============================================================================
log_info "Checking Slack configuration..."

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    log_info "SLACK_WEBHOOK_URL not configured (optional)"
    log_info "  Critical alerts will only be sent via email"
else
    # Validate webhook URL format
    if ! echo "$SLACK_WEBHOOK_URL" | grep -q "hooks.slack.com"; then
        log_warn "SLACK_WEBHOOK_URL doesn't appear to be a valid Slack webhook"
        WARNINGS=$((WARNINGS + 1))
    else
        log_info "Slack webhook configured"
    fi
fi

# ============================================================================
# Check at least one notification channel is properly configured
# ============================================================================
log_info "Checking notification channels..."

CHANNELS_OK=0

# Check if SMTP is properly configured (not example.com and has credentials)
if [ -n "$SMTP_HOST" ] && [ "$SMTP_HOST" != "smtp.gmail.com" ] && \
   [ -n "$SMTP_USERNAME" ] && [ -n "$SMTP_PASSWORD" ] && \
   [ -n "$ALERT_EMAIL" ] && ! echo "$ALERT_EMAIL" | grep -q "example.com"; then
    log_info "Email channel: CONFIGURED"
    CHANNELS_OK=1
fi

# Check if Slack is configured
if [ -n "$SLACK_WEBHOOK_URL" ] && echo "$SLACK_WEBHOOK_URL" | grep -q "hooks.slack.com"; then
    log_info "Slack channel: CONFIGURED"
    CHANNELS_OK=1
fi

if [ "$CHANNELS_OK" -eq 0 ]; then
    log_error "No notification channels properly configured!"
    log_error "  Alerts will be generated but may not be delivered."
    log_error ""
    log_error "  Configure at least one of:"
    log_error "    - Email: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, ALERT_EMAIL"
    log_error "    - Slack: SLACK_WEBHOOK_URL"
    ERRORS=$((ERRORS + 1))
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "============================================"
echo "Validation Summary"
echo "============================================"

if [ "$ERRORS" -gt 0 ]; then
    log_error "Errors: $ERRORS"
fi

if [ "$WARNINGS" -gt 0 ]; then
    log_warn "Warnings: $WARNINGS"
fi

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    log_info "All checks passed!"
fi

echo ""

# ============================================================================
# Exit behavior
# ============================================================================
# In strict mode, exit with error if no channels configured
if [ "${ALERTMANAGER_STRICT_MODE:-false}" = "true" ] && [ "$ERRORS" -gt 0 ]; then
    log_error "Strict mode enabled - exiting due to configuration errors"
    exit 1
fi

# Always continue with warnings (alertmanager will start but alerts may not be delivered)
if [ "$ERRORS" -gt 0 ]; then
    log_warn "Alertmanager will start but alerts may not be delivered properly"
fi

# If this script is used as entrypoint wrapper, exec the original command
if [ -n "$1" ]; then
    exec "$@"
fi

exit 0
