# 1Password CLI Command Reference

Complete reference for all `op` CLI commands and their options.

## Authentication Commands

### op signin

Sign in to a 1Password account.

```bash
op signin [account-shorthand]
op signin --raw                    # Output session token only
op signin --force                  # Force re-authentication
```

### op signout

Sign out of a 1Password account.

```bash
op signout                         # Sign out of current account
op signout --all                   # Sign out of all accounts
op signout --forget                # Remove account from local config
```

### op whoami

Display information about the signed-in account.

```bash
op whoami                          # Show account info
op whoami --format json            # JSON output
```

## Secret Operations

### op read

Read a secret using a secret reference.

```bash
op read "op://vault/item/field"
op read "op://vault/item/field" --no-newline    # No trailing newline
op read "op://vault/item/field" --force         # Skip confirmation prompts
```

### op run

Run a command with secrets injected as environment variables.

```bash
op run -- command [args]
op run --env-file .env.tpl -- command
op run --no-masking -- command      # Don't mask secrets in output
```

### op inject

Inject secrets into a template file.

```bash
op inject -i template.env -o output.env
op inject -i template.yaml          # Output to stdout
op inject --in-file template --out-file output
op inject --force                   # Overwrite existing output
```

## Item Commands

### op item list

List items in vaults.

```bash
op item list
op item list --vault "Vault Name"
op item list --categories login,password
op item list --tags "production,api"
op item list --format json
op item list --favorite              # Only favorites
op item list --include-archive       # Include archived items
```

### op item get

Get details of a specific item.

```bash
op item get "Item Name"
op item get "Item Name" --vault "Vault Name"
op item get "Item Name" --fields label=password
op item get "Item Name" --fields password,username
op item get "Item Name" --format json
op item get "Item Name" --reveal     # Show concealed fields
op item get itemid                   # By ID (more reliable)
```

### op item create

Create a new item.

```bash
# Basic login
op item create --category login --title "My Service" \
  --vault "Development" \
  username=admin password=secret

# With generated password
op item create --category login --title "New Account" \
  --generate-password

# With specific password recipe
op item create --category login --title "Secure Service" \
  --generate-password="letters,digits,symbols,32"

# From template file
op item create --template item.json

# Categories: login, password, identity, credit_card, secure_note,
#            document, bank_account, database, email_account,
#            wireless_router, server, software_license, api_credential
```

### op item edit

Edit an existing item.

```bash
op item edit "Item Name" field=newvalue
op item edit "Item Name" --vault "Vault" password=newsecret
op item edit "Item Name" "section.field=value"
op item edit "Item Name" --title "New Title"
op item edit "Item Name" --generate-password
op item edit "Item Name" --favorite
op item edit "Item Name" --tags "tag1,tag2"
```

### op item delete

Delete an item.

```bash
op item delete "Item Name"
op item delete "Item Name" --vault "Vault"
op item delete "Item Name" --archive    # Archive instead of delete
```

### op item share

Share an item.

```bash
op item share "Item Name"                       # Generate share link
op item share "Item Name" --expiry 1h           # 1 hour expiry
op item share "Item Name" --expiry 7d           # 7 days expiry
op item share "Item Name" --view-once           # Single view only
op item share "Item Name" --emails user@example.com
```

### op item move

Move an item between vaults.

```bash
op item move "Item Name" --current-vault "Source" --destination-vault "Dest"
```

## Vault Commands

### op vault list

List accessible vaults.

```bash
op vault list
op vault list --format json
op vault list --group "Group Name"
```

### op vault get

Get details of a vault.

```bash
op vault get "Vault Name"
op vault get "Vault Name" --format json
```

### op vault create

Create a new vault.

```bash
op vault create "New Vault"
op vault create "New Vault" --description "Description"
op vault create "New Vault" --icon "airplane"
op vault create "New Vault" --allow-admins-to-manage false
```

### op vault edit

Edit a vault.

```bash
op vault edit "Vault Name" --name "New Name"
op vault edit "Vault Name" --description "New description"
op vault edit "Vault Name" --icon "key"
```

### op vault delete

Delete a vault.

```bash
op vault delete "Vault Name"
```

## Document Commands

### op document list

List documents.

```bash
op document list
op document list --vault "Vault Name"
op document list --format json
```

### op document get

Download a document.

```bash
op document get "Document Name"              # To stdout
op document get "Document Name" --out-file path/to/file
op document get "Document Name" --vault "Vault"
```

### op document create

Upload a document.

```bash
op document create path/to/file --vault "Vault"
op document create path/to/file --title "Custom Title" --vault "Vault"
op document create path/to/file --tags "tag1,tag2"
```

### op document edit

Replace a document.

```bash
op document edit "Document Name" --vault "Vault" path/to/newfile
op document edit "Document Name" --title "New Title"
```

### op document delete

Delete a document.

```bash
op document delete "Document Name"
op document delete "Document Name" --vault "Vault"
op document delete "Document Name" --archive
```

## Account Management

### op account list

List configured accounts.

```bash
op account list
op account list --format json
```

### op account get

Get account details.

```bash
op account get
op account get --format json
```

### op account add

Add an account.

```bash
op account add --address example.1password.com
op account add --address example.1password.com --email user@example.com
```

### op account forget

Remove an account from local configuration.

```bash
op account forget example
```

## Service Account Commands

### op service-account create

Create a service account.

```bash
# Read-only access
op service-account create "CI Pipeline" \
  --vault Production:read_items

# Read and write access
op service-account create "Deploy Bot" \
  --vault Production:read_items,write_items \
  --vault Staging:read_items,write_items

# With vault creation permission
op service-account create "Provisioner" \
  --vault Production:read_items,write_items \
  --can-create-vaults

# Permissions: read_items, write_items, share_items
```

### op service-account ratelimit

Check service account rate limits.

```bash
op service-account ratelimit
```

## User Commands

### op user list

List users in account.

```bash
op user list
op user list --group "Group Name"
op user list --vault "Vault Name"
op user list --format json
```

### op user get

Get user details.

```bash
op user get user@example.com
op user get --me
```

### op user provision

Provision a new user.

```bash
op user provision --email user@example.com --name "User Name"
```

### op user edit

Edit a user.

```bash
op user edit user@example.com --name "New Name"
op user edit user@example.com --travel-mode on
```

### op user delete

Delete/suspend a user.

```bash
op user delete user@example.com
op user suspend user@example.com
```

## Group Commands

### op group list

List groups.

```bash
op group list
op group list --vault "Vault Name"
op group list --format json
```

### op group get

Get group details.

```bash
op group get "Group Name"
op group get "Group Name" --format json
```

### op group create

Create a group.

```bash
op group create "New Group"
op group create "New Group" --description "Description"
```

### op group edit

Edit a group.

```bash
op group edit "Group Name" --name "New Name"
op group edit "Group Name" --description "New description"
```

### op group delete

Delete a group.

```bash
op group delete "Group Name"
```

### op group user

Manage group membership.

```bash
op group user grant --group "Group" --user user@example.com
op group user revoke --group "Group" --user user@example.com
op group user list --group "Group"
```

## Connect Server Commands

### op connect server list

List Connect servers.

```bash
op connect server list
```

### op connect server get

Get Connect server details.

```bash
op connect server get "Server Name"
```

### op connect server create

Create a Connect server.

```bash
op connect server create "Server Name" --vault "Vault1" --vault "Vault2"
```

### op connect server edit

Edit a Connect server.

```bash
op connect server edit "Server Name" --name "New Name"
```

### op connect server delete

Delete a Connect server.

```bash
op connect server delete "Server Name"
```

### op connect token create

Create a Connect token.

```bash
op connect token create "Token Name" --server "Server Name" --vault "Vault"
```

### op connect token list

List Connect tokens.

```bash
op connect token list --server "Server Name"
```

### op connect token delete

Delete a Connect token.

```bash
op connect token delete "Token Name" --server "Server Name"
```

## Shell Plugin Commands

### op plugin list

List available plugins.

```bash
op plugin list
```

### op plugin init

Initialize a plugin.

```bash
op plugin init aws
op plugin init gh
op plugin init stripe
```

### op plugin run

Run a command with plugin credentials.

```bash
op plugin run -- aws s3 ls
```

## Utility Commands

### op completion

Generate shell completion scripts.

```bash
op completion bash
op completion zsh
op completion fish
op completion powershell
```

### op update

Check for and apply updates.

```bash
op update
op update --check        # Check only, don't install
```

### op --version

Display version information.

```bash
op --version
```

## Global Flags

These flags work with most commands:

```bash
--account         # Specify account shorthand
--cache           # Enable/disable caching
--config          # Config directory path
--debug           # Enable debug output
--encoding        # Output encoding (utf-8, shift_jis)
--format          # Output format (json, human-readable)
--iso-timestamps  # Use ISO 8601 timestamps
--no-color        # Disable color output
--session         # Session token to use
```

## Environment Variables

```bash
OP_SERVICE_ACCOUNT_TOKEN    # Service account authentication
OP_CONNECT_TOKEN            # Connect server token
OP_CONNECT_HOST             # Connect server URL
OP_SESSION_*                # Session tokens per account
OP_BIOMETRIC_UNLOCK_ENABLED # Enable biometric unlock
OP_DEVICE                   # Device UUID
OP_CONFIG_DIR               # Config directory location
OP_CACHE_DIR                # Cache directory location
OP_LOG_LEVEL                # Logging level (debug, info, warn, error)
```

## Secret Reference Format

The canonical format for referencing secrets:

```
op://<vault>/<item>[/<section>]/<field>
```

Components:

- `vault` - Vault name or ID
- `item` - Item name or ID
- `section` - Optional section name
- `field` - Field label or ID

Examples:

```
op://Development/AWS/access_key_id
op://Production/Database/credentials/password
op://Shared/API Keys/github_token
op://vault-uuid/item-uuid/field-uuid
```

## Item Categories

Available categories for `op item create --category`:

| Category | Description |
|----------|-------------|
| `login` | Website login credentials |
| `password` | Standalone password |
| `identity` | Personal identity information |
| `credit_card` | Credit/debit card |
| `secure_note` | Encrypted text note |
| `document` | File attachment |
| `bank_account` | Bank account details |
| `database` | Database connection |
| `email_account` | Email credentials |
| `wireless_router` | WiFi credentials |
| `server` | Server/SSH credentials |
| `software_license` | License keys |
| `api_credential` | API key/token |
| `ssh_key` | SSH key pair |
| `medical_record` | Medical information |
| `passport` | Passport details |
| `driver_license` | Driver's license |
| `outdoor_license` | Hunting/fishing license |
| `membership` | Membership card |
| `reward_program` | Loyalty program |
| `social_security_number` | SSN |

## Field Types

Available field types when creating items:

| Type | Description |
|------|-------------|
| `STRING` | Plain text |
| `CONCEALED` | Hidden/password field |
| `EMAIL` | Email address |
| `URL` | Web URL |
| `DATE` | Date value |
| `MONTH_YEAR` | Month/year (cards) |
| `PHONE` | Phone number |
| `ADDRESS` | Physical address |
| `TOTP` | One-time password seed |
| `REFERENCE` | Reference to another item |
| `FILE` | File attachment |
