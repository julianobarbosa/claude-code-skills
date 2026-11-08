//! `ship detect`: print the delivery platform and coordinates as key=value lines.

use crate::{Platform, ado_parts, detect_kind, git, parse_work_item};
use std::io::{self, Write};

/// Print the detect output for `remote`. Prints platform/remote/url before the
/// branch lookup, so a failing lookup leaves the same partial output as the TS.
/// Writes go through a locked stdout and return errors (e.g. a closed pipe)
/// instead of panicking.
pub fn run(remote: &str) -> io::Result<()> {
    let url = git::remote_url(remote);
    let override_platform = std::env::var("SHIP_PLATFORM").ok();
    let kind = detect_kind(&url, override_platform.as_deref());

    let mut out = io::stdout().lock();
    writeln!(out, "platform={}", kind.as_str())?;
    writeln!(out, "remote={remote}")?;
    writeln!(out, "url={url}")?;
    let branch = git::current_branch()?;
    writeln!(out, "branch={branch}")?;

    if kind == Platform::Azure
        && let Some(p) = ado_parts(&url)
    {
        writeln!(out, "org_url={}", p.org_url)?;
        writeln!(out, "project={}", p.project)?;
        writeln!(out, "repo={}", p.repo)?;
    }

    let wi = parse_work_item(&branch);
    if !wi.is_empty() {
        writeln!(out, "work_item={wi}")?;
    }
    out.flush()
}
