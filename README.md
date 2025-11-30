# Claude Code Skills

A collection of custom Claude Code skills for Python development, DevOps, and infrastructure automation.

## Overview

This repository contains modular skills that extend Claude's capabilities with specialized knowledge, workflows, and tools. Each skill is designed following Anthropic's best practices for progressive disclosure and token efficiency.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| `python-project` | Python project scaffolding with uv, Flask, and modern tooling | 🚧 Planned |
| `k8s-operations` | Kubernetes operations for Azure AKS environments | 🚧 Planned |
| `devops-automation` | CI/CD and infrastructure automation workflows | 🚧 Planned |

## Repository Structure

```
claude-code-skills/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   └── references.md          # Research and reference links
├── skills/
│   ├── python-project/        # Python project skill
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   ├── references/
│   │   └── assets/
│   ├── k8s-operations/        # Kubernetes operations skill
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   └── references/
│   └── devops-automation/     # DevOps automation skill
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── templates/
    └── skill-template/        # Template for creating new skills
        ├── SKILL.md
        ├── scripts/.gitkeep
        ├── references/.gitkeep
        └── assets/.gitkeep
```

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
