#!/usr/bin/env bash
#
# manage-projects.sh - Dependency-Track project management utilities
#
# Usage:
#   ./manage-projects.sh list
#   ./manage-projects.sh get -n "project-name" -v "1.0.0"
#   ./manage-projects.sh create -n "project-name" -v "1.0.0" -d "Description"
#   ./manage-projects.sh delete -u "project-uuid"
#   ./manage-projects.sh export -n "project-name" -v "1.0.0" -o sbom.json
#
# Environment variables:
#   DTRACK_URL      - Dependency-Track base URL
#   DTRACK_API_KEY  - API key for authentication

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    cat <<EOF
Usage: $0 <command> [options]

Commands:
    list                        List all projects
    get                         Get project details
    create                      Create a new project
    delete                      Delete a project
    export                      Export project SBOM
    vulnerabilities             List project vulnerabilities
    components                  List project components

Options:
    -n, --name          Project name
    -v, --version       Project version
    -u, --uuid          Project UUID
    -d, --description   Project description (for create)
    -t, --tags          Comma-separated tags (for create)
    -o, --output        Output file (for export)
    -f, --format        Output format: json, xml (for export, default: json)
    --json              Output as JSON
    -h, --help          Show this help

Environment:
    DTRACK_URL          Dependency-Track base URL
    DTRACK_API_KEY      API key for authentication
EOF
    exit 1
}

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

check_env() {
    if [[ -z "${DTRACK_URL:-}" ]]; then
        log_error "DTRACK_URL environment variable not set"
        exit 1
    fi
    if [[ -z "${DTRACK_API_KEY:-}" ]]; then
        log_error "DTRACK_API_KEY environment variable not set"
        exit 1
    fi
}

api_get() {
    curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" "${DTRACK_URL}/api/v1$1"
}

api_put() {
    curl -s -X PUT -H "X-Api-Key: ${DTRACK_API_KEY}" \
        -H "Content-Type: application/json" \
        "${DTRACK_URL}/api/v1$1" -d "$2"
}

api_delete() {
    curl -s -X DELETE -H "X-Api-Key: ${DTRACK_API_KEY}" "${DTRACK_URL}/api/v1$1"
}

cmd_list() {
    local json_output="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --json) json_output="true"; shift ;;
            *) shift ;;
        esac
    done

    PROJECTS=$(api_get "/project?pageSize=1000")

    if [[ "$json_output" == "true" ]]; then
        echo "$PROJECTS" | jq .
    else
        echo ""
        echo "Projects:"
        echo "=========================================="
        echo "$PROJECTS" | jq -r '.[] | "\(.name):\(.version) (\(.uuid))"' | sort
        echo ""
        TOTAL=$(echo "$PROJECTS" | jq 'length')
        echo "Total: $TOTAL projects"
    fi
}

cmd_get() {
    local project_name="" project_version="" project_uuid="" json_output="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name) project_name="$2"; shift 2 ;;
            -v|--version) project_version="$2"; shift 2 ;;
            -u|--uuid) project_uuid="$2"; shift 2 ;;
            --json) json_output="true"; shift ;;
            *) shift ;;
        esac
    done

    if [[ -n "$project_uuid" ]]; then
        PROJECT=$(api_get "/project/${project_uuid}")
    elif [[ -n "$project_name" && -n "$project_version" ]]; then
        PROJECT=$(api_get "/project/lookup?name=${project_name}&version=${project_version}")
    else
        log_error "Either --uuid or --name and --version required"
        exit 1
    fi

    if [[ "$json_output" == "true" ]]; then
        echo "$PROJECT" | jq .
    else
        echo ""
        echo "Project Details:"
        echo "=========================================="
        echo "Name:        $(echo "$PROJECT" | jq -r '.name')"
        echo "Version:     $(echo "$PROJECT" | jq -r '.version')"
        echo "UUID:        $(echo "$PROJECT" | jq -r '.uuid')"
        echo "Description: $(echo "$PROJECT" | jq -r '.description // "N/A"')"
        echo "Active:      $(echo "$PROJECT" | jq -r '.active')"
        echo "Tags:        $(echo "$PROJECT" | jq -r '[.tags[]?.name] | join(", ") // "None"')"
        echo "Last BOM:    $(echo "$PROJECT" | jq -r '.lastBomImportFormat // "N/A"')"
        echo "Created:     $(echo "$PROJECT" | jq -r '.created // "N/A"')"
    fi
}

cmd_create() {
    local project_name="" project_version="" description="" tags=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name) project_name="$2"; shift 2 ;;
            -v|--version) project_version="$2"; shift 2 ;;
            -d|--description) description="$2"; shift 2 ;;
            -t|--tags) tags="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [[ -z "$project_name" || -z "$project_version" ]]; then
        log_error "--name and --version required"
        exit 1
    fi

    # Build tags JSON array
    local tags_json="[]"
    if [[ -n "$tags" ]]; then
        tags_json=$(echo "$tags" | tr ',' '\n' | jq -R . | jq -s 'map({name: .})')
    fi

    local payload
    payload=$(jq -n \
        --arg name "$project_name" \
        --arg version "$project_version" \
        --arg description "$description" \
        --argjson tags "$tags_json" \
        '{name: $name, version: $version, description: $description, tags: $tags, active: true}')

    log_info "Creating project: ${project_name}:${project_version}"
    RESULT=$(api_put "/project" "$payload")

    uuid=$(echo "$RESULT" | jq -r '.uuid')
    if [[ "$uuid" != "null" && -n "$uuid" ]]; then
        log_info "Project created successfully!"
        echo "UUID: $uuid"
    else
        log_error "Failed to create project"
        echo "$RESULT"
        exit 1
    fi
}

cmd_delete() {
    local project_uuid=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--uuid) project_uuid="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [[ -z "$project_uuid" ]]; then
        log_error "--uuid required"
        exit 1
    fi

    log_warn "Deleting project: $project_uuid"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        api_delete "/project/${project_uuid}"
        log_info "Project deleted"
    else
        log_info "Cancelled"
    fi
}

cmd_export() {
    local project_name="" project_version="" output_file="" format="json"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name) project_name="$2"; shift 2 ;;
            -v|--version) project_version="$2"; shift 2 ;;
            -o|--output) output_file="$2"; shift 2 ;;
            -f|--format) format="$2"; shift 2 ;;
            *) shift ;;
        esac
    done

    if [[ -z "$project_name" || -z "$project_version" ]]; then
        log_error "--name and --version required"
        exit 1
    fi

    # Get project UUID
    PROJECT=$(api_get "/project/lookup?name=${project_name}&version=${project_version}")
    project_uuid=$(echo "$PROJECT" | jq -r '.uuid')

    if [[ "$project_uuid" == "null" || -z "$project_uuid" ]]; then
        log_error "Project not found"
        exit 1
    fi

    log_info "Exporting SBOM for ${project_name}:${project_version}"

    SBOM=$(curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" \
        "${DTRACK_URL}/api/v1/bom/cyclonedx/project/${project_uuid}?format=${format}")

    if [[ -n "$output_file" ]]; then
        echo "$SBOM" > "$output_file"
        log_info "SBOM exported to: $output_file"
    else
        echo "$SBOM"
    fi
}

cmd_vulnerabilities() {
    local project_name="" project_version="" json_output="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name) project_name="$2"; shift 2 ;;
            -v|--version) project_version="$2"; shift 2 ;;
            --json) json_output="true"; shift ;;
            *) shift ;;
        esac
    done

    PROJECT=$(api_get "/project/lookup?name=${project_name}&version=${project_version}")
    project_uuid=$(echo "$PROJECT" | jq -r '.uuid')

    VULNS=$(api_get "/vulnerability/project/${project_uuid}")

    if [[ "$json_output" == "true" ]]; then
        echo "$VULNS" | jq .
    else
        echo ""
        echo "Vulnerabilities for ${project_name}:${project_version}:"
        echo "=========================================="
        echo "$VULNS" | jq -r '.[] | "\(.vulnerability.severity): \(.vulnerability.vulnId) - \(.component.name):\(.component.version)"' | sort
        echo ""
        echo "Summary:"
        echo "  Critical: $(echo "$VULNS" | jq '[.[] | select(.vulnerability.severity == "CRITICAL")] | length')"
        echo "  High:     $(echo "$VULNS" | jq '[.[] | select(.vulnerability.severity == "HIGH")] | length')"
        echo "  Medium:   $(echo "$VULNS" | jq '[.[] | select(.vulnerability.severity == "MEDIUM")] | length')"
        echo "  Low:      $(echo "$VULNS" | jq '[.[] | select(.vulnerability.severity == "LOW")] | length')"
    fi
}

cmd_components() {
    local project_name="" project_version="" json_output="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name) project_name="$2"; shift 2 ;;
            -v|--version) project_version="$2"; shift 2 ;;
            --json) json_output="true"; shift ;;
            *) shift ;;
        esac
    done

    PROJECT=$(api_get "/project/lookup?name=${project_name}&version=${project_version}")
    project_uuid=$(echo "$PROJECT" | jq -r '.uuid')

    COMPONENTS=$(api_get "/component/project/${project_uuid}?pageSize=1000")

    if [[ "$json_output" == "true" ]]; then
        echo "$COMPONENTS" | jq .
    else
        echo ""
        echo "Components for ${project_name}:${project_version}:"
        echo "=========================================="
        echo "$COMPONENTS" | jq -r '.[] | "\(.name):\(.version) [\(.purl // "no-purl")]"' | sort
        echo ""
        TOTAL=$(echo "$COMPONENTS" | jq 'length')
        echo "Total: $TOTAL components"
    fi
}

# Main
check_env

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    list)
        cmd_list "$@"
        ;;
    get)
        cmd_get "$@"
        ;;
    create)
        cmd_create "$@"
        ;;
    delete)
        cmd_delete "$@"
        ;;
    export)
        cmd_export "$@"
        ;;
    vulnerabilities|vulns)
        cmd_vulnerabilities "$@"
        ;;
    components)
        cmd_components "$@"
        ;;
    -h|--help|"")
        usage
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        usage
        ;;
esac
