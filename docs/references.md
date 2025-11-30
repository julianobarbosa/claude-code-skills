# Claude Code Skills for Python - Reference Links

> **Created:** 2025-11-28
> **Purpose:** Reference collection for Claude Code Skills related to Python specifications and best practices

---

## Official Documentation

### Anthropic/Claude Official
- **Skill Authoring Best Practices**
  https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices

- **Agent Skills Documentation (Claude Code)**
  https://code.claude.com/docs/en/skills

- **Claude Code Best Practices (Anthropic Engineering Blog)**
  https://www.anthropic.com/engineering/claude-code-best-practices

- **How to Create Skills for Claude**
  https://www.claude.com/blog/how-to-create-skills-key-steps-limitations-and-examples

---

## Python Package Management

### uv - Modern Python Package Manager
- **astral-sh/uv** - An extremely fast Python package and project manager, written in Rust
  https://github.com/astral-sh/uv

- **uv Documentation**
  https://docs.astral.sh/uv/

#### Key Features
- 🚀 Single tool replacing `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv`
- ⚡️ 10-100x faster than pip
- 🗂️ Universal lockfile for comprehensive project management
- ❇️ Inline script dependency metadata support
- 🐍 Python version management (install/switch versions)
- 🛠️ Tool execution (`uvx` for ephemeral environments)
- 🏢 Cargo-style workspaces for scalable projects
- 💾 Global cache for disk-space efficient dependency deduplication

#### Quick Reference
```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Project management
uv init example          # Initialize new project
uv add ruff              # Add dependency
uv run ruff check        # Run in project environment
uv lock                  # Generate lockfile
uv sync                  # Sync dependencies

# Scripts with inline dependencies
uv add --script example.py requests
uv run example.py

# Tools (like pipx)
uvx pycowsay 'hello!'    # Run tool in ephemeral env
uv tool install ruff     # Install tool globally

# Python version management
uv python install 3.10 3.11 3.12
uv python pin 3.11
uv venv --python 3.12.0

# pip-compatible interface
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

---

## GitHub Repositories

### Python Project Templates
- **iepathos/python-claude-code** - Python starter template optimized for Claude Code
  https://github.com/iepathos/python-claude-code

- **discus0434/python-template-for-claude-code** - Python project template for Claude Code centric development
  https://github.com/discus0434/python-template-for-claude-code

### Skills Collections
- **travisvn/awesome-claude-skills** - Curated list of Claude Skills and resources
  https://github.com/travisvn/awesome-claude-skills

### Advanced Frameworks
- **ruvnet/claude-flow** - Agent orchestration platform (CLAUDE MD Python wiki)
  https://github.com/ruvnet/claude-flow/wiki/CLAUDE-MD-Python

---

## Community Skills (claude-plugins.dev)

- **python-style** - Python coding conventions and best practices
  https://claude-plugins.dev/skills/@hoelzro/dotfiles/python-style

- **project-planner** - Transforms project ideas into structured documentation
  https://claude-plugins.dev/skills/@MacroMan5/claude-code-workflow-plugins/project-planner

---

## Technical Deep Dives & Tutorials

### Architecture & Implementation
- **Claude Agent Skills: A First Principles Deep Dive** (Lee Han Chung)
  https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/

- **Inside Claude Code Skills: Structure, prompts, invocation** (Mikhail Shilkov)
  https://mikhail.io/2025/10/claude-code-skills/

### Optimization & Best Practices
- **CLAUDE.md Best Practices from Optimizing Claude Code** (Arize AI)
  https://arize.com/blog/claude-md-best-practices-learned-from-optimizing-claude-code-with-prompt-learning/

- **Claude Code Top Tips: Lessons from the First 20 Hours** (Waleed Kadous - Medium)
  https://waleedk.medium.com/claude-code-top-tips-lessons-from-the-first-20-hours-246032b943b4

### Guides & Tutorials
- **The Claude Developer Guide in Python — Agent Skills** (GoPenAI/Medium)
  https://medium.com/@aserdargun/the-claude-developer-guide-in-python-agent-skills-9ff0544b51d6

- **Top 10 Claude Code Skills You Need to Know** (APIDog)
  https://apidog.com/blog/top-10-claude-code-skills/

- **ClaudeLog - Claude Code Docs, Guides & Best Practices**
  https://claudelog.com/faqs/what-programming-languages-work-best-with-claude-code/

---

## Key Concepts Summary

### SKILL.md Structure
```
my-skill/
├── SKILL.md           # Core instructions (YAML frontmatter + markdown)
├── scripts/           # Python/Bash executables
├── references/        # Documentation files
└── assets/            # Templates and binary files
```

### Frontmatter Requirements
- `name`: lowercase letters, numbers, hyphens only (max 64 chars)
- `description`: what the skill does AND when to use it (max 1024 chars)

### Best Practices
1. Use progressive disclosure - load files only when needed
2. Provide defaults with escape hatches for alternatives
3. Match instruction specificity to task fragility
4. Use forward slashes in paths (cross-platform)
5. Include concrete examples in skill instructions

---

## Web Frameworks

### Flask - Python Micro Web Framework
- **Flask Official Documentation**
  https://flask.palletsprojects.com/

- **Flask Installation Guide**
  https://flask.palletsprojects.com/en/stable/installation/

- **Flask Quickstart**
  https://flask.palletsprojects.com/en/stable/quickstart/

- **Flask GitHub Repository** (pallets/flask)
  https://github.com/pallets/flask

- **Flask on PyPI**
  https://pypi.org/project/Flask/

#### Overview
Flask is a lightweight WSGI web application framework. It's a "micro-framework" that provides essentials for web development without unnecessary complexity. Built on Werkzeug (WSGI toolkit) and Jinja2 (template engine).

#### Core Dependencies
- **Werkzeug**: WSGI interface between applications and servers
- **Jinja2**: Template language for rendering pages
- **MarkupSafe**: Escapes untrusted input for security
- **ItsDangerous**: Securely signs data (session cookies)
- **Click**: CLI framework for flask commands
- **Blinker**: Support for Signals

#### Quick Reference (with uv)
```bash
# Installation with uv
uv add flask

# Or with pip
pip install Flask

# Minimal application (app.py)
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

# Run development server
flask run
# Or with debug mode
flask run --debug

# Run on specific host/port
flask run --host=0.0.0.0 --port=8080
```

#### Project Structure
```
my_flask_app/
├── app.py              # Application entry point
├── static/             # CSS, JS, images
│   └── style.css
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   └── index.html
├── requirements.txt    # Dependencies
└── .env               # Environment variables
```

#### Key Features
- URL routing with decorators (`@app.route()`)
- Jinja2 templating with template inheritance
- Request/Response handling
- Session management (cookie-based)
- Static file serving
- Debug mode with auto-reload
- Extensible via Flask extensions

#### Recommended Extensions
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-Login**: User authentication
- **Flask-WTF**: Form handling and CSRF protection
- **Flask-RESTful**: REST API building
- **Flask-Migrate**: Database migrations

#### Learning Resources
- **Flask Mega-Tutorial** (Miguel Grinberg)
  https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

- **Flask Tutorial in VS Code**
  https://code.visualstudio.com/docs/python/tutorial-flask

- **GeeksforGeeks Flask Tutorial**
  https://www.geeksforgeeks.org/python/flask-tutorial/

---

## Related Topics for Further Research

- [ ] MCP (Model Context Protocol) integration with Skills
- [ ] Subagents vs Skills decision matrix
- [ ] Custom slash commands in Claude Code
- [ ] CLAUDE.md optimization techniques
- [ ] Python-specific testing skills (pytest integration)
- [ ] DevOps/Kubernetes skills for infrastructure management

---

*This document is part of the Claude Code Skills research project.*
