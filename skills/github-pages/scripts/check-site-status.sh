#!/bin/bash
# Check GitHub Pages site status
# Usage: ./check-site-status.sh username/repo [custom-domain]

set -euo pipefail

REPO="${1:-}"
CUSTOM_DOMAIN="${2:-}"

if [[ -z "$REPO" ]]; then
    echo "Usage: $0 <username/repo> [custom-domain]"
    echo "Example: $0 octocat/hello-world"
    echo "Example: $0 octocat/hello-world example.com"
    exit 1
fi

# Extract username and repo name
IFS='/' read -r USERNAME REPONAME <<< "$REPO"

if [[ -z "$USERNAME" ]] || [[ -z "$REPONAME" ]]; then
    echo "Error: Invalid repository format. Use username/repo"
    exit 1
fi

echo "========================================="
echo "GitHub Pages Site Status Check"
echo "Repository: $REPO"
echo "========================================="
echo ""

# Determine site URLs
if [[ "$REPONAME" == "$USERNAME.github.io" ]]; then
    SITE_TYPE="User/Organization"
    PAGES_URL="https://$USERNAME.github.io"
else
    SITE_TYPE="Project"
    PAGES_URL="https://$USERNAME.github.io/$REPONAME"
fi

echo "Site Type: $SITE_TYPE"
echo "Expected URL: $PAGES_URL"
if [[ -n "$CUSTOM_DOMAIN" ]]; then
    echo "Custom Domain: https://$CUSTOM_DOMAIN"
fi
echo ""

# Function to check HTTP status
check_url() {
    local url=$1
    local name=$2

    echo "Checking $name..."

    local response
    response=$(curl -sIL -w "%{http_code}" -o /dev/null --connect-timeout 10 "$url" 2>/dev/null) || response="000"

    case $response in
        200)
            echo "  ✅ $url - OK (200)"
            return 0
            ;;
        301|302)
            echo "  ↪️  $url - Redirect ($response)"
            local redirect_url
            redirect_url=$(curl -sI "$url" | grep -i "location:" | head -1 | awk '{print $2}' | tr -d '\r')
            echo "      → $redirect_url"
            return 0
            ;;
        404)
            echo "  ❌ $url - Not Found (404)"
            return 1
            ;;
        000)
            echo "  ❌ $url - Connection failed"
            return 1
            ;;
        *)
            echo "  ⚠️  $url - HTTP $response"
            return 1
            ;;
    esac
}

# Check Pages URL
echo ""
echo "========================================="
echo "Site Availability"
echo "========================================="
echo ""

check_url "$PAGES_URL" "GitHub Pages URL"

if [[ -n "$CUSTOM_DOMAIN" ]]; then
    echo ""
    check_url "https://$CUSTOM_DOMAIN" "Custom Domain (HTTPS)"
    check_url "https://www.$CUSTOM_DOMAIN" "WWW Subdomain (HTTPS)"
fi

# Check via GitHub API (requires gh CLI)
if command -v gh &> /dev/null; then
    echo ""
    echo "========================================="
    echo "GitHub API Status"
    echo "========================================="
    echo ""

    # Check if authenticated
    if gh auth status &> /dev/null; then
        echo "Fetching Pages configuration..."

        pages_info=$(gh api "repos/$REPO/pages" 2>/dev/null) || {
            echo "  ❌ GitHub Pages not enabled or no access"
            exit 0
        }

        status=$(echo "$pages_info" | jq -r '.status // "unknown"')
        url=$(echo "$pages_info" | jq -r '.html_url // "N/A"')
        cname=$(echo "$pages_info" | jq -r '.cname // "none"')
        https=$(echo "$pages_info" | jq -r '.https_enforced // false')
        source_branch=$(echo "$pages_info" | jq -r '.source.branch // "N/A"')
        source_path=$(echo "$pages_info" | jq -r '.source.path // "/"')
        build_type=$(echo "$pages_info" | jq -r '.build_type // "N/A"')

        echo ""
        echo "  Status: $status"
        echo "  URL: $url"
        echo "  Custom Domain: $cname"
        echo "  HTTPS Enforced: $https"
        echo "  Build Type: $build_type"
        if [[ "$build_type" != "workflow" ]]; then
            echo "  Source Branch: $source_branch"
            echo "  Source Path: $source_path"
        fi

        # Check latest build
        echo ""
        echo "Latest Build:"

        latest_build=$(gh api "repos/$REPO/pages/builds" --jq '.[0]' 2>/dev/null) || {
            echo "  No build information available"
            exit 0
        }

        if [[ -n "$latest_build" ]] && [[ "$latest_build" != "null" ]]; then
            build_status=$(echo "$latest_build" | jq -r '.status // "unknown"')
            build_created=$(echo "$latest_build" | jq -r '.created_at // "N/A"')
            build_commit=$(echo "$latest_build" | jq -r '.commit // "N/A"' | head -c 7)

            case $build_status in
                built)
                    echo "  ✅ Status: Built successfully"
                    ;;
                building)
                    echo "  🔄 Status: Building..."
                    ;;
                errored)
                    echo "  ❌ Status: Build error"
                    ;;
                *)
                    echo "  Status: $build_status"
                    ;;
            esac
            echo "  Created: $build_created"
            echo "  Commit: $build_commit"
        else
            echo "  No builds found (using GitHub Actions?)"
        fi
    else
        echo "  ⚠️  Not authenticated with gh CLI"
        echo "  Run: gh auth login"
    fi
else
    echo ""
    echo "Tip: Install GitHub CLI (gh) for more detailed status"
    echo "https://cli.github.com/"
fi

echo ""
echo "========================================="
echo "Troubleshooting"
echo "========================================="
echo ""
echo "If site is not available:"
echo "  1. Check Settings > Pages in repository"
echo "  2. Verify entry file exists (index.html, index.md, README.md)"
echo "  3. Check Actions tab for build errors"
echo "  4. Wait up to 10 minutes for deployment"
echo ""
echo "Documentation: https://docs.github.com/en/pages"
