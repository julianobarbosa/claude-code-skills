//! `ship snapshot`: save an annotated, self-describing tag on HEAD.

use crate::push::is_unsafe_ref;
use crate::{detect_kind, git};
use std::io::{self, Write};

/// `date` format for the default tag name: minute-granular, or one per day.
pub fn date_format(daily: bool) -> &'static str {
    if daily { "+v%Y.%m.%d" } else { "+v%Y.%m.%d-%H%M" }
}

/// First tag-message paragraph: names the tag, branch and commit so the tag
/// describes itself even without any `-m`.
pub fn subject(name: &str, branch: &str, head: &str) -> String {
    format!("Snapshot {name} — {branch} @ {head}")
}

/// Reject a `--name` that git would read as an option or refspec, or that is not a
/// valid tag ref. `check-ref-format` accepts a leading `-`/`+`, so both checks run.
fn validate_name(name: &str) -> Result<(), String> {
    if is_unsafe_ref(name) {
        return Err(format!(
            "invalid tag name '{name}': must not start with '-' or '+' or contain ':'"
        ));
    }
    if name == "HEAD" || !git::valid_tag_name(name) {
        return Err(format!("invalid tag name '{name}': rejected by git check-ref-format"));
    }
    Ok(())
}

/// Create the tag (and push it with `push`). Returns the exit code: 0 on success,
/// 1 when `--push` fails (the local tag stays), 2 when there is nothing to
/// snapshot or the name is invalid, 3 when the tag already exists.
pub fn run(messages: &[String], daily: bool, name: Option<&str>, push: bool) -> io::Result<u8> {
    let Ok(head) = git::short_head() else {
        eprintln!("not a git repo, or no commits yet — nothing to snapshot");
        return Ok(2);
    };
    let branch = git::current_branch()?;

    let name = match name.filter(|n| !n.is_empty()) {
        Some(n) => {
            if let Err(msg) = validate_name(n) {
                eprintln!("ship: {msg}");
                return Ok(2);
            }
            n.to_string()
        }
        None => git::date(date_format(daily))?,
    };

    if git::tag_exists(&name) {
        eprintln!(
            "tag '{name}' already exists. Use --name <other>, or drop --daily for minute granularity."
        );
        return Ok(3);
    }

    let mut paragraphs = vec![subject(&name, &branch, &head)];
    paragraphs.extend(messages.iter().cloned());
    git::create_tag(&name, &paragraphs)?;
    eprintln!(">> created annotated tag {name} -> {head} ({branch})");

    let mut pushed = "no";
    if push {
        let remote = "origin";
        let url = git::remote_url(remote);
        let override_platform = std::env::var("SHIP_PLATFORM").ok();
        let kind = detect_kind(&url, override_platform.as_deref());
        eprintln!(">> pushing tag {name} -> {remote} ({})", kind.as_str());
        pushed = match git::push_with_auth(kind, remote, &[&format!("refs/tags/{name}")]) {
            Some(git::PushMode::OauthBearer) => "yes-oauth-bearer",
            Some(git::PushMode::Normal) => "yes",
            None => {
                eprintln!("tag '{name}' created locally, but push failed");
                return Ok(1);
            }
        };
    }

    let mut out = io::stdout().lock();
    writeln!(out, "tag={name}")?;
    writeln!(out, "commit={head}")?;
    writeln!(out, "branch={branch}")?;
    writeln!(out, "pushed={pushed}")?;
    out.flush()?;
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn date_format_is_minute_granular_unless_daily() {
        assert_eq!(date_format(false), "+v%Y.%m.%d-%H%M");
        assert_eq!(date_format(true), "+v%Y.%m.%d");
    }

    #[test]
    fn subject_names_tag_branch_and_commit() {
        assert_eq!(subject("v1", "main", "abc1234"), "Snapshot v1 — main @ abc1234");
    }

    #[test]
    fn messages_become_one_m_pair_each_in_order_and_verbatim() {
        let msgs = ["subj".to_string(), "why\n\nmulti".to_string(), "-x '$(y)'".to_string()];
        assert_eq!(
            git::tag_args("t", &msgs),
            ["tag", "-a", "t", "-m", "subj", "-m", "why\n\nmulti", "-m", "-x '$(y)'"]
        );
        assert!(!git::tag_args("t", &msgs).iter().any(|a| a == "-f"));
    }
}
