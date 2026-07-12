#!/usr/bin/env bun
/**
 * HookGenerator - Generate .pre-commit-config.yaml templates
 *
 * Usage:
 *   bun run HookGenerator.ts <preset> [options]
 *
 * Presets:
 *   minimal     - Basic hooks (whitespace, yaml, merge conflicts)
 *   python      - Python project hooks (black, isort, flake8, mypy)
 *   javascript  - JS/TS project hooks (prettier, eslint)
 *   terraform   - Infrastructure hooks (fmt, validate, docs, tflint)
 *   kubernetes  - K8s/Helm hooks (yamllint, kubeconform, checkov)
 *   security    - Security-focused hooks (gitleaks, bandit, trivy)
 *   full        - Comprehensive setup with all categories
 */

import { writeFileSync, existsSync } from "fs";
import { stringify as stringifyYaml } from "yaml";

interface HookConfig {
  id: string;
  name?: string;
  args?: string[];
  files?: string;
  exclude?: string;
  types?: string[];
  types_or?: string[];
  stages?: string[];
  additional_dependencies?: string[];
  always_run?: boolean;
  pass_filenames?: boolean;
}

interface RepoConfig {
  repo: string;
  rev: string;
  hooks: HookConfig[];
}

interface PreCommitConfig {
  default_stages?: string[];
  fail_fast?: boolean;
  repos: RepoConfig[];
}

// Hook templates by category
const hookTemplates: Record<string, RepoConfig[]> = {
  base: [
    {
      repo: "https://github.com/pre-commit/pre-commit-hooks",
      rev: "v5.0.0",
      hooks: [
        { id: "trailing-whitespace" },
        { id: "end-of-file-fixer" },
        { id: "check-yaml", args: ["--allow-multiple-documents"] },
        { id: "check-json" },
        { id: "check-added-large-files", args: ["--maxkb=1000"] },
        { id: "check-merge-conflict" },
        { id: "detect-private-key" },
        { id: "no-commit-to-branch", args: ["--branch", "main", "--branch", "master"] },
      ],
    },
  ],

  python: [
    {
      repo: "https://github.com/astral-sh/ruff-pre-commit",
      rev: "v0.7.3",
      hooks: [
        { id: "ruff", args: ["--fix"] },
        { id: "ruff-format" },
      ],
    },
    {
      repo: "https://github.com/pre-commit/mirrors-mypy",
      rev: "v1.13.0",
      hooks: [
        {
          id: "mypy",
          additional_dependencies: ["types-requests", "types-PyYAML"],
        },
      ],
    },
    {
      repo: "https://github.com/pycqa/bandit",
      rev: "1.7.10",
      hooks: [
        {
          id: "bandit",
          args: ["-c", "pyproject.toml"],
          additional_dependencies: ["bandit[toml]"],
        },
      ],
    },
  ],

  python_classic: [
    {
      repo: "https://github.com/psf/black",
      rev: "24.10.0",
      hooks: [{ id: "black" }],
    },
    {
      repo: "https://github.com/pycqa/isort",
      rev: "5.13.2",
      hooks: [{ id: "isort", args: ["--profile=black"] }],
    },
    {
      repo: "https://github.com/pycqa/flake8",
      rev: "7.1.1",
      hooks: [
        { id: "flake8", args: ["--max-line-length=88", "--extend-ignore=E203"] },
      ],
    },
  ],

  javascript: [
    {
      repo: "https://github.com/biomejs/pre-commit",
      rev: "v0.5.0",
      hooks: [
        {
          id: "biome-check",
          additional_dependencies: ["@biomejs/biome@1.9.4"],
        },
      ],
    },
  ],

  javascript_classic: [
    {
      repo: "https://github.com/pre-commit/mirrors-prettier",
      rev: "v4.0.0-alpha.8",
      hooks: [
        {
          id: "prettier",
          types_or: ["javascript", "jsx", "ts", "tsx", "json", "yaml", "markdown"],
        },
      ],
    },
    {
      repo: "https://github.com/pre-commit/mirrors-eslint",
      rev: "v9.14.0",
      hooks: [
        {
          id: "eslint",
          files: "\\.[jt]sx?$",
          additional_dependencies: [
            "eslint@9.14.0",
            "typescript",
            "@typescript-eslint/parser",
            "@typescript-eslint/eslint-plugin",
          ],
        },
      ],
    },
  ],

  terraform: [
    {
      repo: "https://github.com/antonbabenko/pre-commit-terraform",
      rev: "v1.96.2",
      hooks: [
        { id: "terraform_fmt" },
        { id: "terraform_validate" },
        {
          id: "terraform_docs",
          args: [
            "--hook-config=--path-to-file=README.md",
            "--hook-config=--create-file-if-not-exist=true",
          ],
        },
        {
          id: "terraform_tflint",
          args: ["--args=--config=__GIT_WORKING_DIR__/.tflint.hcl"],
        },
        {
          id: "terraform_trivy",
          args: ["--args=--severity=HIGH,CRITICAL"],
        },
      ],
    },
  ],

  kubernetes: [
    {
      repo: "https://github.com/adrienverge/yamllint",
      rev: "v1.35.1",
      hooks: [{ id: "yamllint", args: ["-c", ".yamllint.yaml"] }],
    },
    {
      repo: "https://github.com/gruntwork-io/pre-commit",
      rev: "v0.1.23",
      hooks: [{ id: "helmlint" }],
    },
    {
      repo: "https://github.com/bridgecrewio/checkov",
      rev: "3.2.277",
      hooks: [
        {
          id: "checkov",
          args: ["--framework", "kubernetes", "--quiet", "--compact"],
        },
      ],
    },
  ],

  security: [
    {
      repo: "https://github.com/gitleaks/gitleaks",
      rev: "v8.21.2",
      hooks: [{ id: "gitleaks" }],
    },
    {
      repo: "https://github.com/Yelp/detect-secrets",
      rev: "v1.5.0",
      hooks: [
        { id: "detect-secrets", args: ["--baseline", ".secrets.baseline"] },
      ],
    },
  ],

  yaml: [
    {
      repo: "https://github.com/adrienverge/yamllint",
      rev: "v1.35.1",
      hooks: [{ id: "yamllint", args: ["-c", ".yamllint.yaml"] }],
    },
  ],

  shell: [
    {
      repo: "https://github.com/shellcheck-py/shellcheck-py",
      rev: "v0.10.0.1",
      hooks: [{ id: "shellcheck", args: ["-x"] }],
    },
    {
      repo: "https://github.com/scop/pre-commit-shfmt",
      rev: "v3.10.0-1",
      hooks: [{ id: "shfmt", args: ["-i", "2", "-ci"] }],
    },
  ],

  go: [
    {
      repo: "https://github.com/golangci/golangci-lint",
      rev: "v1.62.0",
      hooks: [{ id: "golangci-lint" }],
    },
    {
      repo: "https://github.com/dnephin/pre-commit-golang",
      rev: "v0.5.1",
      hooks: [{ id: "go-fmt" }, { id: "go-vet" }, { id: "go-imports" }],
    },
  ],

  docker: [
    {
      repo: "https://github.com/hadolint/hadolint",
      rev: "v2.12.0",
      hooks: [{ id: "hadolint" }],
    },
  ],

  docs: [
    {
      repo: "https://github.com/igorshubovych/markdownlint-cli",
      rev: "v0.42.0",
      hooks: [{ id: "markdownlint", args: ["--fix"] }],
    },
    {
      repo: "https://github.com/crate-ci/typos",
      rev: "v1.27.0",
      hooks: [{ id: "typos" }],
    },
  ],

  commits: [
    {
      repo: "https://github.com/compilerla/conventional-pre-commit",
      rev: "v3.6.0",
      hooks: [
        {
          id: "conventional-pre-commit",
          stages: ["commit-msg"],
          args: ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "ci", "build"],
        },
      ],
    },
  ],
};

// Preset definitions
const presets: Record<string, string[]> = {
  minimal: ["base"],
  python: ["base", "python", "security"],
  python_classic: ["base", "python_classic", "security"],
  javascript: ["base", "javascript", "security"],
  javascript_classic: ["base", "javascript_classic", "security"],
  terraform: ["base", "terraform"],
  kubernetes: ["base", "kubernetes", "security"],
  infrastructure: ["base", "terraform", "kubernetes", "security"],
  security: ["base", "security"],
  go: ["base", "go", "security"],
  full: ["base", "yaml", "shell", "docker", "docs", "security", "commits"],
};

function generateConfig(categories: string[]): PreCommitConfig {
  const repos: RepoConfig[] = [];
  const seenRepos = new Set<string>();

  for (const category of categories) {
    const templates = hookTemplates[category];
    if (!templates) {
      console.warn(`⚠️  Unknown category: ${category}`);
      continue;
    }

    for (const template of templates) {
      // Avoid duplicate repos
      if (seenRepos.has(template.repo)) {
        // Merge hooks into existing repo
        const existingRepo = repos.find((r) => r.repo === template.repo);
        if (existingRepo) {
          for (const hook of template.hooks) {
            if (!existingRepo.hooks.some((h) => h.id === hook.id)) {
              existingRepo.hooks.push(hook);
            }
          }
        }
      } else {
        repos.push({ ...template, hooks: [...template.hooks] });
        seenRepos.add(template.repo);
      }
    }
  }

  return {
    default_stages: ["pre-commit"],
    fail_fast: false,
    repos,
  };
}

function generateYaml(config: PreCommitConfig): string {
  // Custom YAML generation for cleaner output
  let yaml = "# .pre-commit-config.yaml\n";
  yaml += "# Generated by HookGenerator\n\n";

  if (config.default_stages) {
    yaml += `default_stages: [${config.default_stages.join(", ")}]\n`;
  }
  if (config.fail_fast !== undefined) {
    yaml += `fail_fast: ${config.fail_fast}\n`;
  }

  yaml += "\nrepos:\n";

  for (const repo of config.repos) {
    yaml += `  - repo: ${repo.repo}\n`;
    yaml += `    rev: ${repo.rev}\n`;
    yaml += `    hooks:\n`;

    for (const hook of repo.hooks) {
      yaml += `      - id: ${hook.id}\n`;

      if (hook.name) {
        yaml += `        name: ${hook.name}\n`;
      }
      if (hook.args && hook.args.length > 0) {
        if (hook.args.length === 1) {
          yaml += `        args: [${hook.args[0]}]\n`;
        } else {
          yaml += `        args:\n`;
          for (const arg of hook.args) {
            yaml += `          - ${arg}\n`;
          }
        }
      }
      if (hook.files) {
        yaml += `        files: ${hook.files}\n`;
      }
      if (hook.exclude) {
        yaml += `        exclude: ${hook.exclude}\n`;
      }
      if (hook.types && hook.types.length > 0) {
        yaml += `        types: [${hook.types.join(", ")}]\n`;
      }
      if (hook.types_or && hook.types_or.length > 0) {
        yaml += `        types_or: [${hook.types_or.join(", ")}]\n`;
      }
      if (hook.stages && hook.stages.length > 0) {
        yaml += `        stages: [${hook.stages.join(", ")}]\n`;
      }
      if (hook.additional_dependencies && hook.additional_dependencies.length > 0) {
        yaml += `        additional_dependencies:\n`;
        for (const dep of hook.additional_dependencies) {
          yaml += `          - ${dep}\n`;
        }
      }
      if (hook.always_run) {
        yaml += `        always_run: true\n`;
      }
      if (hook.pass_filenames === false) {
        yaml += `        pass_filenames: false\n`;
      }
    }
    yaml += "\n";
  }

  return yaml.trim() + "\n";
}

function showHelp(): void {
  console.log(`
HookGenerator - Generate .pre-commit-config.yaml templates

Usage:
  bun run HookGenerator.ts <preset> [options]

Presets:
  minimal           Basic hooks (whitespace, yaml, merge conflicts)
  python            Python project (ruff, mypy, bandit)
  python_classic    Python project (black, isort, flake8)
  javascript        JS/TS project (biome)
  javascript_classic JS/TS project (prettier, eslint)
  terraform         Terraform/IaC hooks
  kubernetes        K8s/Helm hooks
  infrastructure    Terraform + Kubernetes
  security          Security-focused hooks
  go                Go project hooks
  full              Comprehensive setup

Options:
  --output, -o <file>  Output file (default: .pre-commit-config.yaml)
  --force, -f          Overwrite existing file
  --dry-run            Print config without writing
  --add <categories>   Add specific categories (comma-separated)
  --list               List available categories

Categories:
  base, python, python_classic, javascript, javascript_classic,
  terraform, kubernetes, security, yaml, shell, go, docker, docs, commits

Examples:
  bun run HookGenerator.ts python
  bun run HookGenerator.ts minimal --add security,commits
  bun run HookGenerator.ts terraform --dry-run
  bun run HookGenerator.ts --list
`);
}

function listCategories(): void {
  console.log("Available Categories:\n");

  for (const [category, repos] of Object.entries(hookTemplates)) {
    const hookCount = repos.reduce((acc, r) => acc + r.hooks.length, 0);
    console.log(`  ${category.padEnd(20)} ${hookCount} hooks`);
    for (const repo of repos) {
      const repoName = repo.repo.split("/").slice(-1)[0];
      console.log(`    └─ ${repoName}: ${repo.hooks.map((h) => h.id).join(", ")}`);
    }
  }

  console.log("\nPresets:\n");
  for (const [preset, categories] of Object.entries(presets)) {
    console.log(`  ${preset.padEnd(20)} ${categories.join(", ")}`);
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    showHelp();
    process.exit(0);
  }

  if (args.includes("--list")) {
    listCategories();
    process.exit(0);
  }

  // Parse options
  const preset = args[0];
  const outputIndex = args.findIndex((a) => a === "--output" || a === "-o");
  const outputFile =
    outputIndex > -1 ? args[outputIndex + 1] : ".pre-commit-config.yaml";
  const force = args.includes("--force") || args.includes("-f");
  const dryRun = args.includes("--dry-run");
  const addIndex = args.findIndex((a) => a === "--add");
  const additionalCategories = addIndex > -1 ? args[addIndex + 1].split(",") : [];

  // Determine categories
  let categories: string[];
  if (presets[preset]) {
    categories = [...presets[preset], ...additionalCategories];
  } else if (hookTemplates[preset]) {
    categories = ["base", preset, ...additionalCategories];
  } else {
    console.error(`❌ Unknown preset or category: ${preset}`);
    console.log("💡 Use --list to see available options");
    process.exit(1);
  }

  // Generate config
  console.log(`🔧 Generating config with: ${categories.join(", ")}\n`);
  const config = generateConfig(categories);
  const yaml = generateYaml(config);

  if (dryRun) {
    console.log(yaml);
    return;
  }

  // Check existing file
  if (existsSync(outputFile) && !force) {
    console.error(`❌ ${outputFile} already exists`);
    console.log("💡 Use --force to overwrite");
    process.exit(1);
  }

  // Write file
  writeFileSync(outputFile, yaml);
  console.log(`✅ Generated ${outputFile}`);
  console.log(`   Repositories: ${config.repos.length}`);
  const hookCount = config.repos.reduce((acc, r) => acc + r.hooks.length, 0);
  console.log(`   Total Hooks: ${hookCount}`);

  console.log("\n📋 Next steps:");
  console.log("   1. Review the generated configuration");
  console.log("   2. Run: pre-commit install");
  console.log("   3. Test: pre-commit run --all-files");
}

main().catch(console.error);
