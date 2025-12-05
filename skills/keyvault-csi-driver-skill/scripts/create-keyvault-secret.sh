#!/bin/bash
#
# Create or update a secret in Azure Key Vault
#
# Usage: ./create-keyvault-secret.sh <key-vault-name> <secret-name> [secret-value]
#
# If secret-value is not provided, it will be read from stdin or prompted.
#
# Examples:
#   ./create-keyvault-secret.sh kv-cafehyna-dev-hlg my-app-password "secret123"
#   echo "secret123" | ./create-keyvault-secret.sh kv-cafehyna-dev-hlg my-app-password
#   ./create-keyvault-secret.sh kv-cafehyna-dev-hlg my-app-password  # prompts for value

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KV_NAME="${1:?Usage: $0 <key-vault-name> <secret-name> [secret-value]}"
SECRET_NAME="${2:?Usage: $0 <key-vault-name> <secret-name> [secret-value]}"
SECRET_VALUE="${3:-}"

echo -e "${GREEN}=== Azure Key Vault Secret Creator ===${NC}"
echo "Key Vault: $KV_NAME"
echo "Secret Name: $SECRET_NAME"
echo ""

# Check Azure CLI authentication
if ! az account show &>/dev/null; then
    echo -e "${RED}Error: Not logged in to Azure CLI. Run: az login${NC}"
    exit 1
fi

# Verify Key Vault exists
echo -e "${YELLOW}Verifying Key Vault...${NC}"
if ! az keyvault show -n "$KV_NAME" &>/dev/null; then
    echo -e "${RED}Error: Key Vault '$KV_NAME' not found${NC}"
    exit 1
fi
echo -e "${GREEN}Key Vault found${NC}"
echo ""

# Get secret value if not provided
if [ -z "$SECRET_VALUE" ]; then
    if [ -t 0 ]; then
        # Interactive mode - prompt for password
        echo -e "${YELLOW}Enter secret value (input hidden):${NC}"
        read -s SECRET_VALUE
        echo ""
    else
        # Read from stdin
        SECRET_VALUE=$(cat)
    fi
fi

if [ -z "$SECRET_VALUE" ]; then
    echo -e "${RED}Error: Secret value cannot be empty${NC}"
    exit 1
fi

# Check if secret already exists
echo -e "${YELLOW}Checking if secret exists...${NC}"
if az keyvault secret show --vault-name "$KV_NAME" --name "$SECRET_NAME" &>/dev/null; then
    echo -e "${YELLOW}Secret '$SECRET_NAME' already exists. It will be updated.${NC}"
    ACTION="updated"
else
    echo "Secret '$SECRET_NAME' does not exist. It will be created."
    ACTION="created"
fi
echo ""

# Create or update secret
echo -e "${YELLOW}Setting secret value...${NC}"
RESULT=$(az keyvault secret set \
    --vault-name "$KV_NAME" \
    --name "$SECRET_NAME" \
    --value "$SECRET_VALUE" \
    --query "{name:name, created:attributes.created, updated:attributes.updated, version:id}" \
    -o json)

echo -e "${GREEN}Secret $ACTION successfully!${NC}"
echo ""
echo "Details:"
echo "$RESULT" | jq '.'
echo ""

echo -e "${GREEN}=== Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Create/update SecretProviderClass to reference this secret"
echo "2. If pods are already running, delete them to pick up the new secret"
echo ""
echo "SecretProviderClass object example:"
echo "  objects: |"
echo "    array:"
echo "      - |"
echo "        objectName: \"$SECRET_NAME\""
echo "        objectType: \"secret\""
