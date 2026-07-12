---
name: macos-setup
description: |
  macOS development environment setup wizard. Interactive Q&A to collect preferences,
  auto-detect installed software, generate customized installation plan.
  Supports presets: fullstack, frontend, backend, data, devops.
  Triggers: /new-macos-setup, macos setup, dev environment, new mac
---

# macOS Starter - Setup Skill

> From Zero to Hero - AI-powered macOS development environment configuration

## Quick Reference

| Command | Description |
|---------|-------------|
| `/new-macos-setup` | Full interactive setup wizard |
| `/new-macos-setup --quick` | Quick setup with defaults |
| `/new-macos-setup --preset fullstack` | Use fullstack preset |
| `/new-macos-setup --dry-run` | Preview without installing |

---

## Skill Capabilities

### 0. Network Proxy Check (前置步骤)

在开始安装前，必须确保网络可以访问 Google 和 GitHub：

```bash
check_network() {
    echo "=== Network Connectivity Check ==="
    echo ""

    # Test GitHub
    echo "Testing GitHub..."
    if curl -s --connect-timeout 5 https://github.com > /dev/null 2>&1; then
        echo "✅ GitHub: accessible"
    else
        echo "❌ GitHub: not accessible"
        NEED_PROXY=true
    fi

    # Test Google (for some Homebrew dependencies)
    echo "Testing Google..."
    if curl -s --connect-timeout 5 https://www.google.com > /dev/null 2>&1; then
        echo "✅ Google: accessible"
    else
        echo "❌ Google: not accessible"
        NEED_PROXY=true
    fi

    # Test Homebrew
    echo "Testing Homebrew..."
    if curl -s --connect-timeout 5 https://raw.githubusercontent.com > /dev/null 2>&1; then
        echo "✅ Homebrew sources: accessible"
    else
        echo "❌ Homebrew sources: not accessible"
        NEED_PROXY=true
    fi

    if [ "$NEED_PROXY" = true ]; then
        echo ""
        echo "⚠️  Network issues detected. Proxy configuration required."
        return 1
    fi

    echo ""
    echo "✅ Network OK - Ready to proceed"
    return 0
}
```

**代理配置流程:**

1. **询问用户代理信息:**
```yaml
questions:
  - id: proxy_needed
    question: "Do you need to configure a network proxy to access GitHub/Google?"
    options:
      - label: "Yes, I have a proxy"
        description: "Configure HTTP/HTTPS proxy"
      - label: "No, direct connection works"
        description: "Skip proxy configuration"

  - id: proxy_config
    question: "Please provide your proxy configuration:"
    condition: "proxy_needed == 'Yes'"
    inputs:
      - label: "Proxy URL"
        placeholder: "http://127.0.0.1:7890"
        example: "http://127.0.0.1:7890 or socks5://127.0.0.1:1080"
```

2. **设置临时环境变量:**
```bash
setup_proxy() {
    local proxy_url="$1"

    if [ -n "$proxy_url" ]; then
        echo "Setting proxy: $proxy_url"
        export http_proxy="$proxy_url"
        export https_proxy="$proxy_url"
        export HTTP_PROXY="$proxy_url"
        export HTTPS_PROXY="$proxy_url"
        export ALL_PROXY="$proxy_url"

        # For Git
        git config --global http.proxy "$proxy_url"
        git config --global https.proxy "$proxy_url"

        echo "✅ Proxy configured for this session"
        echo ""
        echo "To make permanent, add to ~/.zshrc:"
        echo "  export http_proxy=\"$proxy_url\""
        echo "  export https_proxy=\"$proxy_url\""
    fi
}
```

3. **验证代理是否工作:**
```bash
verify_proxy() {
    echo "Verifying proxy configuration..."

    if curl -s --connect-timeout 5 https://github.com > /dev/null 2>&1; then
        echo "✅ GitHub accessible via proxy"
    else
        echo "❌ GitHub still not accessible"
        return 1
    fi

    if curl -s --connect-timeout 5 https://www.google.com > /dev/null 2>&1; then
        echo "✅ Google accessible via proxy"
    else
        echo "❌ Google still not accessible"
        return 1
    fi

    echo "✅ Proxy verification passed"
    return 0
}
```

---

### 1. System Detection

Detect installed software and versions:

```bash
# Core tools detection script
detect_installed() {
    echo "=== System Detection ==="

    # Homebrew
    if command -v brew &>/dev/null; then
        echo "✅ Homebrew: $(brew --version | head -1)"
    else
        echo "❌ Homebrew: not installed"
    fi

    # Shell
    echo "✅ Shell: $SHELL"
    [ -d "$HOME/.oh-my-zsh" ] && echo "✅ Oh-My-Zsh: installed"
    command -v starship &>/dev/null && echo "✅ Starship: installed"

    # Git
    command -v git &>/dev/null && echo "✅ Git: $(git --version)"
    command -v gh &>/dev/null && echo "✅ GitHub CLI: installed"
    command -v delta &>/dev/null && echo "✅ Delta: installed"

    # Modern CLI
    command -v eza &>/dev/null && echo "✅ eza: installed"
    command -v bat &>/dev/null && echo "✅ bat: installed"
    command -v fd &>/dev/null && echo "✅ fd: installed"
    command -v rg &>/dev/null && echo "✅ ripgrep: installed"

    # Languages
    command -v fnm &>/dev/null && echo "✅ fnm: installed"
    command -v node &>/dev/null && echo "✅ Node.js: $(node --version)"
    command -v pnpm &>/dev/null && echo "✅ pnpm: installed"
    command -v uv &>/dev/null && echo "✅ uv: installed"
    command -v python3 &>/dev/null && echo "✅ Python: $(python3 --version)"
    command -v goenv &>/dev/null && echo "✅ goenv: installed"
    command -v go &>/dev/null && echo "✅ Go: $(go version)"

    # Container
    command -v docker &>/dev/null && echo "✅ Docker: installed"
    command -v kubectl &>/dev/null && echo "✅ kubectl: installed"
    command -v helm &>/dev/null && echo "✅ Helm: installed"
    command -v k9s &>/dev/null && echo "✅ k9s: installed"

    # Applications
    [ -d "/Applications/Raycast.app" ] && echo "✅ Raycast: installed"
    [ -d "/Applications/Warp.app" ] && echo "✅ Warp: installed"
    [ -d "/Applications/Visual Studio Code.app" ] && echo "✅ VS Code: installed"
    [ -d "/Applications/OrbStack.app" ] && echo "✅ OrbStack: installed"

    # Vibe Coding Tools
    echo ""
    echo "--- Vibe Coding Tools ---"
    command -v claude &>/dev/null && echo "✅ Claude Code: $(claude --version 2>/dev/null | head -1 || echo 'installed')" || echo "❌ Claude Code"
    command -v ccline &>/dev/null && echo "✅ CCometixLine: installed" || echo "❌ CCometixLine"
    [ -d "/Applications/Cursor.app" ] && echo "✅ Cursor: installed" || echo "❌ Cursor"
    command -v opencode &>/dev/null && echo "✅ OpenCode: installed" || echo "❌ OpenCode"
    [ -d "/Applications/Cherry Studio.app" ] && echo "✅ Cherry Studio: installed" || echo "❌ Cherry Studio"
    [ -d "/Applications/LM Studio.app" ] && echo "✅ LM Studio: installed" || echo "❌ LM Studio"
}
```

### 2. Interactive Q&A Flow

Use `AskUserQuestion` tool with structured questions:

```yaml
questions:
  - id: role
    question: "What best describes your primary development role?"
    options:
      - label: "Fullstack Developer"
        description: "React/Vue + Node.js + Database"
      - label: "Frontend Developer"
        description: "React/Vue/Svelte + UI/Design tools"
      - label: "Backend Developer"
        description: "Go/Python/Java + APIs + Infrastructure"
      - label: "Data/ML Engineer"
        description: "Python + Jupyter + ML frameworks"
      - label: "DevOps/Platform"
        description: "K8s + Terraform + CI/CD"

  - id: languages
    question: "Which programming languages do you need?"
    multiSelect: true
    options:
      - label: "JavaScript/TypeScript"
        description: "fnm + Node.js LTS + pnpm"
      - label: "Python"
        description: "uv + Python 3.12"
      - label: "Go"
        description: "goenv + latest Go"
      - label: "Rust"
        description: "rustup + stable"

  - id: containers
    question: "Do you need container and Kubernetes tools?"
    options:
      - label: "Full K8s setup"
        description: "OrbStack + kubectl + helm + k9s + stern"
      - label: "Docker only"
        description: "OrbStack for containers"
      - label: "Skip"
        description: "No container tools"

  - id: vibe_coding
    question: "Which additional Vibe Coding tools do you need?"
    multiSelect: true
    note: "We assume you already have at least one AI coding tool installed to use this project."
    detection: |
      command -v claude &>/dev/null && echo "✅ Claude Code installed"
      command -v ccline &>/dev/null && echo "✅ CCometixLine installed"
      [ -d "/Applications/Cursor.app" ] && echo "✅ Cursor installed"
      command -v opencode &>/dev/null && echo "✅ OpenCode installed"
      [ -d "/Applications/Cherry Studio.app" ] && echo "✅ Cherry Studio installed"
    options:
      - label: "Claude Code"
        description: "Anthropic's official agentic CLI"
        skip_if: "command -v claude &>/dev/null"
      - label: "CCometixLine"
        description: "Claude Code statusline enhancer (Git, model, context)"
        skip_if: "command -v ccline &>/dev/null"
        requires: "Node.js"
      - label: "Cursor"
        description: "AI-first code editor"
        skip_if: "[ -d '/Applications/Cursor.app' ]"
      - label: "OpenCode"
        description: "Open-source terminal AI assistant"
        skip_if: "command -v opencode &>/dev/null"
      - label: "Cherry Studio"
        description: "AI desktop client with multi-model support"
        skip_if: "[ -d '/Applications/Cherry Studio.app' ]"

  - id: apps
    question: "Which collaboration apps?"
    multiSelect: true
    options:
      - label: "Work (CN)"
        description: "Lark + DingTalk + WeCom"
      - label: "International"
        description: "Slack + Discord + WhatsApp"
      - label: "Meetings"
        description: "Tencent Meeting + Zoom"

  - id: macos
    question: "macOS optimizations?"
    multiSelect: true
    options:
      - label: "Dock"
        description: "Hide recent apps, faster animations"
      - label: "Keyboard"
        description: "Faster repeat, disable auto-correct"
      - label: "Finder"
        description: "Show hidden files, path bar"
      - label: "Screenshots"
        description: "Save to ~/Pictures/Screenshots"
```

### 3. Plan Generation

Generate structured installation plan based on answers:

```markdown
## Generated Plan for: [User Name]

### Phase 1: Prerequisites
- [ ] Xcode Command Line Tools
- [ ] Homebrew

### Phase 2: CLI Tools
| Package | Purpose | Command |
|---------|---------|---------|
| git | Version control | `brew install git` |
| gh | GitHub CLI | `brew install gh` |
| delta | Better diffs | `brew install delta` |
| starship | Modern prompt | `brew install starship` |
| eza | ls replacement | `brew install eza` |
| bat | cat replacement | `brew install bat` |
| fd | find replacement | `brew install fd` |
| ripgrep | grep replacement | `brew install ripgrep` |

### Phase 3: Language Environments
| Language | Manager | Setup Command |
|----------|---------|---------------|
| Node.js | fnm | `fnm install --lts && fnm default lts-latest` |
| Python | uv | `uv python install 3.12` |
| Go | goenv | `goenv install latest && goenv global latest` |

### Phase 4: Applications
| App | Purpose | Command |
|-----|---------|---------|
| Raycast | Launcher + window mgmt | `brew install --cask raycast` |
| Warp | Modern terminal | `brew install --cask warp` |
| OrbStack | Docker/K8s | `brew install --cask orbstack` |

### Phase 5: Vibe Coding Tools
> Note: Skip already installed tools

| Tool | Purpose | Command | Skip If |
|------|---------|---------|---------|
| Claude Code | Anthropic agentic CLI | `brew install --cask claude-code` | `command -v claude` |
| CCometixLine | Claude Code statusline | `npm install -g @cometix/ccline` | `command -v ccline` |
| Cursor | AI-first code editor | `brew install --cask cursor` | App exists |
| OpenCode | Open-source terminal AI | `brew install opencode` | `command -v opencode` |
| Cherry Studio | Multi-model AI client | `brew install --cask cherry-studio` | App exists |

### Phase 6: Fonts
| Font | Purpose |
|------|---------|
| JetBrains Mono Nerd Font | Terminal icons |
| Fira Code | Ligatures |
| Inter | UI font |

### Phase 7: Shell Configuration
- [ ] Zsh plugins (autosuggestions, syntax-highlighting)
- [ ] Starship prompt
- [ ] Modern CLI aliases

### Phase 8: macOS Defaults
- [ ] Dock optimization
- [ ] Keyboard settings
- [ ] Finder preferences
```

### 4. Execution Engine

Execute plan with progress tracking:

```bash
# Example execution with progress
execute_phase() {
    local phase=$1
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Phase $phase"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Phase 1: CLI Tools
execute_phase "1: CLI Tools"
brew install git gh delta starship
brew install eza bat fd ripgrep sd dust procs bottom
brew install tree wget curl jq yq

# Phase 2: Languages
execute_phase "2: Language Environments"
brew install fnm uv goenv go
fnm install --lts
fnm default lts-latest
npm install -g pnpm

# Phase 3: Apps
execute_phase "3: Applications"
brew install --cask raycast warp orbstack

# Phase 4: Vibe Coding (with skip detection)
execute_phase "4: Vibe Coding Tools"

# Claude Code
if ! command -v claude &>/dev/null; then
    echo "📦 Installing Claude Code..."
    brew install --cask claude-code
else
    echo "⏭️  Claude Code already installed, skipping"
fi

# CCometixLine (requires Node.js)
if ! command -v ccline &>/dev/null; then
    if command -v npm &>/dev/null; then
        echo "📦 Installing CCometixLine..."
        npm install -g @cometix/ccline
        echo "💡 Configure: Add to ~/.claude/settings.json:"
        echo '   {"statusLine": {"type": "command", "command": "ccline"}}'
    else
        echo "⚠️  CCometixLine requires Node.js, install fnm/node first"
    fi
else
    echo "⏭️  CCometixLine already installed, skipping"
fi

# Cursor
if [ ! -d "/Applications/Cursor.app" ]; then
    echo "📦 Installing Cursor..."
    brew install --cask cursor
else
    echo "⏭️  Cursor already installed, skipping"
fi

# OpenCode
if ! command -v opencode &>/dev/null; then
    echo "📦 Installing OpenCode..."
    brew install opencode
else
    echo "⏭️  OpenCode already installed, skipping"
fi

# Cherry Studio
if [ ! -d "/Applications/Cherry Studio.app" ]; then
    echo "📦 Installing Cherry Studio..."
    brew install --cask cherry-studio
else
    echo "⏭️  Cherry Studio already installed, skipping"
fi

# Phase 5: Fonts
execute_phase "5: Fonts"
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code font-inter

# Phase 6: Shell
execute_phase "6: Shell Configuration"
# Install zsh plugins...
# Configure starship...

# Phase 7: macOS
execute_phase "7: macOS Optimization"
defaults write com.apple.dock show-recents -bool false
defaults write NSGlobalDomain KeyRepeat -int 2
# ...

echo "✅ Setup complete!"
```

---

## Presets

### fullstack
```yaml
name: Fullstack Developer
languages: [javascript, python]
containers: full
apps: [raycast, warp, cursor, orbstack, notion]
macos: [dock, keyboard]
```

### frontend
```yaml
name: Frontend Developer
languages: [javascript]
containers: docker
apps: [raycast, cursor, figma]
macos: [dock, keyboard]
```

### backend
```yaml
name: Backend Developer
languages: [go, python]
containers: full
cloud: [aws]
apps: [raycast, warp, cursor, orbstack]
macos: [dock, keyboard, finder]
```

### data
```yaml
name: Data/ML Engineer
languages: [python]
containers: docker
apps: [cursor, jupyter]
macos: [keyboard]
```

### devops
```yaml
name: DevOps Engineer
languages: [go, python]
containers: full
cloud: [aws, gcp]
apps: [raycast, warp, orbstack]
macos: [dock, keyboard, finder]
```

---

## Configuration Files

This skill references:
- `presets.md` - Detailed preset configurations
- `packages.md` - Complete package registry
- `../../scripts/Brewfile` - Homebrew bundle
- `../../configs/` - Configuration templates

---

## Best Practices

1. **Always detect first** - Never reinstall what exists
2. **Ask, don't assume** - User preferences matter
3. **Show before doing** - Display plan before execution
4. **Progress tracking** - Use TodoWrite for visibility
5. **Verify after** - Confirm installations succeeded
6. **Non-destructive** - Never remove existing tools

---

## Error Handling

```bash
# Retry failed installations
retry_install() {
    local cmd=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if eval "$cmd"; then
            return 0
        fi
        echo "⚠️  Attempt $attempt failed, retrying..."
        ((attempt++))
        sleep 2
    done

    echo "❌ Failed after $max_attempts attempts"
    return 1
}
```

---

## Trigger Keywords

This skill activates on:
- `/new-macos-setup`
- "setup macos"
- "configure mac"
- "new mac setup"
- "dev environment"
- "install development tools"

---

## Gotchas

- **Brewfile on Apple Silicon**: many casks have x86-only fallbacks — check architecture before bulk install, otherwise Rosetta-only apps land on M-series.
- **`defaults write` changes don't always take effect immediately** — some need `cfprefsd flush` or app restart; an apparently-applied setting may not stick.
- **Xcode CLI tools install separately from Xcode.app** — `xcode-select` switches between but doesn't install; new machines need explicit `xcode-select --install`.
- **`com.apple.quarantine` xattr blocks unsigned binaries** — `xattr -d` removes but Gatekeeper may re-add on next download.
- **SIP (System Integrity Protection) is per-volume** — disabling on recovery affects the boot drive only; external drives have their own SIP state.
- **macOS Sequoia+ `sudo` no longer caches credentials by default** — scripts that assumed credential cache silently re-prompt or fail in unattended runs.
