# Workflow: Troubleshoot mise

Diagnose from evidence, not theory. mise gives you the diagnostics — run them before editing config.

## Always start here

```sh
mise doctor      # activation, PATH order, config files loaded, plugin status
mise config ls   # which config files are in play, and their tools
mise env         # the env mise would apply here
```

`mise doctor` alone resolves most issues by telling you exactly what's misconfigured. Add `MISE_DEBUG=1`
in front of any command for verbose logs.

## "Tool not found" / command missing

Almost always an **activation vs shims** problem, not a version problem.

- **In an interactive shell?** Check the activation line is in the shell rc and the shell was
  restarted. `mise doctor` reports if activation is missing.
- **In a script, IDE, cron, or CI?** These never hit a shell prompt, so `mise activate` doesn't apply.
  Fix with one of:
  ```sh
  mise exec -- <cmd>                 # run through mise
  eval "$(mise hook-env)"            # refresh env now, inside the script
  export PATH="$HOME/.local/share/mise/shims:$PATH"   # shims work everywhere
  ```
- **Just installed a new global CLI and its binary isn't found?** `mise reshim`, then check
  `~/.local/share/mise/shims/<tool>`.

## Wrong version is active

```sh
mise ls <tool>     # every installed version + which config selected the active one
mise config ls     # config priority: closer-to-cwd and global both matter
mise which <tool>  # the exact binary being resolved
```

Remember the precedence: within a directory `mise.toml` outranks idiomatic files (`.nvmrc` etc.), and
directories closer to `cwd` outrank parents and global.

## "Config file is not trusted"

mise won't evaluate a config that can run code until you trust it:

```sh
mise trust
```

Or pre-trust the tree in global settings:

```toml
[settings]
trusted_config_paths = ['~/work/my-trusted-projects']
```

## `mise self-update` refuses

mise was installed via a package manager (brew/apt/cargo). Update through that manager instead
(`brew upgrade mise`, etc.).

## Windows: bash not found for tasks

Point mise at a bash binary, per-project or globally:

```toml
[env]
MISE_BASH_PATH = 'C:/tools/msys64/usr/bin/bash.exe'
```

## Reset when things are genuinely weird

```sh
mise cache clear   # clear cached remote/version data
mise reshim        # rebuild shims
mise prune         # drop unreferenced installed versions
```

## Escalating

If `doctor` is clean but behavior is still wrong, the best single artifact to share is the full
`mise doctor` output plus the offending `mise.toml`. Upstream troubleshooting reference:
<https://mise.jdx.dev/troubleshooting.html>.
