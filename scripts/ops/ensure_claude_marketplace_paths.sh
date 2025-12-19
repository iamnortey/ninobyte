#!/usr/bin/env bash
#
# ensure_claude_marketplace_paths.sh
#
# Idempotently ensures Claude Code marketplace paths are correctly configured:
# - Creates .claude-plugin/products symlink if missing
# - Validates JSON syntax for marketplace.json and plugin.json
# - Runs full artifact validation
#
# Usage:
#   ./scripts/ops/ensure_claude_marketplace_paths.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed (actionable error messages provided)
#

set -euo pipefail

# Determine repo root (script is in scripts/ops/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MARKETPLACE_DIR="$REPO_ROOT/.claude-plugin"
MARKETPLACE_JSON="$MARKETPLACE_DIR/marketplace.json"
PRODUCTS_SYMLINK="$MARKETPLACE_DIR/products"
PLUGIN_JSON="$REPO_ROOT/products/claude-code-plugins/ninobyte-senior-dev-brain/.claude-plugin/plugin.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail() { echo -e "${RED}❌ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_info() { echo -e "ℹ️  $1"; }

EXIT_CODE=0

echo ""
echo "============================================================"
echo "Claude Code Marketplace Path Setup"
echo "============================================================"
echo "Repo root: $REPO_ROOT"
echo ""

# -------------------------------------------------------------------
# Step 1: Ensure .claude-plugin directory exists
# -------------------------------------------------------------------
if [[ ! -d "$MARKETPLACE_DIR" ]]; then
    log_fail "Marketplace directory missing: $MARKETPLACE_DIR"
    echo "    Create it with: mkdir -p $MARKETPLACE_DIR"
    EXIT_CODE=1
else
    log_ok "Marketplace directory exists: $MARKETPLACE_DIR"
fi

# -------------------------------------------------------------------
# Step 2: Ensure products symlink exists and points correctly
# -------------------------------------------------------------------
echo ""
echo "--- Symlink Check ---"

if [[ -L "$PRODUCTS_SYMLINK" ]]; then
    # Symlink exists, verify target
    SYMLINK_TARGET=$(readlink "$PRODUCTS_SYMLINK")
    if [[ "$SYMLINK_TARGET" == "../products" ]]; then
        log_ok "Symlink valid: $PRODUCTS_SYMLINK -> $SYMLINK_TARGET"
    else
        log_fail "Symlink exists but points to wrong target: $SYMLINK_TARGET (expected ../products)"
        echo "    Fix with: rm $PRODUCTS_SYMLINK && ln -sf ../products $PRODUCTS_SYMLINK"
        EXIT_CODE=1
    fi
elif [[ -e "$PRODUCTS_SYMLINK" ]]; then
    # Path exists but is not a symlink
    log_fail "$PRODUCTS_SYMLINK exists but is not a symlink"
    echo "    Remove it and create symlink: rm -rf $PRODUCTS_SYMLINK && ln -sf ../products $PRODUCTS_SYMLINK"
    EXIT_CODE=1
else
    # Symlink missing, create it
    log_warn "Symlink missing, creating: $PRODUCTS_SYMLINK -> ../products"
    ln -sf ../products "$PRODUCTS_SYMLINK"
    if [[ -L "$PRODUCTS_SYMLINK" ]]; then
        log_ok "Symlink created successfully"
    else
        log_fail "Failed to create symlink"
        EXIT_CODE=1
    fi
fi

# -------------------------------------------------------------------
# Step 3: Validate marketplace.json syntax
# -------------------------------------------------------------------
echo ""
echo "--- JSON Validation ---"

if [[ ! -f "$MARKETPLACE_JSON" ]]; then
    log_fail "marketplace.json not found: $MARKETPLACE_JSON"
    EXIT_CODE=1
else
    if python3 -m json.tool "$MARKETPLACE_JSON" >/dev/null 2>&1; then
        log_ok "marketplace.json is valid JSON"
    else
        log_fail "marketplace.json has invalid JSON syntax"
        echo "    Run: python3 -m json.tool $MARKETPLACE_JSON"
        EXIT_CODE=1
    fi
fi

if [[ ! -f "$PLUGIN_JSON" ]]; then
    log_fail "plugin.json not found: $PLUGIN_JSON"
    EXIT_CODE=1
else
    if python3 -m json.tool "$PLUGIN_JSON" >/dev/null 2>&1; then
        log_ok "plugin.json is valid JSON"
    else
        log_fail "plugin.json has invalid JSON syntax"
        echo "    Run: python3 -m json.tool $PLUGIN_JSON"
        EXIT_CODE=1
    fi
fi

# -------------------------------------------------------------------
# Step 4: Verify source path schema compliance
# -------------------------------------------------------------------
echo ""
echo "--- Schema Compliance Check ---"

if [[ -f "$MARKETPLACE_JSON" ]]; then
    # Extract source field and check prefix
    SOURCE=$(python3 -c "
import json, sys
try:
    data = json.load(open('$MARKETPLACE_JSON'))
    for p in data.get('plugins', []):
        print(p.get('source', ''))
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null | head -1)

    if [[ -z "$SOURCE" ]]; then
        log_fail "Could not extract plugin source from marketplace.json"
        EXIT_CODE=1
    elif [[ "$SOURCE" == ./* ]]; then
        log_ok "Plugin source starts with './' (schema compliant): $SOURCE"
    else
        log_fail "Plugin source does NOT start with './' (schema violation): $SOURCE"
        echo "    Claude Code requires: source must start with './'"
        echo "    Current value: $SOURCE"
        EXIT_CODE=1
    fi
fi

# -------------------------------------------------------------------
# Step 5: Verify resolved path exists
# -------------------------------------------------------------------
echo ""
echo "--- Path Resolution Check ---"

if [[ -f "$MARKETPLACE_JSON" && -n "${SOURCE:-}" && "$SOURCE" == ./* ]]; then
    RESOLVED_PATH="$MARKETPLACE_DIR/${SOURCE#./}"
    if [[ -d "$RESOLVED_PATH" ]]; then
        log_ok "Plugin source resolves to existing directory: $RESOLVED_PATH"
    else
        log_fail "Plugin source does not resolve to existing directory: $RESOLVED_PATH"
        echo "    Check symlink: ls -la $PRODUCTS_SYMLINK"
        EXIT_CODE=1
    fi
fi

# -------------------------------------------------------------------
# Step 6: Run full artifact validation
# -------------------------------------------------------------------
echo ""
echo "--- Full Artifact Validation ---"

VALIDATE_SCRIPT="$REPO_ROOT/scripts/ci/validate_artifacts.py"
if [[ -f "$VALIDATE_SCRIPT" ]]; then
    if python3 "$VALIDATE_SCRIPT"; then
        log_ok "Full artifact validation passed"
    else
        log_fail "Full artifact validation failed"
        EXIT_CODE=1
    fi
else
    log_warn "validate_artifacts.py not found, skipping full validation"
fi

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
echo ""
echo "============================================================"
if [[ $EXIT_CODE -eq 0 ]]; then
    log_ok "All Claude Code marketplace path checks PASSED"
else
    log_fail "Some checks FAILED - see errors above"
fi
echo "============================================================"
echo ""

exit $EXIT_CODE

