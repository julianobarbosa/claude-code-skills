//! Git subprocess helpers. Always an argument array, never a shell.

use std::io;
use std::process::{Command, Stdio};

/// Run `git` with `args`; stdout is trimmed. stderr is inherited, like the TS
/// `execFileSync` default. A non-zero exit is an error.
fn run(args: &[&str]) -> io::Result<String> {
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
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

/// Current checked-out branch name. Errors outside a repo.
pub fn current_branch() -> io::Result<String> {
    run(&["rev-parse", "--abbrev-ref", "HEAD"])
}

/// Fetch URL of a remote; empty string when the remote (or git itself) fails.
pub fn remote_url(remote: &str) -> String {
    run(&["remote", "get-url", remote]).unwrap_or_default()
}
