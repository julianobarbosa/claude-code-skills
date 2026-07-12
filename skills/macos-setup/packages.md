# Package Registry

> Complete catalog of installable packages, categorized by purpose

## CLI Tools

### Version Control
| Package | Description | Command | Replaces |
|---------|-------------|---------|----------|
| git | Version control | `brew install git` | - |
| gh | GitHub CLI | `brew install gh` | hub |
| delta | Better git diff | `brew install delta` | diff |

### Shell & Prompt
| Package | Description | Command | Replaces |
|---------|-------------|---------|----------|
| zsh | Modern shell | Pre-installed on macOS | bash |
| starship | Cross-shell prompt | `brew install starship` | oh-my-zsh themes |

### Modern CLI Replacements
| Package | Description | Command | Replaces |
|---------|-------------|---------|----------|
| eza | Modern ls | `brew install eza` | ls |
| bat | Cat with syntax highlighting | `brew install bat` | cat |
| fd | Fast file finder | `brew install fd` | find |
| ripgrep | Fast grep | `brew install ripgrep` | grep |
| sd | Intuitive sed | `brew install sd` | sed |
| dust | Intuitive du | `brew install dust` | du |
| procs | Modern ps | `brew install procs` | ps |
| bottom | System monitor | `brew install bottom` | top/htop |

### File & Data Tools
| Package | Description | Command |
|---------|-------------|---------|
| tree | Directory tree | `brew install tree` |
| wget | File download | `brew install wget` |
| curl | HTTP client | `brew install curl` |
| jq | JSON processor | `brew install jq` |
| yq | YAML processor | `brew install yq` |

### Code Quality
| Package | Description | Command |
|---------|-------------|---------|
| shellcheck | Shell script linter | `brew install shellcheck` |
| golangci-lint | Go linter | `brew install golangci-lint` |

---

## Language Environments

### Node.js
| Package | Description | Command |
|---------|-------------|---------|
| fnm | Fast Node Manager | `brew install fnm` |
| pnpm | Fast package manager | `npm install -g pnpm` |

**Setup:**
```bash
brew install fnm
eval "$(fnm env --use-on-cd)"
fnm install --lts
fnm default lts-latest
npm install -g pnpm
pnpm setup
```

### Python
| Package | Description | Command |
|---------|-------------|---------|
| uv | Fast Python/pip | `brew install uv` |

**Setup:**
```bash
brew install uv
uv python install 3.12
```

### Go
| Package | Description | Command |
|---------|-------------|---------|
| goenv | Go version manager | `brew install goenv` |
| go | Go language | `brew install go` |

**Setup:**
```bash
brew install goenv go
# Add to .zshrc:
# export GOENV_ROOT="$HOME/.goenv"
# export PATH="$GOENV_ROOT/bin:$PATH"
# eval "$(goenv init -)"
# export PATH="$GOPATH/bin:$PATH"
```

### Rust
| Package | Description | Command |
|---------|-------------|---------|
| rustup | Rust toolchain manager | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |

### Java
| Package | Description | Command |
|---------|-------------|---------|
| sdkman | JDK manager | `curl -s "https://get.sdkman.io" \| bash` |

---

## Container & Kubernetes

### Core
| Package | Description | Command |
|---------|-------------|---------|
| kubectl | K8s CLI | `brew install kubectl` |
| helm | K8s package manager | `brew install helm` |
| k9s | K8s TUI | `brew install k9s` |
| stern | Multi-pod log tail | `brew install stern` |

### Context Management
| Package | Description | Command |
|---------|-------------|---------|
| kubeswitch | K8s context switcher | `brew tap danielfoehrkn/switch && brew install switch` |

---

## Cloud CLIs

| Package | Description | Command |
|---------|-------------|---------|
| awscli | AWS CLI | `brew install awscli` |
| google-cloud-sdk | GCP CLI | `brew install google-cloud-sdk` |
| azure-cli | Azure CLI | `brew install azure-cli` |
| rclone | Cloud storage sync | `brew install rclone` |

---

## Applications

### Must Have
| App | Description | Command |
|-----|-------------|---------|
| Raycast | Launcher + window mgmt | `brew install --cask raycast` |
| 1Password | Password manager | `brew install --cask 1password` |
| Google Chrome | Browser | `brew install --cask google-chrome` |
| KeepingYouAwake | Prevent sleep | `brew install --cask keepingyouawake` |
| Keka | Archive utility | `brew install --cask keka` |
| AppCleaner | App uninstaller | `brew install --cask appcleaner` |

### Development
| App | Description | Command |
|-----|-------------|---------|
| Cursor | AI code editor | `brew install --cask cursor` |
| VS Code | Code editor | `brew install --cask visual-studio-code` |
| Warp | Modern terminal | `brew install --cask warp` |
| OrbStack | Docker/K8s | `brew install --cask orbstack` |
| Sourcetree | Git GUI | `brew install --cask sourcetree` |

### Collaboration (CN)
| App | Description | Command |
|-----|-------------|---------|
| Lark | Feishu | `brew install --cask lark` |
| DingTalk | Alibaba work | `brew install --cask dingtalk` |
| WeChat | Personal | `brew install --cask wechat` |
| Tencent Meeting | Video call | `brew install --cask tencent-meeting` |

### Collaboration (International)
| App | Description | Command |
|-----|-------------|---------|
| Discord | Community | `brew install --cask discord` |
| WhatsApp | Messaging | `brew install --cask whatsapp` |
| Notion | Notes/Wiki | `brew install --cask notion` |

### Media
| App | Description | Command |
|-----|-------------|---------|
| IINA | Video player | `brew install --cask iina` |
| ImageOptim | Image compression | `brew install --cask imageoptim` |

### System Enhancement
| App | Description | Command |
|-----|-------------|---------|
| coconutBattery | Battery monitor | `brew install --cask coconutbattery` |
| MonitorControl | External display | `brew install --cask monitorcontrol` |
| Gas Mask | Hosts manager | `brew install --cask gas-mask` |
| balenaEtcher | USB boot disk | `brew install --cask balenaetcher` |

### Quick Look Plugins
| App | Description | Command |
|-----|-------------|---------|
| QLMarkdown | Markdown preview | `brew install --cask qlmarkdown` |
| Syntax Highlight | Code preview | `brew install --cask syntax-highlight` |

### Vibe Coding (AI-Assisted Programming)

> 用户使用本项目时，假设已安装其中至少一个 CLI 工具。安装前会自动检测并跳过已安装的工具。

| App | Description | Command | Detection |
|-----|-------------|---------|-----------|
| Claude Code | Anthropic agentic CLI | `brew install --cask claude-code` | `command -v claude` |
| CCometixLine | Claude Code statusline enhancer | `npm install -g @cometix/ccline` | `command -v ccline` |
| Cursor | AI-first code editor | `brew install --cask cursor` | `[ -d "/Applications/Cursor.app" ]` |
| OpenCode | Open-source terminal AI | `brew install opencode` | `command -v opencode` |
| Cherry Studio | AI desktop client | `brew install --cask cherry-studio` | `[ -d "/Applications/Cherry Studio.app" ]` |
| LM Studio | Local LLM runner | `brew install --cask lm-studio` | `[ -d "/Applications/LM Studio.app" ]` |

**检测脚本:**
```bash
detect_vibe_coding() {
    echo "=== Vibe Coding Tools ==="
    command -v claude &>/dev/null && echo "✅ Claude Code: $(claude --version 2>/dev/null || echo 'installed')" || echo "❌ Claude Code"
    command -v ccline &>/dev/null && echo "✅ CCometixLine: installed" || echo "❌ CCometixLine"
    [ -d "/Applications/Cursor.app" ] && echo "✅ Cursor: installed" || echo "❌ Cursor"
    command -v opencode &>/dev/null && echo "✅ OpenCode: installed" || echo "❌ OpenCode"
    [ -d "/Applications/Cherry Studio.app" ] && echo "✅ Cherry Studio: installed" || echo "❌ Cherry Studio"
    [ -d "/Applications/LM Studio.app" ] && echo "✅ LM Studio: installed" || echo "❌ LM Studio"
}
```

**安装脚本 (带跳过检测):**
```bash
install_vibe_coding() {
    echo "=== Installing Vibe Coding Tools ==="

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
}
```

**Claude Code 配置:**
```bash
# 方式 1: Homebrew (推荐)
brew install --cask claude-code

# 方式 2: 原生安装脚本
curl -fsSL https://claude.ai/install.sh | bash

# 登录认证
claude login

# 启动
claude
```

**CCometixLine 配置 (Claude Code Statusline):**
```bash
# 安装 (需要 Node.js)
npm install -g @cometix/ccline

# 配置 Claude Code settings.json
# 位置: ~/.claude/settings.json
{
  "statusLine": {
    "type": "command",
    "command": "ccline",
    "padding": 0
  }
}

# 或使用 ccline 自带的 TUI 配置
ccline config
```

> CCometixLine 功能: Git 分支状态、Claude 模型名称、上下文使用率、工作目录显示

**OpenCode 配置:**
```bash
# 安装
brew install opencode

# 配置 (~/.opencode/config.yaml)
default_model: anthropic/claude-sonnet-4-20250514
providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
```

**Cherry Studio 配置:**
```bash
# 安装
brew install --cask cherry-studio

# 启动后在 UI 中配置 API Keys
```

---

## Fonts

### Programming Fonts
| Font | Description | Command |
|------|-------------|---------|
| JetBrains Mono | Monospace | `brew install --cask font-jetbrains-mono` |
| JetBrains Mono Nerd | With icons | `brew install --cask font-jetbrains-mono-nerd-font` |
| Fira Code | Ligatures | `brew install --cask font-fira-code` |
| Fira Code Nerd | With icons | `brew install --cask font-fira-code-nerd-font` |
| Hack Nerd Font | Terminal | `brew install --cask font-hack-nerd-font` |
| Meslo LG Nerd | Powerline | `brew install --cask font-meslo-lg-nerd-font` |

### UI Fonts
| Font | Description | Command |
|------|-------------|---------|
| Inter | UI font | `brew install --cask font-inter` |
| Noto Sans CJK SC | Chinese | `brew install --cask font-noto-sans-cjk-sc` |

---

## Zsh Plugins

| Plugin | Description | Install |
|--------|-------------|---------|
| zsh-autosuggestions | Command suggestions | `git clone https://github.com/zsh-users/zsh-autosuggestions ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions` |
| zsh-syntax-highlighting | Syntax colors | `git clone https://github.com/zsh-users/zsh-syntax-highlighting ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting` |

---

## macOS Defaults

### Dock
```bash
# Hide recent apps
defaults write com.apple.dock show-recents -bool false

# Faster animations
defaults write com.apple.dock autohide-delay -float 0
defaults write com.apple.dock autohide-time-modifier -float 0.3

# Set icon size
defaults write com.apple.dock tilesize -int 48

# Apply
killall Dock
```

### Keyboard
```bash
# Faster key repeat
defaults write NSGlobalDomain KeyRepeat -int 2
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Disable auto-correct
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# Disable press-and-hold
defaults write NSGlobalDomain ApplePressAndHoldEnabled -bool false
```

### Finder
```bash
# Show hidden files
defaults write com.apple.finder AppleShowAllFiles -bool true

# Show all extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Show path bar
defaults write com.apple.finder ShowPathbar -bool true

# Show status bar
defaults write com.apple.finder ShowStatusBar -bool true

# Apply
killall Finder
```

### Screenshots
```bash
# Save to folder
mkdir -p ~/Pictures/Screenshots
defaults write com.apple.screencapture location ~/Pictures/Screenshots

# PNG format
defaults write com.apple.screencapture type -string "png"

# Disable shadow
defaults write com.apple.screencapture disable-shadow -bool true

# Apply
killall SystemUIServer
```

---

## Detection Scripts

### Check if package is installed

```bash
# Brew formula
brew list <package> &>/dev/null && echo "installed" || echo "not installed"

# Brew cask
brew list --cask <package> &>/dev/null && echo "installed" || echo "not installed"

# Command
command -v <cmd> &>/dev/null && echo "installed" || echo "not installed"

# App
[ -d "/Applications/<App>.app" ] && echo "installed" || echo "not installed"
```

### Full detection script

```bash
#!/bin/bash
# detect-installed.sh

echo "=== Checking installed packages ==="

check_cmd() {
    command -v "$1" &>/dev/null && echo "✅ $1" || echo "❌ $1"
}

check_app() {
    [ -d "/Applications/$1.app" ] && echo "✅ $1" || echo "❌ $1"
}

echo "--- CLI Tools ---"
check_cmd git
check_cmd gh
check_cmd delta
check_cmd starship
check_cmd eza
check_cmd bat
check_cmd fd
check_cmd rg

echo "--- Languages ---"
check_cmd fnm
check_cmd node
check_cmd pnpm
check_cmd uv
check_cmd python3
check_cmd goenv
check_cmd go

echo "--- Container ---"
check_cmd docker
check_cmd kubectl
check_cmd helm
check_cmd k9s

echo "--- Applications ---"
check_app "Raycast"
check_app "Warp"
check_app "Cursor"
check_app "Visual Studio Code"
check_app "OrbStack"
```
