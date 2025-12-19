#!/usr/bin/env bash
#
# Azure DevOps CLI Examples
#
# This script provides bash examples for common Azure DevOps operations
# using curl and the REST API.
#
# Prerequisites:
#   - curl
#   - jq (for JSON parsing)
#   - base64
#
# Environment Variables:
#   AZURE_DEVOPS_ORG: Organization name
#   AZURE_DEVOPS_PAT: Personal Access Token
#   AZURE_DEVOPS_PROJECT: Project name
#

set -euo pipefail

# Configuration
ORG="${AZURE_DEVOPS_ORG:-your-org}"
PAT="${AZURE_DEVOPS_PAT:-your-pat}"
PROJECT="${AZURE_DEVOPS_PROJECT:-your-project}"
API_VERSION="7.2-preview.3"

# Base URL
BASE_URL="https://dev.azure.com/${ORG}"

# Generate auth header
get_auth() {
    echo -n ":${PAT}" | base64
}

AUTH_HEADER="Authorization: Basic $(get_auth)"

# ============================================================================
# Work Item Functions
# ============================================================================

# Get a single work item
get_work_item() {
    local id="$1"
    local expand="${2:-all}"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/wit/workitems/${id}?api-version=${API_VERSION}&\$expand=${expand}"
}

# Create a work item
create_work_item() {
    local type="$1"
    local title="$2"
    local description="${3:-}"

    local body="["
    body+="{\"op\":\"add\",\"path\":\"/fields/System.Title\",\"value\":\"${title}\"}"

    if [[ -n "${description}" ]]; then
        body+=",{\"op\":\"add\",\"path\":\"/fields/System.Description\",\"value\":\"${description}\"}"
    fi

    body+="]"

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json-patch+json" \
        -d "${body}" \
        "${BASE_URL}/${PROJECT}/_apis/wit/workitems/\$${type}?api-version=${API_VERSION}"
}

# Update a work item
update_work_item() {
    local id="$1"
    local field="$2"
    local value="$3"

    local body="[{\"op\":\"add\",\"path\":\"/fields/${field}\",\"value\":\"${value}\"}]"

    curl -s -X PATCH \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json-patch+json" \
        -d "${body}" \
        "${BASE_URL}/${PROJECT}/_apis/wit/workitems/${id}?api-version=${API_VERSION}"
}

# Run WIQL query
run_wiql() {
    local query="$1"

    local body="{\"query\":\"${query}\"}"

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "${BASE_URL}/${PROJECT}/_apis/wit/wiql?api-version=${API_VERSION}"
}

# ============================================================================
# Pipeline Functions
# ============================================================================

# List pipelines
list_pipelines() {
    local top="${1:-50}"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/pipelines?api-version=7.2-preview.1&\$top=${top}"
}

# Get pipeline
get_pipeline() {
    local pipeline_id="$1"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/pipelines/${pipeline_id}?api-version=7.2-preview.1"
}

# Run pipeline
run_pipeline() {
    local pipeline_id="$1"
    local branch="${2:-main}"

    local body="{\"resources\":{\"repositories\":{\"self\":{\"refName\":\"refs/heads/${branch}\"}}}}"

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "${BASE_URL}/${PROJECT}/_apis/pipelines/${pipeline_id}/runs?api-version=7.2-preview.1"
}

# List builds
list_builds() {
    local top="${1:-50}"
    local status="${2:-}"

    local url="${BASE_URL}/${PROJECT}/_apis/build/builds?api-version=7.2-preview.7&\$top=${top}"

    if [[ -n "${status}" ]]; then
        url+="&statusFilter=${status}"
    fi

    curl -s -H "${AUTH_HEADER}" "${url}"
}

# Get build
get_build() {
    local build_id="$1"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/build/builds/${build_id}?api-version=7.2-preview.7"
}

# Get build logs
get_build_logs() {
    local build_id="$1"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/build/builds/${build_id}/logs?api-version=7.2-preview.2"
}

# Get specific log content
get_log_content() {
    local build_id="$1"
    local log_id="$2"

    curl -s -H "${AUTH_HEADER}" \
        -H "Accept: text/plain" \
        "${BASE_URL}/${PROJECT}/_apis/build/builds/${build_id}/logs/${log_id}?api-version=7.2-preview.2"
}

# ============================================================================
# Repository Functions
# ============================================================================

# List repositories
list_repos() {
    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/git/repositories?api-version=7.2-preview.1"
}

# Get repository
get_repo() {
    local repo_name="$1"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/git/repositories/${repo_name}?api-version=7.2-preview.1"
}

# List branches
list_branches() {
    local repo_id="$1"
    local filter="${2:-}"

    local url="${BASE_URL}/${PROJECT}/_apis/git/repositories/${repo_id}/refs?api-version=7.2-preview.1&filter=heads"

    if [[ -n "${filter}" ]]; then
        url+="/${filter}"
    fi

    curl -s -H "${AUTH_HEADER}" "${url}"
}

# ============================================================================
# Pull Request Functions
# ============================================================================

# List pull requests
list_prs() {
    local repo_id="$1"
    local status="${2:-active}"
    local top="${3:-50}"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/git/repositories/${repo_id}/pullrequests?api-version=7.2-preview.1&searchCriteria.status=${status}&\$top=${top}"
}

# Get pull request
get_pr() {
    local repo_id="$1"
    local pr_id="$2"

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/git/repositories/${repo_id}/pullrequests/${pr_id}?api-version=7.2-preview.1"
}

# Create pull request
create_pr() {
    local repo_id="$1"
    local source_branch="$2"
    local target_branch="$3"
    local title="$4"
    local description="${5:-}"

    local body=$(cat <<EOF
{
    "sourceRefName": "refs/heads/${source_branch}",
    "targetRefName": "refs/heads/${target_branch}",
    "title": "${title}",
    "description": "${description}"
}
EOF
)

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "${BASE_URL}/${PROJECT}/_apis/git/repositories/${repo_id}/pullrequests?api-version=7.2-preview.1"
}

# ============================================================================
# Search Functions
# ============================================================================

# Search code
search_code() {
    local query="$1"
    local top="${2:-25}"

    local body=$(cat <<EOF
{
    "searchText": "${query}",
    "\$top": ${top}
}
EOF
)

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "https://almsearch.dev.azure.com/${ORG}/${PROJECT}/_apis/search/codesearchresults?api-version=7.2-preview.1"
}

# Search work items
search_work_items() {
    local query="$1"
    local top="${2:-25}"

    local body=$(cat <<EOF
{
    "searchText": "${query}",
    "\$top": ${top}
}
EOF
)

    curl -s -X POST \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "https://almsearch.dev.azure.com/${ORG}/${PROJECT}/_apis/search/workitemsearchresults?api-version=7.2-preview.1"
}

# ============================================================================
# Wiki Functions
# ============================================================================

# List wikis
list_wikis() {
    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/wiki/wikis?api-version=7.2-preview.2"
}

# Get wiki page content
get_wiki_page() {
    local wiki_id="$1"
    local page_path="$2"

    # URL encode the path
    local encoded_path=$(echo -n "${page_path}" | jq -sRr @uri)

    curl -s -H "${AUTH_HEADER}" \
        "${BASE_URL}/${PROJECT}/_apis/wiki/wikis/${wiki_id}/pages?path=${encoded_path}&api-version=7.2-preview.1&includeContent=true"
}

# ============================================================================
# Usage Examples
# ============================================================================

usage() {
    cat <<EOF
Azure DevOps CLI Examples

Usage: $0 <command> [arguments]

Commands:
  work-item get <id>              Get work item by ID
  work-item create <type> <title> Create work item
  work-item update <id> <field> <value>  Update work item field

  pipeline list                   List pipelines
  pipeline get <id>               Get pipeline by ID
  pipeline run <id> [branch]      Run pipeline

  build list [top] [status]       List builds
  build get <id>                  Get build by ID
  build logs <id>                 Get build logs

  repo list                       List repositories
  repo get <name>                 Get repository
  branch list <repo_id>           List branches

  pr list <repo_id> [status]      List pull requests
  pr get <repo_id> <pr_id>        Get pull request
  pr create <repo_id> <source> <target> <title>  Create PR

  search code <query>             Search code
  search work-items <query>       Search work items

  wiki list                       List wikis
  wiki page <wiki_id> <path>      Get wiki page

Environment Variables:
  AZURE_DEVOPS_ORG      Organization name (current: ${ORG})
  AZURE_DEVOPS_PAT      Personal Access Token
  AZURE_DEVOPS_PROJECT  Project name (current: ${PROJECT})
EOF
}

# Main command dispatcher
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "${cmd}" in
        work-item)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                get) get_work_item "$@" | jq . ;;
                create) create_work_item "$@" | jq . ;;
                update) update_work_item "$@" | jq . ;;
                *) echo "Unknown work-item command: ${subcmd}" ;;
            esac
            ;;
        pipeline)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_pipelines "$@" | jq . ;;
                get) get_pipeline "$@" | jq . ;;
                run) run_pipeline "$@" | jq . ;;
                *) echo "Unknown pipeline command: ${subcmd}" ;;
            esac
            ;;
        build)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_builds "$@" | jq . ;;
                get) get_build "$@" | jq . ;;
                logs) get_build_logs "$@" | jq . ;;
                *) echo "Unknown build command: ${subcmd}" ;;
            esac
            ;;
        repo)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_repos | jq . ;;
                get) get_repo "$@" | jq . ;;
                *) echo "Unknown repo command: ${subcmd}" ;;
            esac
            ;;
        branch)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_branches "$@" | jq . ;;
                *) echo "Unknown branch command: ${subcmd}" ;;
            esac
            ;;
        pr)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_prs "$@" | jq . ;;
                get) get_pr "$@" | jq . ;;
                create) create_pr "$@" | jq . ;;
                *) echo "Unknown pr command: ${subcmd}" ;;
            esac
            ;;
        search)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                code) search_code "$@" | jq . ;;
                work-items) search_work_items "$@" | jq . ;;
                *) echo "Unknown search command: ${subcmd}" ;;
            esac
            ;;
        wiki)
            local subcmd="${1:-}"
            shift || true
            case "${subcmd}" in
                list) list_wikis | jq . ;;
                page) get_wiki_page "$@" | jq . ;;
                *) echo "Unknown wiki command: ${subcmd}" ;;
            esac
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo "Unknown command: ${cmd}"
            usage
            exit 1
            ;;
    esac
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
