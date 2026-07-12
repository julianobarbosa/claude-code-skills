#!/bin/bash
# Setup script for GitHub CLI with 1Password integration
# This script configures gh CLI to use 1Password for authentication

set -e

echo "=== 1Password GitHub CLI Plugin Setup ==="
echo ""

# Check prerequisites
command -v op >/dev/null 2>&1 || { echo "Error: 1Password CLI (op) is not installed"; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "Error: GitHub CLI (gh) is not installed"; exit 1; }

# Sign in to 1Password if needed
echo "Step 1: Checking 1Password authentication..."
if ! op whoami >/dev/null 2>&1; then
    echo "Please sign in to 1Password:"
    eval $(op signin)
fi
echo "Signed in as: $(op whoami --format json | jq -r '.email')"
echo ""

# List GitHub-related items
echo "Step 2: Available GitHub tokens in 1Password:"
echo "-------------------------------------------"
op item list --categories "API Credential,Login" 2>/dev/null | grep -i github | nl
echo ""

# Prompt for item selection
read -p "Enter the number of the item to use (or 'q' to quit): " selection
if [[ "$selection" == "q" ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Get the item ID from selection
ITEM_ID=$(op item list --categories "API Credential,Login" 2>/dev/null | grep -i github | sed -n "${selection}p" | awk '{print $1}')

if [[ -z "$ITEM_ID" ]]; then
    echo "Error: Invalid selection"
    exit 1
fi

ITEM_NAME=$(op item get "$ITEM_ID" --format json | jq -r '.title')
echo ""
echo "Selected: $ITEM_NAME ($ITEM_ID)"
echo ""

# Remove old plugin configuration
echo "Step 3: Clearing old gh plugin configuration..."
rm -f ~/.config/op/plugins/used_items/gh.json 2>/dev/null || true
echo "Done."
echo ""

# Initialize gh plugin
echo "Step 4: Initializing gh plugin with 1Password..."
op plugin init gh
echo ""

# Configure git credential helper
echo "Step 5: Configuring git credential helper..."

# Remove old credential helpers for github.com
git config --global --unset-all credential.https://github.com.helper 2>/dev/null || true
git config --global --unset-all credential.https://gist.github.com.helper 2>/dev/null || true

# Set gh as credential helper
git config --global credential.https://github.com.helper '!/opt/homebrew/bin/gh auth git-credential'
git config --global credential.https://gist.github.com.helper '!/opt/homebrew/bin/gh auth git-credential'

echo "Git credential helper configured."
echo ""

# Verify setup
echo "Step 6: Verifying setup..."
echo ""
echo "GitHub CLI auth status:"
gh auth status
echo ""

echo "=== Setup Complete ==="
echo ""
echo "You can now use git push/pull with GitHub repositories."
echo "The gh CLI will automatically use 1Password for authentication."
echo ""
echo "To test, run:"
echo "  git push origin main"
