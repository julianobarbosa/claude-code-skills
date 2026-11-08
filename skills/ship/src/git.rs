//! Git subprocess helpers. Always an argument array, never a shell.

use std::io;
use std::process::{Command, Stdio};

/// Run `git` with `args`; stdout is returned untrimmed. stderr is inherited,
/// like the TS `execFileSync` default. A non-zero exit is an error.
fn run_raw(args: &[&str]) -> io::Result<String> {
    let out = Command::new("git")
        .args(args)
        .stdin(Stdio::null())
        .stderr(Stdio::inherit())
        .output()
        .map_err(|e| io::Error::new(e.kind(), format!("failed to run git: {e}")))?;
    if !out.status.success() {
        return Err(io::Error::other(format!(
            "Command failed: git {} ({})",
            args.join(" "),
            out.status
        )));
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

/// Like [`run_raw`] but with stdout trimmed, as the TS `sh()` does.
fn run(args: &[&str]) -> io::Result<String> {
    run_raw(args).map(|s| s.trim().to_string())
}

/// Current checked-out branch name. Errors outside a repo.
pub fn current_branch() -> io::Result<String> {
    run(&["rev-parse", "--abbrev-ref", "HEAD"])
}

/// Fetch URL of a remote; empty string when the remote (or git itself) fails.
pub fn remote_url(remote: &str) -> String {
    run(&["remote", "get-url", remote]).unwrap_or_default()
}

/// `git log --oneline @{u}..`: one line per local commit not on the upstream.
/// Empty when there is no upstream (or git fails); git's own stderr still shows.
pub fn log_ahead_of_upstream() -> String {
    run(&["log", "--oneline", "@{u}.."]).unwrap_or_default()
}

/// `git status --porcelain`, deliberately untrimmed: trimming would eat the
/// leading space of a first ` M path` line and misread it as staged (the TS
/// `sh()` bug). Only trailing newlines are dropped. Empty when git fails.
/// `--untracked-files=normal` is explicit so a `status.showUntrackedFiles=no`
/// config cannot hide new files from the scope guard; on default config the
/// output is identical to plain `git status --porcelain`.
pub fn status_porcelain() -> String {
    run_raw(&["status", "--porcelain", "--untracked-files=normal"])
        .map(|s| s.trim_end_matches('\n').to_string())
        .unwrap_or_default()
}
