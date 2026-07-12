# Claude Code Skills

A collection of 55+ custom Claude Code skills for Python development, DevOps, infrastructure automation, and productivity.

## Overview

This repository contains modular skills that extend Claude's capabilities with specialized knowledge, workflows, and tools. Each skill is designed following Anthropic's best practices for progressive disclosure and token efficiency.

## Skills

### Authentication & Secrets (3)

| Skill | Description |
|-------|-------------|
| `1password` | 1Password secrets management - CLI operations, service accounts, and Kubernetes integration |
| `azure-ad-sso` | Azure AD OAuth2/OIDC SSO integration for Kubernetes applications |
| `keyvault-csi-driver` | Azure Key Vault + CSI Driver integration for Kubernetes secrets management |

### Azure & Cloud (6)

| Skill | Description |
|-------|-------------|
| `az-aks-agent` | Azure AKS Agentic CLI - AI-powered troubleshooting and insights for AKS |
| `azure-devops` | Comprehensive Azure DevOps REST API for work items, pipelines, repos, and more |
| `azure-devops-wiki` | Azure DevOps Wiki management and automation |
| `using-cloud-cli` | AWS & GCP CLI usage patterns and best practices |

### Container & Orchestration (7)

| Skill | Description |
|-------|-------------|
| `knative` | Knative serverless platform for Kubernetes |
| `argocd` | ArgoCD API and CLI for GitOps automation |
| `gitops-principles` | GitOps fundamentals and best practices |
| `opentelemetry` | OpenTelemetry instrumentation and observability |

### DNS & Networking (2)

| Skill | Description |
|-------|-------------|
| `cloudflare-dns` | Cloudflare DNS management with Azure integration |
| `external-dns` | External-DNS configuration across Azure DNS, Route53, Cloudflare, and GCP |

### Developer Tools (5)

| Skill | Description |
|-------|-------------|
| `neovim` | Comprehensive Neovim configuration guide (82+ plugins) |
| `iterm2` | iTerm2 terminal emulator and tmux multiplexer expertise |
| `shell-prompt` | Shell prompt configuration and customization |
| `direnv` | direnv for directory-specific environment variables |
| `git-worktree` | Git worktrees for parallel development |

### Git & Version Control (2)

| Skill | Description |
|-------|-------------|
| `git` | Comprehensive Git workflows with 13 workflow definitions |
| `using-git-worktrees` | Git worktree workflow automation |

### Infrastructure & DevOps (4)

| Skill | Description |
|-------|-------------|
| `managing-infra` | Infrastructure patterns for Kubernetes, Terraform, Helm, and GitHub Actions |
| `defectdojo` | DefectDojo security vulnerability management |
| `github-pages` | GitHub Pages deployment with 6 workflow templates |
| `mkdocs` | MkDocs documentation site generation |

### Monitoring & Observability (7)

| Skill | Description |
|-------|-------------|
| `prometheus` | Prometheus HTTP API queries and PromQL |
| `grafana` | Grafana HTTP API for dashboards, alerts, and data sources |
| `loki` | Grafana Loki log aggregation and LogQL queries |
| `mimir` | Grafana Mimir for long-term Prometheus metrics storage |
| `tempo` | Grafana Tempo distributed tracing |
| `pyroscope` | Continuous profiling with Pyroscope |
| `holmesgpt` | AI-powered monitoring insights |

### Obsidian & Knowledge Management (4)

| Skill | Description |
|-------|-------------|
| `obsidian` | Obsidian vault management fundamentals |
| `obsidian-vault-management` | Advanced vault features with dataview queries |
| `obsidian-nvim` | Obsidian + Neovim integration |
| `obsidian-claude-integration` | Second brain patterns and templates |

### Programming Languages & Frameworks (6)

| Skill | Description |
|-------|-------------|
| `writing-python` | Idiomatic Python 3.14+ development patterns |
| `writing-go` | Go development best practices |
| `writing-typescript` | TypeScript & React patterns |
| `uv` | uv package manager (10-100x faster than pip) |
| `playwright` | Browser automation with Playwright |

### Utilities & AI (7)

| Skill | Description |
|-------|-------------|
| `repomix` | Pack codebases into AI-friendly files |
| `markitdown` | Document conversion to markdown |
| `looking-up-docs` | Library documentation lookup via Context7 |
| `researching-web` | Web research patterns |
| `consulting-design` | Consult Gemini AI for architecture alternatives |
| `reviewing-code` | Code review with Codex AI |
| `zsh-path` | Zsh PATH management |

### System Monitoring (1)

| Skill | Description |
|-------|-------------|
| `zabbix-api` | Zabbix monitoring system automation via API and Python |

## Repository Structure

```
claude-code-skills/
├── README.md                      # This file
├── LICENSE                        # MIT License
├── .gitignore
├── docs/
│   └── references.md              # Research and reference links
├── scripts/
│   └── install-skills.sh          # Symlink skills to ~/.claude/skills/
├── templates/
│   └── skill-template/            # Template for creating new skills
│       ├── SKILL.md
│       ├── scripts/.gitkeep
│       ├── references/.gitkeep
│       └── assets/.gitkeep
└── skills/                        # 55 skill implementations
    ├── 1password-skill/
    │   ├── SKILL.md               # Main skill definition
    │   ├── references/            # 2 reference docs
    │   └── scripts/               # 3 shell scripts
    ├── argocd-skill/
    │   ├── SKILL.md
    │   ├── references/            # 2 reference docs
    │   └── scripts/               # 1 shell script
    ├── grafana-skill/
    │   ├── SKILL.md
    │   ├── references/            # 7 reference docs
    │   └── scripts/               # 1 Python script
    ├── ... (52 more skills)
    └── zsh-path-skill/
        └── SKILL.md
```

### Skill Structure Patterns

Each skill follows a consistent structure:

| Directory | Purpose |
|-----------|---------|
| `SKILL.md` | Main skill definition with YAML frontmatter |
| `references/` | Reference documentation loaded on-demand |
| `scripts/` | Executable Python/Bash/Zsh scripts |
| `templates/` | Workflow/configuration templates |
| `samples/` | YAML configuration examples |
| `workflows/` | Workflow definitions |
| `assets/` | Images, fonts, and other resources |

## Installation

### Claude Code (Project-level)
```bash
# Clone to your project's .claude/skills directory
git clone https://github.com/YOUR_USERNAME/claude-code-skills.git .claude/skills
```

### Claude Code (User-level)
```bash
# Clone to your personal skills directory
git clone https://github.com/YOUR_USERNAME/claude-code-skills.git ~/.claude/skills
```

### Using the Install Script
```bash
# Run the install script to symlink individual skills
./scripts/install-skills.sh
```

### Claude.ai Desktop
Upload individual `.skill` packages via Settings > Skills.

## Skill Development

### Creating a New Skill

1. Copy the template:
   ```bash
   cp -r templates/skill-template skills/your-skill-name
   ```

2. Edit `SKILL.md` with:
   - YAML frontmatter (`name`, `description`)
   - Markdown instructions

3. Add supporting resources:
   - `scripts/` - Executable Python/Bash scripts
   - `references/` - Documentation loaded on-demand
   - `assets/` - Templates, images, fonts

### Best Practices

- **Be concise**: Claude is smart; only add what it doesn't know
- **Progressive disclosure**: Keep SKILL.md under 500 lines
- **Clear triggers**: Description should explain WHEN to use the skill
- **Test scripts**: Verify all scripts work before committing

## Tech Stack Preferences

This repository's skills are optimized for:

- **Package Manager**: [uv](https://github.com/astral-sh/uv) (10-100x faster than pip)
- **Web Framework**: [Flask](https://flask.palletsprojects.com/) (lightweight WSGI)
- **Infrastructure**: Azure AKS, Kubernetes
- **Code Quality**: ruff, mypy, pytest
- **GitOps**: ArgoCD, Kargo, External-DNS
- **Observability**: Prometheus, Grafana, Loki, Tempo

## Statistics

| Metric | Count |
|--------|-------|
| Total Skills | 55 |
| Reference Docs | 200+ |
| Python Scripts | ~25 |
| Shell Scripts | ~20 |

## References

See [docs/references.md](docs/references.md) for curated links to:
- Official Claude Code documentation
- Skill authoring best practices
- Python project templates
- Community skills and resources

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b skill/new-skill-name`)
3. Follow the skill template structure
4. Test your skill thoroughly
5. Submit a Pull Request

---

*Built for use with [Claude Code](https://claude.ai/code) by Anthropic*
