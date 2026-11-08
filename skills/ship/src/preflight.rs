//! `ship preflight`: anything-to-deliver check plus a working-tree scope audit.
//! Advisory only: exits 0 whenever the branch lookup succeeds.

use crate::{git, scope_audit};
use std::io::{self, Write};

/// Print the preflight output. `branch` is resolved before anything is written, so
/// a non-repo leaves stdout empty. The warnings go to stderr after the stdout
/// lines, as in the TS script.
pub fn run() -> io::Result<()> {
    let branch = git::current_branch()?;

    let ahead = git::log_ahead_of_upstream();
    let ahead_count = if ahead.is_empty() { 0 } else { ahead.split('\n').count() };
    let audit = scope_audit(&git::status_porcelain());
    let s = &audit.status;

    // Keep the stdout result: a closed pipe must not silence the stderr guard below.
    let stdout_result = (|| {
        let mut out = io::stdout().lock();
        writeln!(out, "branch={branch}")?;
        writeln!(out, "commits_ahead_of_upstream={ahead_count}")?;
        writeln!(out, "staged={}", s.staged.len())?;
        writeln!(out, "unstaged={}", s.unstaged.len())?;
        writeln!(out, "untracked={}", s.untracked.len())?;
        writeln!(out, "scope_clean={}", audit.ok)?;
        out.flush()
    })();

    // Best effort: a closed stderr must not turn an advisory check into a failure.
    let mut err = io::stderr().lock();
    if !s.unstaged.is_empty() {
        let _ = writeln!(
            err,
            ">> WARNING: {} file(s) changed but not staged: {}",
            s.unstaged.len(),
            s.unstaged.join(", ")
        );
    }
    if !s.untracked.is_empty() {
        let _ = writeln!(
            err,
            ">> WARNING: {} untracked file(s): {}",
            s.untracked.len(),
            s.untracked.join(", ")
        );
    }
    if !audit.ok {
        let _ = writeln!(
            err,
            ">> Confirm these don't belong in this PR before committing (the PR #192 guard)."
        );
    }
    stdout_result
}
