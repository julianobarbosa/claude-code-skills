#!/usr/bin/env bash
#
# security-gate.sh - Security gate check for CI/CD pipelines
#
# Usage:
#   ./security-gate.sh -n "project-name" -v "1.0.0"
#   ./security-gate.sh -n "project-name" -v "1.0.0" --max-critical 0 --max-high 5
#
# Environment variables:
#   DTRACK_URL      - Dependency-Track base URL
#   DTRACK_API_KEY  - API key for authentication
#
# Options:
#   -n, --name          Project name (required)
#   -v, --version       Project version (required)
#   --max-critical      Maximum allowed critical vulnerabilities (default: 0)
#   --max-high          Maximum allowed high vulnerabilities (default: 0)
#   --max-medium        Maximum allowed medium vulnerabilities (default: unlimited)
#   --max-low           Maximum allowed low vulnerabilities (default: unlimited)
#   --max-policy-fail   Maximum allowed FAIL policy violations (default: 0)
#   --fail-on-warn      Fail on policy WARN violations
#   -o, --output        Output format: text, json, github (default: text)
#   -h, --help          Show this help message

set -euo pipefail

# Default thresholds
MAX_CRITICAL=0
MAX_HIGH=0
MAX_MEDIUM=999999
MAX_LOW=999999
MAX_POLICY_FAIL=0
FAIL_ON_WARN="false"
OUTPUT_FORMAT="text"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    grep '^#' "$0" | grep -v '#!/' | cut -c3-
    exit 1
}

log_info() {
    [[ "$OUTPUT_FORMAT" == "text" ]] && echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    [[ "$OUTPUT_FORMAT" == "text" ]] && echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    [[ "$OUTPUT_FORMAT" == "text" ]] && echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -v|--version)
            PROJECT_VERSION="$2"
            shift 2
            ;;
        --max-critical)
            MAX_CRITICAL="$2"
            shift 2
            ;;
        --max-high)
            MAX_HIGH="$2"
            shift 2
            ;;
        --max-medium)
            MAX_MEDIUM="$2"
            shift 2
            ;;
        --max-low)
            MAX_LOW="$2"
            shift 2
            ;;
        --max-policy-fail)
            MAX_POLICY_FAIL="$2"
            shift 2
            ;;
        --fail-on-warn)
            FAIL_ON_WARN="true"
            shift
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate environment
if [[ -z "${DTRACK_URL:-}" ]]; then
    log_error "DTRACK_URL environment variable not set"
    exit 1
fi

if [[ -z "${DTRACK_API_KEY:-}" ]]; then
    log_error "DTRACK_API_KEY environment variable not set"
    exit 1
fi

if [[ -z "${PROJECT_NAME:-}" || -z "${PROJECT_VERSION:-}" ]]; then
    log_error "Project name (-n) and version (-v) are required"
    usage
fi

# Get project UUID
log_info "Looking up project: ${PROJECT_NAME}:${PROJECT_VERSION}"
PROJECT=$(curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" \
    "${DTRACK_URL}/api/v1/project/lookup?name=${PROJECT_NAME}&version=${PROJECT_VERSION}")

PROJECT_UUID=$(echo "$PROJECT" | jq -r '.uuid // empty')

if [[ -z "$PROJECT_UUID" ]]; then
    log_error "Project not found: ${PROJECT_NAME}:${PROJECT_VERSION}"
    exit 1
fi

log_info "Project UUID: $PROJECT_UUID"

# Get vulnerability metrics
METRICS=$(curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" \
    "${DTRACK_URL}/api/v1/metrics/project/${PROJECT_UUID}/current")

CRITICAL=$(echo "$METRICS" | jq -r '.critical // 0')
HIGH=$(echo "$METRICS" | jq -r '.high // 0')
MEDIUM=$(echo "$METRICS" | jq -r '.medium // 0')
LOW=$(echo "$METRICS" | jq -r '.low // 0')
UNASSIGNED=$(echo "$METRICS" | jq -r '.unassigned // 0')

# Get policy violations
VIOLATIONS=$(curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" \
    "${DTRACK_URL}/api/v1/violation/project/${PROJECT_UUID}")

POLICY_FAIL=$(echo "$VIOLATIONS" | jq '[.[] | select(.policyViolation.violationState == "FAIL")] | length')
POLICY_WARN=$(echo "$VIOLATIONS" | jq '[.[] | select(.policyViolation.violationState == "WARN")] | length')
POLICY_INFO=$(echo "$VIOLATIONS" | jq '[.[] | select(.policyViolation.violationState == "INFO")] | length')

# Determine result
RESULT="PASSED"
FAILURES=()

if [[ $CRITICAL -gt $MAX_CRITICAL ]]; then
    FAILURES+=("Critical: $CRITICAL > $MAX_CRITICAL")
    RESULT="FAILED"
fi

if [[ $HIGH -gt $MAX_HIGH ]]; then
    FAILURES+=("High: $HIGH > $MAX_HIGH")
    RESULT="FAILED"
fi

if [[ $MEDIUM -gt $MAX_MEDIUM ]]; then
    FAILURES+=("Medium: $MEDIUM > $MAX_MEDIUM")
    RESULT="FAILED"
fi

if [[ $LOW -gt $MAX_LOW ]]; then
    FAILURES+=("Low: $LOW > $MAX_LOW")
    RESULT="FAILED"
fi

if [[ $POLICY_FAIL -gt $MAX_POLICY_FAIL ]]; then
    FAILURES+=("Policy FAIL: $POLICY_FAIL > $MAX_POLICY_FAIL")
    RESULT="FAILED"
fi

if [[ "$FAIL_ON_WARN" == "true" && $POLICY_WARN -gt 0 ]]; then
    FAILURES+=("Policy WARN: $POLICY_WARN (--fail-on-warn enabled)")
    RESULT="FAILED"
fi

# Output results
case "$OUTPUT_FORMAT" in
    json)
        cat <<EOF
{
    "result": "$RESULT",
    "project": {
        "name": "$PROJECT_NAME",
        "version": "$PROJECT_VERSION",
        "uuid": "$PROJECT_UUID"
    },
    "vulnerabilities": {
        "critical": $CRITICAL,
        "high": $HIGH,
        "medium": $MEDIUM,
        "low": $LOW,
        "unassigned": $UNASSIGNED
    },
    "thresholds": {
        "critical": $MAX_CRITICAL,
        "high": $MAX_HIGH,
        "medium": $MAX_MEDIUM,
        "low": $MAX_LOW
    },
    "policyViolations": {
        "fail": $POLICY_FAIL,
        "warn": $POLICY_WARN,
        "info": $POLICY_INFO
    },
    "failures": $(printf '%s\n' "${FAILURES[@]:-}" | jq -R . | jq -s .)
}
EOF
        ;;

    github)
        # GitHub Actions output format
        echo "result=$RESULT" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "critical=$CRITICAL" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "high=$HIGH" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "medium=$MEDIUM" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "low=$LOW" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "policy_fail=$POLICY_FAIL" >> "${GITHUB_OUTPUT:-/dev/stdout}"
        echo "policy_warn=$POLICY_WARN" >> "${GITHUB_OUTPUT:-/dev/stdout}"

        # Summary
        {
            echo "## Security Gate: $RESULT"
            echo ""
            echo "| Severity | Count | Threshold |"
            echo "|----------|-------|-----------|"
            echo "| Critical | $CRITICAL | $MAX_CRITICAL |"
            echo "| High | $HIGH | $MAX_HIGH |"
            echo "| Medium | $MEDIUM | $MAX_MEDIUM |"
            echo "| Low | $LOW | $MAX_LOW |"
            echo ""
            echo "### Policy Violations"
            echo "- FAIL: $POLICY_FAIL"
            echo "- WARN: $POLICY_WARN"
            echo "- INFO: $POLICY_INFO"
        } >> "${GITHUB_STEP_SUMMARY:-/dev/stdout}"
        ;;

    text|*)
        echo ""
        echo "========================================"
        echo "Security Gate: $RESULT"
        echo "========================================"
        echo "Project: ${PROJECT_NAME}:${PROJECT_VERSION}"
        echo ""
        echo "Vulnerabilities:"
        echo "  Critical:   $CRITICAL (max: $MAX_CRITICAL)"
        echo "  High:       $HIGH (max: $MAX_HIGH)"
        echo "  Medium:     $MEDIUM (max: $MAX_MEDIUM)"
        echo "  Low:        $LOW (max: $MAX_LOW)"
        echo "  Unassigned: $UNASSIGNED"
        echo ""
        echo "Policy Violations:"
        echo "  FAIL: $POLICY_FAIL (max: $MAX_POLICY_FAIL)"
        echo "  WARN: $POLICY_WARN"
        echo "  INFO: $POLICY_INFO"
        echo ""

        if [[ ${#FAILURES[@]} -gt 0 ]]; then
            echo "Failures:"
            for failure in "${FAILURES[@]}"; do
                echo "  - $failure"
            done
        fi
        echo "========================================"
        ;;
esac

# Exit with appropriate code
if [[ "$RESULT" == "PASSED" ]]; then
    exit 0
else
    exit 1
fi
