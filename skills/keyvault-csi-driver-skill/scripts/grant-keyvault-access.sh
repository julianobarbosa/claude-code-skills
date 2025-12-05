#!/bin/bash
#
# Grant Azure Key Vault access to a managed identity
#
# Usage: ./grant-keyvault-access.sh <key-vault-name> <object-id>
#
# This script automatically detects whether the Key Vault uses RBAC or
# Access Policies and grants the appropriate permissions.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KV_NAME="${1:?Usage: $0 <key-vault-name> <object-id>}"
OBJECT_ID="${2:?Usage: $0 <key-vault-name> <object-id>}"

echo -e "${GREEN}=== Key Vault Access Grant Script ===${NC}"
echo "Key Vault: $KV_NAME"
echo "Object ID: $OBJECT_ID"
echo ""

# Check Azure CLI authentication
if ! az account show &>/dev/null; then
    echo -e "${RED}Error: Not logged in to Azure CLI. Run: az login${NC}"
    exit 1
fi

# Get Key Vault details
echo -e "${YELLOW}Fetching Key Vault details...${NC}"
KV_INFO=$(az keyvault show -n "$KV_NAME" --query "{id:id, rbac:properties.enableRbacAuthorization, rg:resourceGroup}" -o json 2>/dev/null)

if [ -z "$KV_INFO" ]; then
    echo -e "${RED}Error: Key Vault '$KV_NAME' not found${NC}"
    exit 1
fi

RBAC_ENABLED=$(echo "$KV_INFO" | jq -r '.rbac')
KV_ID=$(echo "$KV_INFO" | jq -r '.id')
RG_NAME=$(echo "$KV_INFO" | jq -r '.rg')

echo "Resource Group: $RG_NAME"
echo "RBAC Enabled: $RBAC_ENABLED"
echo ""

if [ "$RBAC_ENABLED" == "true" ]; then
    echo -e "${YELLOW}Granting RBAC role 'Key Vault Secrets User'...${NC}"

    if az role assignment create \
        --role "Key Vault Secrets User" \
        --assignee-object-id "$OBJECT_ID" \
        --assignee-principal-type ServicePrincipal \
        --scope "$KV_ID" 2>/dev/null; then
        echo -e "${GREEN}RBAC role assigned successfully${NC}"
    else
        echo -e "${YELLOW}Role may already exist or there was an error${NC}"
    fi

    echo -e "\n${YELLOW}Verifying role assignment...${NC}"
    az role assignment list \
        --assignee "$OBJECT_ID" \
        --scope "$KV_ID" \
        --query "[].{role:roleDefinitionName, scope:scope}" -o table
else
    echo -e "${YELLOW}Granting Access Policy permissions (get, list)...${NC}"

    if az keyvault set-policy \
        --name "$KV_NAME" \
        --object-id "$OBJECT_ID" \
        --secret-permissions get list; then
        echo -e "${GREEN}Access policy set successfully${NC}"
    else
        echo -e "${RED}Failed to set access policy${NC}"
        exit 1
    fi

    echo -e "\n${YELLOW}Verifying access policy...${NC}"
    az keyvault show -n "$KV_NAME" \
        --query "properties.accessPolicies[?objectId=='$OBJECT_ID'].{objectId:objectId, permissions:permissions.secrets}" -o table
fi

echo -e "\n${GREEN}=== Complete ===${NC}"
echo "Next steps:"
echo "1. Delete the failing pod to trigger a restart"
echo "2. Monitor pod status: kubectl get pod <pod-name> -w"
