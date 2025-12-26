# Security Checklist Reference

Pre-commit security verification to prevent sensitive data exposure.

## Quick Scan Commands

```bash
# Check for common secrets patterns
git diff --cached | grep -iE "(api[_-]?key|secret|password|token|credential|private[_-]?key)"

# Check for environment files
git diff --cached --name-only | grep -E "\.env|\.env\.|config\.json|secrets\."

# Check for key files
git diff --cached --name-only | grep -E "\.(pem|key|p12|pfx|jks)$"
```

## Files to NEVER Commit

### Environment Files

| File Pattern | Risk |
|--------------|------|
| `.env` | API keys, database credentials |
| `.env.local` | Local overrides with secrets |
| `.env.production` | Production secrets |
| `.env.*` | Any environment variant |
| `config.local.json` | Local configuration |

### Credential Files

| File Pattern | Risk |
|--------------|------|
| `*.pem` | Private keys |
| `*.key` | Private keys |
| `*.p12` | PKCS#12 certificates |
| `*.pfx` | Windows certificates |
| `*.jks` | Java keystores |
| `id_rsa*` | SSH private keys |
| `*.ppk` | PuTTY keys |

### Cloud Provider Files

| File Pattern | Risk |
|--------------|------|
| `credentials` | AWS credentials |
| `*.tfstate` | Terraform state (may contain secrets) |
| `kubeconfig` | Kubernetes access |
| `service-account.json` | GCP service accounts |

### IDE and Tool Files

| File Pattern | Risk |
|--------------|------|
| `.idea/` | May contain tokens |
| `.vscode/settings.json` | May contain tokens |
| `*.code-workspace` | May contain paths/tokens |

## Sensitive Patterns to Detect

### API Keys

```regex
# AWS
AKIA[0-9A-Z]{16}

# Google
AIza[0-9A-Za-z\-_]{35}

# GitHub
gh[pousr]_[A-Za-z0-9_]{36,255}

# Stripe
sk_live_[A-Za-z0-9]{24,}
rk_live_[A-Za-z0-9]{24,}

# Generic patterns
[aA][pP][iI][_-]?[kK][eE][yY].*['\"][A-Za-z0-9]{16,}['\"]
```

### Secrets and Passwords

```regex
# Password assignments
password\s*[:=]\s*['\"][^'\"]+['\"]
passwd\s*[:=]\s*['\"][^'\"]+['\"]
pwd\s*[:=]\s*['\"][^'\"]+['\"]

# Secret assignments
secret\s*[:=]\s*['\"][^'\"]+['\"]
api_secret\s*[:=]\s*['\"][^'\"]+['\"]
```

### Tokens

```regex
# JWT tokens
eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+

# Bearer tokens
[Bb]earer\s+[A-Za-z0-9\-_]+

# OAuth tokens
access_token\s*[:=]\s*['\"][^'\"]+['\"]
refresh_token\s*[:=]\s*['\"][^'\"]+['\"]
```

### Private Keys

```regex
-----BEGIN (RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----
-----BEGIN PGP PRIVATE KEY BLOCK-----
```

### Database URLs

```regex
# PostgreSQL
postgres(ql)?://[^:]+:[^@]+@

# MySQL
mysql://[^:]+:[^@]+@

# MongoDB
mongodb(\+srv)?://[^:]+:[^@]+@

# Redis
redis://:[^@]+@
```

## Pre-Commit Verification Script

```bash
#!/bin/bash
# save as .git/hooks/pre-commit

echo "Running security check..."

# Patterns to check
PATTERNS=(
  "password\s*[:=]"
  "api[_-]?key\s*[:=]"
  "secret\s*[:=]"
  "token\s*[:=]"
  "AKIA[0-9A-Z]{16}"
  "-----BEGIN.*PRIVATE KEY-----"
  "sk_live_"
  "rk_live_"
)

# Files to block
BLOCKED_FILES=(
  "\.env$"
  "\.env\."
  "\.pem$"
  "\.key$"
  "id_rsa"
  "credentials$"
)

# Check staged files
STAGED=$(git diff --cached --name-only)

# Check for blocked files
for pattern in "${BLOCKED_FILES[@]}"; do
  if echo "$STAGED" | grep -qE "$pattern"; then
    echo "ERROR: Attempting to commit sensitive file matching: $pattern"
    exit 1
  fi
done

# Check content for secrets
for pattern in "${PATTERNS[@]}"; do
  if git diff --cached | grep -qiE "$pattern"; then
    echo "WARNING: Potential secret detected matching: $pattern"
    echo "Please review staged changes carefully."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
done

echo "Security check passed."
exit 0
```

## Recommended .gitignore

```gitignore
# Environment files
.env
.env.*
!.env.example
!.env.template

# Credentials
*.pem
*.key
*.p12
*.pfx
*.jks
id_rsa*
*.ppk

# Cloud credentials
credentials
.aws/
.gcloud/
kubeconfig
**/terraform.tfstate
**/terraform.tfstate.*
**/.terraform/

# IDE settings that may contain tokens
.idea/
.vscode/settings.json
*.code-workspace

# Logs that may contain sensitive info
*.log
logs/

# Local config
config.local.*
secrets.*
```

## Tools for Secret Detection

### git-secrets (AWS)

```bash
# Install
brew install git-secrets

# Setup
git secrets --install
git secrets --register-aws

# Scan
git secrets --scan
```

### gitleaks

```bash
# Install
brew install gitleaks

# Scan repository
gitleaks detect

# Scan staged changes
gitleaks protect --staged
```

### truffleHog

```bash
# Install
pip install truffleHog

# Scan
trufflehog git file://./
```

## If Secrets Are Committed

### Immediate Actions

1. **Revoke the secret immediately**
   - Generate new API key/password
   - Update all systems using it

2. **Remove from history** (if not pushed)
   ```bash
   git reset --soft HEAD~1
   # Remove secret from files
   git add .
   git commit -m "chore: remove sensitive data"
   ```

3. **If already pushed** - Consider it compromised
   - Rotate credentials first
   - Then clean history with BFG or git filter-branch
   - Force push (coordinate with team)

### Using BFG Repo-Cleaner

```bash
# Install BFG
brew install bfg

# Remove file from history
bfg --delete-files .env

# Remove secrets by pattern
bfg --replace-text patterns.txt

# Clean and force push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

## Security Mindset

### Before Every Commit

1. Review staged changes: `git diff --cached`
2. Check file names: `git diff --cached --name-only`
3. Run security scan if available
4. Ask: "Would I want this public?"

### Environment Best Practices

1. Use `.env.example` with placeholder values
2. Document required environment variables
3. Use secret management tools (Vault, AWS Secrets Manager)
4. Rotate credentials regularly

### Code Review Checklist

- [ ] No hardcoded credentials
- [ ] No API keys in source
- [ ] No private keys included
- [ ] Environment variables used for config
- [ ] Logging doesn't expose secrets
- [ ] Error messages don't leak secrets
