//! `ship push`: push a branch and set upstream, Azure Bearer token first.

use crate::{detect_kind, git};
use std::io::{self, Write};

/// A ref name git would read as an option (`-`), a force refspec (`+`) or a
/// `src:dst` refspec (`:`). Shared with `snapshot`'s tag-name check.
pub fn is_unsafe_ref(name: &str) -> bool {
    name.starts_with(['-', '+']) || name.contains(':')
}

/// Reject input that git would read as an option or a refspec: a remote starting
/// with `-`, a branch starting with `-` or `+` (force refspec) or containing `:`
/// (`src:dst` refspec).
pub fn validate_target(remote: &str, branch: Option<&str>) -> Result<(), String> {
    if remote.starts_with('-') {
        return Err(format!("invalid remote '{remote}': must not start with '-'"));
    }
    if let Some(b) = branch
        && is_unsafe_ref(b)
    {
        return Err(format!(
            "invalid branch '{b}': must not start with '-' or '+' or contain ':'"
        ));
    }
    Ok(())
}

/// Push `branch` (default: the current one) to `remote`. Returns the exit code:
/// 0 on success, 1 when the final push fails (`push failed` on stderr), 2 for an
/// invalid remote or branch (nothing is pushed).
pub fn run(remote: &str, branch: Option<&str>) -> io::Result<u8> {
    if let Err(msg) = validate_target(remote, branch) {
        eprintln!("ship: {msg}");
        return Ok(2);
    }
    let branch = match branch {
        Some(b) if !b.is_empty() => b.to_string(),
        _ => git::current_branch()?,
    };
    let url = git::remote_url(remote);
    let override_platform = std::env::var("SHIP_PLATFORM").ok();
    let kind = detect_kind(&url, override_platform.as_deref());
    eprintln!(">> pushing {branch} -> {remote} ({})", kind.as_str());

    match git::push_with_auth(kind, remote, &[&branch]) {
        Some(mode) => {
            let mut out = io::stdout().lock();
            writeln!(out, "push_ok={}", mode.as_str())?;
            out.flush()?;
            Ok(0)
        }
        None => {
            eprintln!("push failed");
            Ok(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::validate_target;

    #[test]
    fn rejects_force_refspecs_options_and_colons() {
        assert!(validate_target("origin", Some("+main")).is_err());
        assert!(validate_target("origin", Some("-f")).is_err());
        assert!(validate_target("origin", Some("a:b")).is_err());
        assert!(validate_target("--force", None).is_err());
    }

    #[test]
    fn accepts_ordinary_targets() {
        assert!(validate_target("origin", Some("feat/x")).is_ok());
        assert!(validate_target("up", None).is_ok());
    }
}
