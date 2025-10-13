#!/usr/bin/env bash

#
# Security Audit Script for CI/CD Pipeline
# 
# This script performs automated security audits on Python dependencies
# and can be integrated into GitHub Actions, GitLab CI, or other CI/CD systems.
#
# Exit Codes:
#   0 - No vulnerabilities found or only low-severity issues
#   1 - High or critical vulnerabilities found (fails CI/CD)
#   2 - Script execution error
#
# Usage:
#   ./scripts/security_audit.sh [--strict] [--output-dir DIR]
#
# Options:
#   --strict        Fail on ANY vulnerability (including low severity)
#   --output-dir    Directory to save audit reports (default: ./security-reports)
#   --help          Show this help message
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${PROJECT_ROOT}/security-reports"
STRICT_MODE=false
MAX_SEVERITY_FAIL="high"  # Fail on 'high' or 'critical' by default

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    grep "^#" "$0" | grep -v "#!/usr/bin/env" | sed 's/^# \?//'
    exit 0
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            MAX_SEVERITY_FAIL="low"
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 2
            ;;
    esac
done

# ============================================================================
# Setup
# ============================================================================

log_info "Starting security audit at ${TIMESTAMP}"
log_info "Project root: ${PROJECT_ROOT}"
log_info "Strict mode: ${STRICT_MODE}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    log_warning "pip-audit not found. Installing..."
    pip install pip-audit
fi

# Check if safety is installed (optional additional check)
SAFETY_AVAILABLE=false
if command -v safety &> /dev/null; then
    SAFETY_AVAILABLE=true
    log_info "safety tool detected - will run additional checks"
fi

# ============================================================================
# Run pip-audit
# ============================================================================

log_info "Running pip-audit vulnerability scan..."

AUDIT_OUTPUT="${OUTPUT_DIR}/pip-audit_${TIMESTAMP}.txt"
AUDIT_JSON="${OUTPUT_DIR}/pip-audit_${TIMESTAMP}.json"
AUDIT_EXIT_CODE=0

# Run pip-audit with description
pip-audit --desc > "$AUDIT_OUTPUT" 2>&1 || AUDIT_EXIT_CODE=$?

# Also save JSON format for programmatic parsing
pip-audit --format json > "$AUDIT_JSON" 2>&1 || true

log_info "Audit results saved to: $AUDIT_OUTPUT"
log_info "JSON results saved to: $AUDIT_JSON"

# ============================================================================
# Parse Results
# ============================================================================

# Count vulnerabilities by severity (from text output)
CRITICAL_COUNT=$(grep -i "critical" "$AUDIT_OUTPUT" | wc -l || echo 0)
HIGH_COUNT=$(grep -i "high" "$AUDIT_OUTPUT" | wc -l || echo 0)
MEDIUM_COUNT=$(grep -i "medium" "$AUDIT_OUTPUT" | wc -l || echo 0)
LOW_COUNT=$(grep -i "low" "$AUDIT_OUTPUT" | wc -l || echo 0)

# Extract total vulnerabilities from summary line
TOTAL_VULNS=$(grep "Found.*vulnerabilities" "$AUDIT_OUTPUT" | grep -oE '[0-9]+' | head -1 || echo 0)

log_info "Vulnerability Summary:"
echo "  Critical: ${CRITICAL_COUNT}"
echo "  High:     ${HIGH_COUNT}"
echo "  Medium:   ${MEDIUM_COUNT}"
echo "  Low:      ${LOW_COUNT}"
echo "  Total:    ${TOTAL_VULNS}"

# ============================================================================
# Run Safety Check (if available)
# ============================================================================

if [ "$SAFETY_AVAILABLE" = true ]; then
    log_info "Running safety vulnerability scan..."
    
    SAFETY_OUTPUT="${OUTPUT_DIR}/safety_${TIMESTAMP}.txt"
    SAFETY_JSON="${OUTPUT_DIR}/safety_${TIMESTAMP}.json"
    
    # Run safety check
    safety check --json > "$SAFETY_JSON" 2>&1 || true
    safety check > "$SAFETY_OUTPUT" 2>&1 || true
    
    log_info "Safety results saved to: $SAFETY_OUTPUT"
fi

# ============================================================================
# Generate Summary Report
# ============================================================================

SUMMARY_REPORT="${OUTPUT_DIR}/summary_${TIMESTAMP}.md"

cat > "$SUMMARY_REPORT" <<EOF
# Security Audit Summary

**Date**: $(date '+%Y-%m-%d %H:%M:%S')  
**Project**: RSS Feed Backend  
**Audit Tool**: pip-audit $(pip-audit --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")

---

## Vulnerability Summary

| Severity | Count |
|----------|-------|
| Critical | ${CRITICAL_COUNT} |
| High     | ${HIGH_COUNT} |
| Medium   | ${MEDIUM_COUNT} |
| Low      | ${LOW_COUNT} |
| **Total** | **${TOTAL_VULNS}** |

---

## Audit Status

EOF

# Determine overall status
if [ "$TOTAL_VULNS" -eq 0 ]; then
    echo "✅ **PASS** - No vulnerabilities detected" >> "$SUMMARY_REPORT"
    EXIT_STATUS=0
elif [ "$STRICT_MODE" = true ]; then
    echo "❌ **FAIL** - Vulnerabilities detected (strict mode)" >> "$SUMMARY_REPORT"
    EXIT_STATUS=1
elif [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
    echo "❌ **FAIL** - Critical or high-severity vulnerabilities detected" >> "$SUMMARY_REPORT"
    EXIT_STATUS=1
else
    echo "⚠️  **WARNING** - Only low/medium vulnerabilities detected" >> "$SUMMARY_REPORT"
    EXIT_STATUS=0
fi

# Add detailed findings
cat >> "$SUMMARY_REPORT" <<EOF

---

## Detailed Reports

- Full audit output: \`$(basename "$AUDIT_OUTPUT")\`
- JSON format: \`$(basename "$AUDIT_JSON")\`
EOF

if [ "$SAFETY_AVAILABLE" = true ]; then
    cat >> "$SUMMARY_REPORT" <<EOF
- Safety report: \`$(basename "$SAFETY_OUTPUT")\`
- Safety JSON: \`$(basename "$SAFETY_JSON")\`
EOF
fi

cat >> "$SUMMARY_REPORT" <<EOF

---

## Recommendations

EOF

if [ "$TOTAL_VULNS" -gt 0 ]; then
    cat >> "$SUMMARY_REPORT" <<EOF
1. Review the detailed audit output for specific vulnerabilities
2. Update affected packages to patched versions
3. Run \`pip install -r requirements-prod.txt --upgrade\` to apply updates
4. Re-run security audit to verify fixes: \`./scripts/security_audit.sh\`
5. Check the Security Audit Report for detailed upgrade instructions

### Quick Fix Commands

\`\`\`bash
# Upgrade pip and setuptools first
python -m pip install --upgrade 'pip>=25.3' 'setuptools>=78.1.1'

# Install updated requirements
pip install -r requirements-prod.txt --upgrade

# Verify fixes
pip-audit
\`\`\`
EOF
else
    cat >> "$SUMMARY_REPORT" <<EOF
✅ No action required - all dependencies are secure!

Continue monitoring with regular security audits.
EOF
fi

cat >> "$SUMMARY_REPORT" <<EOF

---

## CI/CD Integration

This audit was run automatically as part of the CI/CD pipeline.

**Exit Code**: ${EXIT_STATUS}
- 0 = Pass (no critical/high vulnerabilities)
- 1 = Fail (critical/high vulnerabilities found)
- 2 = Script error

---

**Generated by**: \`scripts/security_audit.sh\`
EOF

log_info "Summary report saved to: $SUMMARY_REPORT"

# ============================================================================
# Display Results
# ============================================================================

echo ""
echo "========================================================================"
cat "$SUMMARY_REPORT"
echo "========================================================================"
echo ""

# ============================================================================
# Exit with appropriate code
# ============================================================================

if [ "$EXIT_STATUS" -eq 0 ]; then
    log_success "Security audit passed!"
else
    log_error "Security audit failed! Critical or high-severity vulnerabilities detected."
    log_error "Review the detailed reports in: $OUTPUT_DIR"
fi

exit $EXIT_STATUS
