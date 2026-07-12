# macOS Setup Presets

> Pre-configured development environment profiles for different roles

## Available Presets

| Preset | Target Role | Languages | Apps | Time |
|--------|-------------|-----------|------|------|
| `fullstack` | Fullstack Developer | JS/TS, Python | Full suite | ~20min |
| `frontend` | Frontend Developer | JS/TS | Design-focused | ~15min |
| `backend` | Backend Developer | Go, Python | API/Infra tools | ~18min |
| `data` | Data/ML Engineer | Python | Jupyter, ML libs | ~15min |
| `devops` | DevOps Engineer | Go, Python | K8s, Terraform | ~20min |
| `minimal` | Quick Start | None | Core only | ~8min |

---

## fullstack

**Target:** Fullstack Developer working with modern web stacks

### CLI Tools
```bash
brew install git gh delta starship
brew install eza bat fd ripgrep sd dust procs bottom
brew install tree wget curl jq yq
brew install shellcheck
```

### Languages
```bash
# Node.js
brew install fnm
fnm install --lts
fnm default lts-latest
npm install -g pnpm

# Python
brew install uv
uv python install 3.12
```

### Container & K8s
```bash
brew install kubectl helm k9s stern
brew tap danielfoehrkn/switch
brew install danielfoehrkn/switch/switch
```

### Applications
```bash
brew install --cask raycast
brew install --cask warp
brew install --cask cursor
brew install --cask claude-code
brew install --cask visual-studio-code
brew install --cask orbstack
brew install --cask sourcetree
brew install --cask notion
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code
brew install --cask font-inter
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, kubectl, zsh-autosuggestions, zsh-syntax-highlighting
- Starship prompt
- Modern CLI aliases (eza, bat)

### macOS Optimization
- Dock: hide recent apps
- Keyboard: faster repeat, disable auto-correct

---

## frontend

**Target:** Frontend Developer focused on UI/UX

### CLI Tools
```bash
brew install git gh delta starship
brew install eza bat fd ripgrep
brew install tree wget curl jq
```

### Languages
```bash
# Node.js only
brew install fnm
fnm install --lts
fnm default lts-latest
npm install -g pnpm
```

### Container (Optional)
```bash
# Basic Docker only
brew install --cask orbstack
```

### Applications
```bash
brew install --cask raycast
brew install --cask cursor
brew install --cask claude-code
brew install --cask visual-studio-code
brew install --cask iina
brew install --cask imageoptim
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code
brew install --cask font-inter
brew install --cask font-noto-sans-cjk-sc
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, zsh-autosuggestions, zsh-syntax-highlighting
- Starship prompt

### macOS Optimization
- Dock: hide recent apps
- Keyboard: faster repeat

---

## backend

**Target:** Backend Developer building APIs and services

### CLI Tools
```bash
brew install git gh delta starship
brew install eza bat fd ripgrep sd dust procs bottom
brew install tree wget curl jq yq
brew install shellcheck golangci-lint
```

### Languages
```bash
# Go
brew install goenv go
# Install latest stable Go version
LATEST_GO=$(goenv install -l | grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+$' | tail -1 | tr -d ' ')
goenv install "$LATEST_GO"
goenv global "$LATEST_GO"

# Python
brew install uv
uv python install 3.12
```

### Container & K8s
```bash
brew install kubectl helm k9s stern
brew tap danielfoehrkn/switch
brew install danielfoehrkn/switch/switch
brew install awscli rclone
```

### Applications
```bash
brew install --cask raycast
brew install --cask warp
brew install --cask cursor
brew install --cask claude-code
brew install --cask orbstack
brew install --cask sourcetree
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, kubectl, zsh-autosuggestions, zsh-syntax-highlighting
- Starship prompt
- Go development aliases

### macOS Optimization
- Dock: hide recent apps, faster animations
- Keyboard: faster repeat, disable auto-correct
- Finder: show hidden files, path bar

---

## data

**Target:** Data/ML Engineer working with Python and notebooks

### CLI Tools
```bash
brew install git gh delta starship
brew install eza bat fd ripgrep
brew install tree wget curl jq yq
```

### Languages
```bash
# Python (primary)
brew install uv
uv python install 3.11
uv python install 3.12

# Node.js (for Jupyter extensions)
brew install fnm
fnm install --lts
fnm default lts-latest
```

### Container
```bash
# Docker for ML containers
brew install --cask orbstack
```

### Applications
```bash
brew install --cask raycast
brew install --cask cursor
brew install --cask claude-code
brew install --cask visual-studio-code
```

### Python ML Stack (via uv)
```bash
# Create ML environment
uv venv ~/.venvs/ml
source ~/.venvs/ml/bin/activate
uv pip install jupyter pandas numpy scipy matplotlib seaborn scikit-learn
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
brew install --cask font-fira-code
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, zsh-autosuggestions, zsh-syntax-highlighting
- Python environment management

### macOS Optimization
- Keyboard: faster repeat

---

## devops

**Target:** DevOps/Platform Engineer managing infrastructure

### CLI Tools
```bash
brew install git gh delta starship
brew install eza bat fd ripgrep sd dust procs bottom
brew install tree wget curl jq yq
brew install shellcheck
```

### Languages
```bash
# Go (for tooling)
brew install goenv go

# Python (for automation)
brew install uv
uv python install 3.12
```

### Container & K8s (Full)
```bash
brew install kubectl helm k9s stern
brew tap danielfoehrkn/switch
brew install danielfoehrkn/switch/switch

# Cloud CLIs
brew install awscli
# brew install google-cloud-sdk  # Optional, large
# brew install azure-cli          # Optional

brew install rclone
```

### Infrastructure Tools
```bash
# Terraform (optional)
# brew install terraform

# Ansible (optional)
# brew install ansible
```

### Applications
```bash
brew install --cask raycast
brew install --cask warp
brew install --cask cursor
brew install --cask claude-code
brew install --cask orbstack
brew install --cask sourcetree
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, kubectl, aws, zsh-autosuggestions, zsh-syntax-highlighting
- kubeswitch for context management
- Starship with K8s context display

### macOS Optimization
- Dock: hide recent apps, faster animations
- Keyboard: faster repeat, disable auto-correct
- Finder: show hidden files, path bar

---

## minimal

**Target:** Quick start with essential tools only

### CLI Tools
```bash
brew install git gh starship
brew install eza bat fd ripgrep
```

### Applications
```bash
brew install --cask raycast
brew install --cask warp
brew install --cask cursor
brew install --cask claude-code
```

### Fonts
```bash
brew install --cask font-jetbrains-mono-nerd-font
```

### Shell Enhancement
- Oh-My-Zsh plugins: git, zsh-autosuggestions, zsh-syntax-highlighting
- Starship prompt

### macOS Optimization
- Dock: hide recent apps

---

## Custom Preset

Create your own preset by combining options:

```yaml
# Example: my-preset.yaml
name: My Custom Setup
extends: minimal  # Optional base preset

cli:
  - git
  - gh
  - delta
  - starship
  - eza
  - bat
  - fd
  - ripgrep

languages:
  nodejs: true    # fnm + pnpm
  python: true    # uv
  go: false
  rust: false

containers:
  docker: true
  kubernetes: false

apps:
  - raycast
  - warp
  - cursor

fonts:
  - font-jetbrains-mono-nerd-font

macos:
  dock:
    show_recents: false
  keyboard:
    key_repeat: 2
    initial_repeat: 15
    auto_correct: false
```

---

## Usage

```bash
# Use a preset
/new-macos-setup --preset fullstack

# Preview preset without installing
/new-macos-setup --preset backend --dry-run

# Combine preset with modifications
/new-macos-setup --preset minimal
# Then answer additional questions to customize
```
