# Atuin Sync Setup Guide

Complete guide for setting up history synchronization across machines.

## Overview

Atuin sync provides:
- End-to-end encrypted history synchronization
- Cross-machine history access
- Automatic background sync
- Self-hosting option for privacy

## Quick Setup (Cloud Sync)

### Step 1: Register Account

```bash
# Create account
atuin register -u <USERNAME> -e <EMAIL>

# You'll be prompted for a password
# Email is used for account recovery only
```

### Step 2: Import Existing History

```bash
# Auto-detect and import
atuin import auto

# Check import results
atuin stats
```

### Step 3: Sync

```bash
# Initial sync (uploads history)
atuin sync

# Verify sync status
atuin status
```

### Step 4: Setup on Additional Machines

```bash
# Install Atuin (same as first machine)
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# Add shell integration
echo 'eval "$(atuin init zsh)"' >> ~/.zshrc
source ~/.zshrc

# Login to existing account
atuin login -u <USERNAME>

# You'll be prompted for password

# Sync to download history
atuin sync

# Now history is shared!
```

## Encryption Key Management

### How It Works

1. Encryption key generated on first registration
2. Key stored locally at `~/.local/share/atuin/key`
3. All history encrypted before leaving your machine
4. Server cannot read your history

### Key Backup (CRITICAL)

```bash
# Backup key file
cp ~/.local/share/atuin/key ~/atuin-key-backup.txt

# Store securely (password manager, encrypted drive, etc.)

# The key looks like:
# aGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3QgYmFzZTY0
```

### Restoring Key on New Machine

```bash
# Before login, restore key
mkdir -p ~/.local/share/atuin
cp ~/atuin-key-backup.txt ~/.local/share/atuin/key

# Then login
atuin login -u <USERNAME>

# Sync will now work with your existing history
```

### Key Lost?

If you lose your key:
- Existing synced history cannot be recovered
- You must delete account and re-register
- Start with fresh sync

```bash
# Delete account (if key lost)
atuin account delete

# Re-register
atuin register -u <USERNAME> -e <EMAIL>

# Import local history again
atuin import auto
atuin sync
```

## Sync Configuration

### Basic Settings

```toml
# ~/.config/atuin/config.toml

# Sync server (default: Atuin cloud)
sync_address = "https://api.atuin.sh"

# Enable automatic sync
auto_sync = true

# Sync frequency (human-readable)
sync_frequency = "1h"
# Options: 10s, 5m, 1h, 4h, 1d
```

### Sync v2 Protocol (Recommended)

```toml
# ~/.config/atuin/config.toml

[sync]
records = true  # Enable sync v2

# Benefits:
# - Faster sync
# - More efficient data transfer
# - Better conflict resolution
```

### Network Tuning

```toml
# ~/.config/atuin/config.toml

# Request timeout (seconds)
network_timeout = 30

# Connection timeout (seconds)
network_connect_timeout = 5
```

## Daemon Mode (Continuous Sync)

### Enable Daemon

```toml
# ~/.config/atuin/config.toml

[daemon]
enabled = true
sync_frequency = 300  # seconds (5 minutes)
```

### Manual Daemon Control

```bash
# Start daemon
atuin daemon

# Check status
atuin daemon status

# Run in foreground (for debugging)
atuin daemon --foreground
```

### Systemd Service (Linux)

```bash
# Create service file
cat > ~/.config/systemd/user/atuin-daemon.service << 'EOF'
[Unit]
Description=Atuin Daemon
After=network.target

[Service]
ExecStart=/usr/bin/atuin daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable atuin-daemon
systemctl --user start atuin-daemon

# Check status
systemctl --user status atuin-daemon
```

### launchd Service (macOS)

```bash
# Create plist
cat > ~/Library/LaunchAgents/sh.atuin.daemon.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>sh.atuin.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/atuin</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/atuin-daemon.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/atuin-daemon.error.log</string>
</dict>
</plist>
EOF

# Load service
launchctl load ~/Library/LaunchAgents/sh.atuin.daemon.plist

# Check status
launchctl list | grep atuin
```

## Self-Hosted Server

### Docker Deployment

```bash
# Create data directory
mkdir -p ~/.atuin-server

# Run server
docker run -d \
  --name atuin-server \
  -p 8888:8888 \
  -v ~/.atuin-server:/data \
  -e ATUIN_HOST=0.0.0.0 \
  -e ATUIN_PORT=8888 \
  -e ATUIN_OPEN_REGISTRATION=true \
  -e ATUIN_DB_URI=sqlite:///data/atuin.db \
  ghcr.io/atuinsh/atuin:latest \
  server start

# Check logs
docker logs atuin-server
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3'
services:
  atuin:
    image: ghcr.io/atuinsh/atuin:latest
    command: server start
    ports:
      - "8888:8888"
    volumes:
      - ./data:/data
    environment:
      ATUIN_HOST: "0.0.0.0"
      ATUIN_PORT: "8888"
      ATUIN_OPEN_REGISTRATION: "true"
      ATUIN_DB_URI: "sqlite:///data/atuin.db"
    restart: unless-stopped
```

### PostgreSQL Backend (Production)

```yaml
# docker-compose.yml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: atuin
      POSTGRES_PASSWORD: secretpassword
      POSTGRES_DB: atuin
    volumes:
      - postgres_data:/var/lib/postgresql/data

  atuin:
    image: ghcr.io/atuinsh/atuin:latest
    command: server start
    depends_on:
      - postgres
    ports:
      - "8888:8888"
    environment:
      ATUIN_HOST: "0.0.0.0"
      ATUIN_PORT: "8888"
      ATUIN_OPEN_REGISTRATION: "true"
      ATUIN_DB_URI: "postgresql://atuin:secretpassword@postgres/atuin"
    restart: unless-stopped

volumes:
  postgres_data:
```

### Server Configuration

```bash
# Environment variables for server
ATUIN_HOST=0.0.0.0          # Listen address
ATUIN_PORT=8888             # Listen port
ATUIN_OPEN_REGISTRATION=true # Allow new users
ATUIN_DB_URI=sqlite:///data/atuin.db  # Database URI
ATUIN_MAX_HISTORY_LENGTH=8192  # Max command length
ATUIN_PAGE_SIZE=1000        # Pagination size
```

### Client Configuration for Self-Hosted

```toml
# ~/.config/atuin/config.toml

# Point to your server
sync_address = "https://atuin.yourdomain.com"
# Or for local: sync_address = "http://localhost:8888"
```

### HTTPS with Reverse Proxy

```nginx
# /etc/nginx/sites-available/atuin
server {
    listen 443 ssl http2;
    server_name atuin.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Sync Troubleshooting

### Check Sync Status

```bash
# Detailed status
atuin status

# Should show:
# - Username
# - Last sync time
# - Record counts
# - Any errors
```

### Force Full Resync

```bash
# Force re-upload/download
atuin sync --force
```

### Debug Sync

```bash
# Enable debug logging
ATUIN_LOG=debug atuin sync

# Check for errors in output
```

### Network Issues

```bash
# Test connectivity
curl https://api.atuin.sh/healthz

# Or for self-hosted:
curl http://localhost:8888/healthz

# Increase timeouts if slow network
# In config.toml:
# network_timeout = 60
# network_connect_timeout = 10
```

### Reset Sync State

```bash
# Logout
atuin logout

# Clear local session
rm ~/.local/share/atuin/session

# Login again
atuin login -u <USERNAME>

# Resync
atuin sync --force
```

### Conflict Resolution

Sync v2 handles conflicts automatically:
- Newer timestamps win
- Both machines' history preserved
- No data loss

If issues persist:
```bash
# Export local history
atuin history list --cmd-only > history-backup.txt

# Clear and reimport
rm ~/.local/share/atuin/history.db
atuin import auto
atuin sync
```

## Offline Mode

### Disable Sync Entirely

```toml
# ~/.config/atuin/config.toml

auto_sync = false
# Leave sync_address empty or remove it
```

### Temporary Offline

Atuin works fully offline:
- History stored locally
- Search works without network
- Sync when reconnected

## Security Considerations

### What's Encrypted

- Command text
- Working directory
- Hostname
- Session ID
- Timestamp
- Duration
- Exit code

### What Server Sees

- Encrypted blobs
- Account email/username
- Sync timestamps
- Record counts

### Best Practices

1. **Backup your key** - Essential for recovery
2. **Use strong password** - Protects account access
3. **Self-host for sensitive work** - Full control
4. **Use secrets_filter** - Prevent sensitive data in history

```toml
# Enable built-in secrets filtering
secrets_filter = true

# Add custom filters
history_filter = [
  ".*password.*",
  ".*secret.*",
  ".*API_KEY.*"
]
```
