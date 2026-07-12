#!/bin/bash
# OpenTelemetry Collector Configuration Validator
# Validates OTEL configuration files and Helm values

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

ERRORS=0
WARNINGS=0

# Check dependencies
check_deps() {
    echo "Checking dependencies..."

    for cmd in yq helm kubectl; do
        if command -v $cmd &> /dev/null; then
            print_status "$cmd is available"
        else
            print_warning "$cmd not found (some validations may be skipped)"
        fi
    done
    echo ""
}

# Validate YAML syntax
validate_yaml() {
    local file="$1"
    echo "Validating YAML: $file"

    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        ((ERRORS++))
        return 1
    fi

    if command -v yq &> /dev/null; then
        if yq eval '.' "$file" > /dev/null 2>&1; then
            print_status "YAML syntax valid"
        else
            print_error "Invalid YAML syntax"
            ((ERRORS++))
            return 1
        fi
    else
        # Fallback to Python
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            print_status "YAML syntax valid"
        else
            print_error "Invalid YAML syntax"
            ((ERRORS++))
            return 1
        fi
    fi
}

# Validate Helm values
validate_helm_values() {
    local file="$1"
    echo "Validating Helm values: $file"

    if [ ! -f "$file" ]; then
        print_warning "Values file not found: $file"
        return 0
    fi

    # Check for required fields
    if command -v yq &> /dev/null; then
        # Check mode
        mode=$(yq eval '.mode // ""' "$file")
        if [ -n "$mode" ]; then
            if [[ "$mode" == "daemonset" || "$mode" == "deployment" || "$mode" == "statefulset" ]]; then
                print_status "Valid mode: $mode"
            else
                print_error "Invalid mode: $mode (must be daemonset, deployment, or statefulset)"
                ((ERRORS++))
            fi
        fi

        # Check resources
        mem_limit=$(yq eval '.resources.limits.memory // ""' "$file")
        if [ -n "$mem_limit" ]; then
            print_status "Memory limit configured: $mem_limit"
        else
            print_warning "No memory limit configured"
            ((WARNINGS++))
        fi

        # Check memory limiter processor
        mem_limiter=$(yq eval '.config.processors.memory_limiter // ""' "$file")
        if [ -n "$mem_limiter" ] && [ "$mem_limiter" != "null" ]; then
            print_status "memory_limiter processor configured"
        else
            print_warning "memory_limiter processor not configured (recommended)"
            ((WARNINGS++))
        fi

        # Check batch processor
        batch=$(yq eval '.config.processors.batch // ""' "$file")
        if [ -n "$batch" ] && [ "$batch" != "null" ]; then
            print_status "batch processor configured"
        else
            print_warning "batch processor not configured (recommended)"
            ((WARNINGS++))
        fi

        # Check service pipelines
        pipelines=$(yq eval '.config.service.pipelines // ""' "$file")
        if [ -n "$pipelines" ] && [ "$pipelines" != "null" ]; then
            print_status "Service pipelines configured"
        else
            print_error "No service pipelines configured"
            ((ERRORS++))
        fi

        # Check exporters
        exporters=$(yq eval '.config.exporters | keys | .[]' "$file" 2>/dev/null)
        if [ -n "$exporters" ]; then
            print_status "Exporters configured: $(echo $exporters | tr '\n' ' ')"
        else
            print_warning "No exporters configured"
            ((WARNINGS++))
        fi

        # Check receivers
        receivers=$(yq eval '.config.receivers | keys | .[]' "$file" 2>/dev/null)
        if [ -n "$receivers" ]; then
            print_status "Receivers configured: $(echo $receivers | tr '\n' ' ')"
        else
            print_warning "No receivers configured"
            ((WARNINGS++))
        fi
    fi
    echo ""
}

# Validate Helm template rendering
validate_helm_template() {
    local values_file="$1"
    local chart="${2:-opentelemetry-collector}"
    local repo="${3:-https://open-telemetry.github.io/opentelemetry-helm-charts}"

    echo "Validating Helm template rendering..."

    if ! command -v helm &> /dev/null; then
        print_warning "helm not available, skipping template validation"
        return 0
    fi

    if [ ! -f "$values_file" ]; then
        print_warning "Values file not found: $values_file"
        return 0
    fi

    # Add repo if not exists
    helm repo add open-telemetry "$repo" 2>/dev/null || true
    helm repo update open-telemetry 2>/dev/null || true

    # Try to render template
    if helm template otel-test open-telemetry/"$chart" -f "$values_file" > /dev/null 2>&1; then
        print_status "Helm template renders successfully"
    else
        print_error "Helm template rendering failed"
        helm template otel-test open-telemetry/"$chart" -f "$values_file" 2>&1 | head -20
        ((ERRORS++))
    fi
    echo ""
}

# Check Kubernetes connectivity and resources
check_kubernetes() {
    echo "Checking Kubernetes resources..."

    if ! command -v kubectl &> /dev/null; then
        print_warning "kubectl not available, skipping Kubernetes checks"
        return 0
    fi

    # Check namespace
    if kubectl get namespace monitoring &> /dev/null; then
        print_status "monitoring namespace exists"
    else
        print_warning "monitoring namespace not found"
    fi

    # Check OTEL collector
    if kubectl get pods -n monitoring -l app.kubernetes.io/name=otel-collector 2>/dev/null | grep -q Running; then
        print_status "OTEL collector pods running"
    else
        print_warning "No running OTEL collector pods found"
    fi

    # Check ServiceMonitor
    if kubectl get servicemonitor -n monitoring otel-collector &> /dev/null; then
        print_status "ServiceMonitor exists"
    else
        print_warning "ServiceMonitor not found"
    fi
    echo ""
}

# Test OTLP endpoint
test_otlp_endpoint() {
    local endpoint="${1:-http://otel-collector.monitoring:4318}"

    echo "Testing OTLP endpoint: $endpoint"

    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null -w "%{http_code}" "$endpoint/v1/traces" -X POST -H "Content-Type: application/json" -d '{"resourceSpans":[]}' | grep -q "200\|204"; then
            print_status "OTLP endpoint responsive"
        else
            print_warning "OTLP endpoint not responding (may need port-forward)"
        fi
    else
        print_warning "curl not available, skipping endpoint test"
    fi
    echo ""
}

# Main
main() {
    echo "========================================"
    echo "OpenTelemetry Configuration Validator"
    echo "========================================"
    echo ""

    check_deps

    # Validate files passed as arguments
    if [ $# -gt 0 ]; then
        for file in "$@"; do
            if [[ "$file" == *.yaml ]] || [[ "$file" == *.yml ]]; then
                validate_yaml "$file"
                validate_helm_values "$file"
                validate_helm_template "$file"
            fi
        done
    else
        echo "Usage: $0 <values-file.yaml> [more-files...]"
        echo ""
        echo "Example:"
        echo "  $0 values.yaml values-dev.yaml"
        echo ""
        echo "Running Kubernetes checks only..."
    fi

    check_kubernetes

    # Summary
    echo "========================================"
    echo "Validation Summary"
    echo "========================================"
    if [ $ERRORS -gt 0 ]; then
        print_error "Errors: $ERRORS"
    else
        print_status "Errors: 0"
    fi

    if [ $WARNINGS -gt 0 ]; then
        print_warning "Warnings: $WARNINGS"
    else
        print_status "Warnings: 0"
    fi

    if [ $ERRORS -gt 0 ]; then
        exit 1
    fi
}

main "$@"
