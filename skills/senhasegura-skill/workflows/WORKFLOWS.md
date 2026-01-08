# Senhasegura Workflows

Step-by-step workflows for common senhasegura operations.

---

## Workflow 1: Initial A2A Application Setup

### Objective
Configure a new A2A application for API integration with OAuth 2.0 authentication.

### Prerequisites
- senhasegura console access with admin privileges
- Target application/system defined

### Steps

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Create A2A Application                              │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   A2A > Applications > ⊕ New                                │
│                                                              │
│ Configuration:                                               │
│   • Name: my-app-integration                                │
│   • Authentication method: OAuth 2.0                        │
│   • Status: Enabled                                         │
│   • Description: Integration for production workloads       │
│                                                              │
│ Click: Save                                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Retrieve OAuth Credentials                          │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   A2A > Applications > my-app-integration > Authorization   │
│                                                              │
│ Copy and store securely:                                    │
│   • client_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx        │
│   • client_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Configure Authorization Rules                       │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   A2A > Authorizations > ⊕ New                              │
│                                                              │
│ Configuration:                                               │
│   • Application: my-app-integration                         │
│   • Module: PAM Core (or DSM)                              │
│   • Permission: Read and Write                              │
│   • IP Restriction: 10.0.0.0/8 (recommended)               │
│   • Credential filter: tag:production (optional)            │
│                                                              │
│ Security Best Practice:                                     │
│   Set one credential per authorization                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Test Authentication                                 │
├─────────────────────────────────────────────────────────────┤
│ Terminal:                                                    │
│                                                              │
│ curl -X POST "$SENHASEGURA_URL/iso/oauth2/token" \         │
│   -H "Content-Type: application/x-www-form-urlencoded" \   │
│   -d "grant_type=client_credentials" \                     │
│   -d "client_id=$CLIENT_ID" \                              │
│   -d "client_secret=$CLIENT_SECRET"                        │
│                                                              │
│ Expected Response:                                          │
│ {                                                           │
│   "access_token": "eyJhbGci...",                           │
│   "token_type": "Bearer",                                  │
│   "expires_in": 3600                                       │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Verify API Access                                   │
├─────────────────────────────────────────────────────────────┤
│ Terminal:                                                    │
│                                                              │
│ curl -X GET "$SENHASEGURA_URL/api/pam/credential" \        │
│   -H "Authorization: Bearer $ACCESS_TOKEN"                 │
│                                                              │
│ Expected: List of authorized credentials                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow 2: Kubernetes Secret Synchronization

### Objective
Sync secrets from Senhasegura DSM to Kubernetes using External Secrets Operator.

### Prerequisites
- Kubernetes cluster access
- Helm installed
- Senhasegura A2A credentials

### Steps

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Install External Secrets Operator                   │
├─────────────────────────────────────────────────────────────┤
│ Terminal:                                                    │
│                                                              │
│ helm repo add external-secrets \                            │
│   https://charts.external-secrets.io                        │
│                                                              │
│ helm install external-secrets \                             │
│   external-secrets/external-secrets \                       │
│   -n external-secrets \                                     │
│   --create-namespace \                                      │
│   --wait                                                    │
│                                                              │
│ Verify:                                                      │
│ kubectl get pods -n external-secrets                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create Authentication Secret                        │
├─────────────────────────────────────────────────────────────┤
│ Terminal:                                                    │
│                                                              │
│ kubectl create secret generic senhasegura-auth \            │
│   -n external-secrets \                                     │
│   --from-literal=clientId="$CLIENT_ID" \                   │
│   --from-literal=clientSecret="$CLIENT_SECRET"             │
│                                                              │
│ Or apply YAML:                                              │
│ kubectl apply -f samples/kubernetes/secretstore.yaml       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Create SecretStore                                  │
├─────────────────────────────────────────────────────────────┤
│ File: secretstore.yaml                                      │
│                                                              │
│ apiVersion: external-secrets.io/v1beta1                     │
│ kind: SecretStore                                           │
│ metadata:                                                   │
│   name: senhasegura-dsm                                     │
│   namespace: default                                        │
│ spec:                                                       │
│   provider:                                                 │
│     senhasegura:                                            │
│       url: "https://senhasegura.example.com"               │
│       module: DSM                                           │
│       auth:                                                 │
│         clientId:                                           │
│           secretRef:                                        │
│             name: senhasegura-auth                          │
│             key: clientId                                   │
│             namespace: external-secrets                     │
│         clientSecretSecretRef:                              │
│           name: senhasegura-auth                            │
│           key: clientSecret                                 │
│           namespace: external-secrets                       │
│                                                              │
│ kubectl apply -f secretstore.yaml                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Create ExternalSecret                               │
├─────────────────────────────────────────────────────────────┤
│ File: externalsecret.yaml                                   │
│                                                              │
│ apiVersion: external-secrets.io/v1beta1                     │
│ kind: ExternalSecret                                        │
│ metadata:                                                   │
│   name: database-credentials                                │
│ spec:                                                       │
│   refreshInterval: 1h                                       │
│   secretStoreRef:                                           │
│     name: senhasegura-dsm                                   │
│     kind: SecretStore                                       │
│   target:                                                   │
│     name: db-secret                                         │
│   data:                                                     │
│     - secretKey: password                                   │
│       remoteRef:                                            │
│         key: database-prod                                  │
│         property: password                                  │
│                                                              │
│ kubectl apply -f externalsecret.yaml                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Verify Synchronization                              │
├─────────────────────────────────────────────────────────────┤
│ Check ExternalSecret status:                                │
│ kubectl get externalsecret database-credentials            │
│                                                              │
│ Expected: STATUS = SecretSynced                             │
│                                                              │
│ Verify Kubernetes secret created:                           │
│ kubectl get secret db-secret -o yaml                       │
│                                                              │
│ Debug if needed:                                            │
│ kubectl describe externalsecret database-credentials       │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow 3: CI/CD Pipeline Secret Injection

### Objective
Inject secrets from Senhasegura DSM into CI/CD pipeline without exposing them.

### Prerequisites
- DSM CLI installed
- Senhasegura OAuth credentials stored in CI/CD secrets

### Steps

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Store Credentials in CI/CD Platform                 │
├─────────────────────────────────────────────────────────────┤
│ GitHub Actions:                                             │
│   Settings > Secrets and variables > Actions                │
│   Add:                                                      │
│     • SENHASEGURA_URL                                       │
│     • SENHASEGURA_CLIENT_ID                                 │
│     • SENHASEGURA_CLIENT_SECRET                             │
│                                                              │
│ GitLab CI:                                                  │
│   Settings > CI/CD > Variables                              │
│   Add masked variables (same as above)                      │
│                                                              │
│ Azure DevOps:                                               │
│   Pipelines > Library > Variable group                      │
│   Create: senhasegura-credentials                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Install DSM CLI in Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Step:                                              │
│                                                              │
│ - name: Install DSM CLI                                     │
│   run: |                                                    │
│     curl -LO https://github.com/senhasegura/dsmcli/\       │
│       releases/latest/download/dsm-linux-amd64             │
│     chmod +x dsm-linux-amd64                               │
│     sudo mv dsm-linux-amd64 /usr/local/bin/dsm             │
│     dsm --version                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch Secrets                                       │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Step:                                              │
│                                                              │
│ - name: Fetch Secrets                                       │
│   env:                                                      │
│     SENHASEGURA_URL: ${{ secrets.SENHASEGURA_URL }}        │
│     SENHASEGURA_CLIENT_ID: ${{ secrets.CLIENT_ID }}        │
│     SENHASEGURA_CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}│
│   run: |                                                    │
│     dsm runb \                                             │
│       --tool-name github \                                 │
│       --application my-app \                               │
│       --system production \                                │
│       --environment prod                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Load Secrets into Environment                       │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Step:                                              │
│                                                              │
│ - name: Load Secrets                                        │
│   run: |                                                    │
│     source .runb.vars                                      │
│     # Secrets now available as $DB_PASSWORD, etc.          │
│                                                              │
│ For GitHub Actions export to other steps:                   │
│     cat .runb.vars >> $GITHUB_ENV                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Use Secrets and Cleanup                             │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Step (use secrets):                                │
│                                                              │
│ - name: Deploy                                              │
│   run: |                                                    │
│     echo "Deploying with database: $DB_HOST"               │
│     ./deploy.sh                                            │
│                                                              │
│ Pipeline Step (cleanup - ALWAYS run):                       │
│                                                              │
│ - name: Cleanup                                             │
│   if: always()                                              │
│   run: rm -f .runb.vars                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow 4: Password Rotation Automation

### Objective
Configure automated password rotation for credentials.

### Prerequisites
- senhasegura console access
- Execution templates configured

### Steps

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Configure Execution Template                        │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   Executions > Templates > ⊕ New                            │
│                                                              │
│ Configuration:                                               │
│   • Name: Linux Password Change                             │
│   • Executor: SSH                                           │
│   • Plugin: Linux                                           │
│   • Credential type: Local User                             │
│                                                              │
│ Commands (example):                                         │
│   echo '[#NEW_PASSWORD#]' | passwd --stdin [#USERNAME#]    │
│                                                              │
│ Verification:                                               │
│   SSH login test with new password                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Create Execution Policy                             │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   Executions > Policies > ⊕ New                             │
│                                                              │
│ Configuration:                                               │
│   • Name: Monthly Linux Password Rotation                   │
│   • Status: Active                                          │
│   • Credentials: tag:linux-servers                          │
│   • Template: Linux Password Change                         │
│                                                              │
│ Schedule:                                                   │
│   • Frequency: Monthly                                      │
│   • Day: 1st                                                │
│   • Time: 02:00 AM                                          │
│                                                              │
│ Notification:                                               │
│   • Email: security@example.com                             │
│   • On: Success, Failure                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Test Rotation (Manual)                              │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   PAM Core > Credentials > [credential] > Actions > Rotate │
│                                                              │
│ Or via API:                                                 │
│                                                              │
│ curl -X POST "$URL/api/pam/credential/123/rotate" \        │
│   -H "Authorization: Bearer $TOKEN"                        │
│                                                              │
│ Verify:                                                      │
│   • Check Executions > History                              │
│   • Test login with new password                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Monitor Execution History                           │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   Executions > History                                      │
│                                                              │
│ Review:                                                      │
│   • Execution status (Success/Failed)                       │
│   • Execution logs                                          │
│   • Error messages                                          │
│                                                              │
│ Common Issues:                                              │
│   • Connection timeout: Check network/firewall             │
│   • Authentication failed: Verify current password         │
│   • Command failed: Review template syntax                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Workflow 5: SSH Key Registration and Rotation

### Objective
Register SSH keys in senhasegura and configure automatic rotation.

### Steps

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Generate SSH Key Pair                               │
├─────────────────────────────────────────────────────────────┤
│ Terminal (if generating new key):                           │
│                                                              │
│ ssh-keygen -t ed25519 -C "deploy@example.com" \            │
│   -f ~/.ssh/deploy_key                                     │
│                                                              │
│ Output:                                                      │
│   • Private key: ~/.ssh/deploy_key                          │
│   • Public key: ~/.ssh/deploy_key.pub                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Register Key in senhasegura                         │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   PAM Core > Credentials > SSH Keys > ⊕ New                │
│                                                              │
│ Configuration:                                               │
│   • Identifier: deploy-key-prod                             │
│   • Username: deploy                                        │
│   • Device: *.prod.example.com                              │
│   • Private key: [paste private key]                        │
│   • Public key: [paste public key]                          │
│   • Passphrase: [if applicable]                             │
│                                                              │
│ Rotation Settings:                                          │
│   • Enable automatic renewal: Yes                           │
│   • Renewal period: 90 days                                 │
│   • Key type: Ed25519                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Configure Target Devices                            │
├─────────────────────────────────────────────────────────────┤
│ Console Navigation:                                          │
│   PAM Core > Credentials > SSH Keys > deploy-key-prod      │
│   > Devices tab                                             │
│                                                              │
│ Add devices that:                                           │
│   • Will receive new public key on rotation                 │
│   • Allow key-based authentication                          │
│                                                              │
│ Ensure:                                                      │
│   • Devices are reachable from senhasegura                  │
│   • SSH service is running                                  │
│   • Authorized_keys path is correct                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Retrieve Key via API                                │
├─────────────────────────────────────────────────────────────┤
│ Terminal:                                                    │
│                                                              │
│ # List SSH keys                                             │
│ curl -X GET "$URL/api/pam/sshkey" \                        │
│   -H "Authorization: Bearer $TOKEN"                        │
│                                                              │
│ # Get specific key                                          │
│ curl -X GET "$URL/api/pam/sshkey/456" \                    │
│   -H "Authorization: Bearer $TOKEN"                        │
│                                                              │
│ # Use in application                                        │
│ PRIVATE_KEY=$(curl -s ... | jq -r '.private_key')          │
│ echo "$PRIVATE_KEY" > /tmp/deploy_key                      │
│ chmod 600 /tmp/deploy_key                                  │
│ ssh -i /tmp/deploy_key deploy@server                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Trigger Manual Rotation (if needed)                 │
├─────────────────────────────────────────────────────────────┤
│ Via Console:                                                │
│   SSH Keys > deploy-key-prod > Actions > Rotate            │
│                                                              │
│ Via API:                                                    │
│                                                              │
│ curl -X POST "$URL/api/pam/sshkey/456/rotate" \            │
│   -H "Authorization: Bearer $TOKEN"                        │
│                                                              │
│ senhasegura will:                                           │
│   1. Generate new key pair                                  │
│   2. Update authorized_keys on all devices                  │
│   3. Store new private key                                  │
│   4. Log the operation                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: API Patterns

### Authentication Flow
```bash
# 1. Get token
TOKEN=$(curl -s -X POST "$URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

# 2. Make API calls
curl -H "Authorization: Bearer $TOKEN" "$URL/api/..."

# 3. Token expires in 1 hour - request new one
```

### Common Operations
```bash
# List credentials
curl -H "Authorization: Bearer $TOKEN" "$URL/api/pam/credential"

# Get password
curl -H "Authorization: Bearer $TOKEN" "$URL/iso/coe/senha?credentialId=123"

# Release custody
curl -X DELETE -H "Authorization: Bearer $TOKEN" "$URL/iso/pam/credential/custody/123"

# List SSH keys
curl -H "Authorization: Bearer $TOKEN" "$URL/api/pam/sshkey"

# DSM secrets
curl -H "Authorization: Bearer $TOKEN" "$URL/api/dsm/secret"
```
