#!/usr/bin/env bash

#
# Security Upgrades Verification Script
#
# This script automatically verifies that security upgrades have been
# properly applied and the application is functioning correctly.
#
# Usage:
#   ./scripts/verify_security_upgrades.sh [--verbose]
#
# Exit Codes:
#   0 - All verifications passed
#   1 - One or more verifications failed
#   2 - Script execution error
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERBOSE=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    ((TESTS_SKIPPED++))
}

verbose_log() {
    if [ "$VERBOSE" = true ]; then
        echo "    $1"
    fi
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/usr/bin/env" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 2
            ;;
    esac
done

# ============================================================================
# Verification Tests
# ============================================================================

log_info "Starting security upgrades verification..."
echo ""

# Test 1: Check Python version
log_info "Test 1: Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l) -eq 1 ]]; then
    log_success "Python version $PYTHON_VERSION is compatible (>= 3.10)"
else
    log_error "Python version $PYTHON_VERSION is too old (need >= 3.10)"
fi
echo ""

# Test 2: Check critical packages are installed
log_info "Test 2: Verifying critical packages..."

check_package() {
    local package=$1
    local min_version=$2
    
    if pip show "$package" &> /dev/null; then
        local installed_version=$(pip show "$package" | grep "^Version:" | awk '{print $2}')
        verbose_log "$package installed: $installed_version"
        
        # Simple version comparison (works for most cases)
        if [[ "$installed_version" == "$min_version" ]] || \
           [[ "$installed_version" > "$min_version" ]]; then
            log_success "$package $installed_version (>= $min_version)"
        else
            log_error "$package $installed_version (need >= $min_version)"
        fi
    else
        log_error "$package not installed"
    fi
}

check_package "fastapi" "0.115.0"
check_package "uvicorn" "0.32.0"
check_package "httpx" "0.28.0"
check_package "authlib" "1.6.5"
check_package "h11" "0.16.0"
check_package "h2" "4.3.0"
check_package "starlette" "0.47.2"
echo ""

# Test 3: Check for dependency conflicts
log_info "Test 3: Checking for dependency conflicts..."
if pip check &> /dev/null; then
    log_success "No broken dependencies found"
else
    log_error "Dependency conflicts detected"
    verbose_log "$(pip check 2>&1)"
fi
echo ""

# Test 4: Verify documentation files exist
log_info "Test 4: Verifying documentation files..."

check_file() {
    local file=$1
    if [ -f "$PROJECT_ROOT/$file" ]; then
        log_success "$file exists"
    else
        log_error "$file not found"
    fi
}

check_file "SECURITY_AUDIT_REPORT.md"
check_file "VULNERABILITY_ANALYSIS.md"
check_file "SECURITY_WORK_SUMMARY.md"
check_file "SECURITY_REVIEW_CHECKLIST.md"
check_file "DEPLOYMENT_TESTING_PLAN.md"
check_file "ROLLBACK_PROCEDURES.md"
echo ""

# Test 5: Verify requirements files
log_info "Test 5: Verifying requirements files..."
check_file "requirements-prod.txt"
check_file "requirements-dev.txt"
check_file "requirements.txt"
check_file "requirements.txt.backup"
echo ""

# Test 6: Verify scripts
log_info "Test 6: Verifying automation scripts..."
check_file "scripts/security_audit.sh"
check_file "scripts/README.md"

# Check if scripts are executable
if [ -x "$PROJECT_ROOT/scripts/security_audit.sh" ]; then
    log_success "security_audit.sh is executable"
else
    log_error "security_audit.sh is not executable"
fi
echo ""

# Test 7: Verify CI/CD workflow
log_info "Test 7: Verifying CI/CD workflow..."
check_file ".github/workflows/security-audit.yml"

# Validate YAML syntax
if command -v python &> /dev/null; then
    python -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/.github/workflows/security-audit.yml'))" 2>/dev/null && \
        log_success "security-audit.yml YAML syntax valid" || \
        log_error "security-audit.yml YAML syntax invalid"
else
    log_skip "Python not available for YAML validation"
fi
echo ""

# Test 8: Try importing main application
log_info "Test 8: Testing application imports..."
cd "$PROJECT_ROOT"
if python -c "from app import main" 2>/dev/null; then
    log_success "app.main imports successfully"
else
    log_error "Failed to import app.main"
    verbose_log "$(python -c 'from app import main' 2>&1)"
fi
echo ""

# Test 9: Check monitoring packages
log_info "Test 9: Verifying monitoring packages..."
check_package "sentry-sdk" "2.20.0"
check_package "prometheus-fastapi-instrumentator" "7.0.0"
check_package "python-json-logger" "2.0.7"
echo ""

# Test 10: Run pip-audit (if available)
log_info "Test 10: Running security audit..."
if command -v pip-audit &> /dev/null; then
    AUDIT_OUTPUT=$(pip-audit 2>&1 || true)
    VULN_COUNT=$(echo "$AUDIT_OUTPUT" | grep -oE 'Found [0-9]+ known vulnerabilities' | grep -oE '[0-9]+' || echo "0")
    
    if [ "$VULN_COUNT" -lt 30 ]; then
        log_success "Security audit passed ($VULN_COUNT vulnerabilities, down from 89)"
    elif [ "$VULN_COUNT" -lt 50 ]; then
        log_error "Security audit shows $VULN_COUNT vulnerabilities (expected < 30)"
    else
        log_error "Security audit shows $VULN_COUNT vulnerabilities (too many!)"
    fi
else
    log_skip "pip-audit not installed"
fi
echo ""

# ============================================================================
# Results Summary
# ============================================================================

echo "========================================================================"
echo "                    VERIFICATION RESULTS                                "
echo "========================================================================"
echo ""
echo -e "Tests Passed:  ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed:  ${RED}$TESTS_FAILED${NC}"
echo -e "Tests Skipped: ${YELLOW}$TESTS_SKIPPED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All verifications passed!${NC}"
    echo ""
    echo "Security upgrades have been successfully applied."
    echo "The application is ready for deployment testing."
    exit 0
else
    echo -e "${RED}✗ Some verifications failed!${NC}"
    echo ""
    echo "Please review the failures above and fix the issues."
    echo "Re-run this script after making corrections."
    exit 1
fi
