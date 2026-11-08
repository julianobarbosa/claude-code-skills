//! `ship pr`: open a pull request. GitHub only in this story; Azure Repos is Story 3.2.

use crate::push::validate_target;
use crate::{
    Platform, default_tags_from_title, detect_kind, git, github, github_owner_repo, parse_related_ids,
    parse_tags, tag_from_branch_prefix,
};
use std::io::{self, Write};

/// Parsed `pr` flags. `title` is checked in [`run`] so the TS message and exit code apply.
#[derive(Debug, Default)]
pub struct Args {
    pub title: Option<String>,
    pub body: String,
    pub body_file: Option<String>,
    pub target: String,
    pub source: Option<String>,
    pub remote: String,
    pub draft: bool,
    pub tags: Vec<String>,
    pub no_tag: bool,
    pub reviewers: Vec<String>,
    pub required_reviewers: Vec<String>,
    pub no_reviewer: bool,
    pub related: Vec<String>,
}

/// The tags a PR gets when the caller named none, with the stderr line to print.
/// Order: Conventional-Commit title, then branch prefix, then `needs-review`.
pub fn derive_tags(title: &str, branch: &str) -> (Vec<String>, String) {
    let from_title = default_tags_from_title(title);
    let prefix = branch.split('/').next().unwrap_or("").to_lowercase();
    if from_title[0] != "needs-review" {
        let note = format!(">> NOTE: no --tag given; derived '{}' from the title", from_title.join(","));
        (from_title, note)
    } else if let Some(t) = tag_from_branch_prefix(&prefix) {
        (
            vec![t.to_string()],
            format!(">> NOTE: no --tag given; derived '{t}' from branch prefix '{prefix}/'"),
        )
    } else {
        (
            from_title,
            format!(">> WARNING: no type in title or branch '{branch}'; tagging 'needs-review'"),
        )
    }
}

fn fail(msg: &str, code: u8) -> io::Result<u8> {
    eprintln!("{msg}");
    Ok(code)
}

/// Open the PR. Exit codes: 0 success (also when reviewers could not be requested),
/// 1 for a platform, token, API or file failure, 2 for bad arguments.
pub fn run(a: &Args) -> io::Result<u8> {
    let Some(title) = a.title.as_deref().filter(|t| !t.is_empty()) else {
        return fail("--title is required", 2);
    };
    if let Err(msg) = validate_target(&a.remote, Some(&a.target)) {
        return fail(&format!("ship: {msg}"), 2);
    }
    let source = match a.source.as_deref().filter(|s| !s.is_empty()) {
        Some(s) => s.to_string(),
        None => git::current_branch()?,
    };
    if let Err(msg) = validate_target(&a.remote, Some(&source)) {
        return fail(&format!("ship: {msg}"), 2);
    }
    if let Err(msg) = parse_related_ids(&a.related) {
        return fail(&msg, 2);
    }

    let url = git::remote_url(&a.remote);
    let override_platform = std::env::var("SHIP_PLATFORM").ok();
    let kind = detect_kind(&url, override_platform.as_deref());

    let body = match a.body_file.as_deref().filter(|f| !f.is_empty()) {
        Some(f) => match std::fs::read_to_string(f) {
            Ok(s) => s,
            Err(e) => return fail(&format!("cannot read --body-file {f}: {e}"), 1),
        },
        None => a.body.clone(),
    };

    let mut tags = parse_tags(&a.tags);
    if tags.is_empty() && !a.no_tag {
        let (derived, line) = derive_tags(title, &source);
        eprintln!("{line}");
        tags = derived;
    }

    match kind {
        Platform::Github => run_github(a, &url, title, &body, &source, &tags),
        Platform::Azure => fail(
            "ship pr: Azure Repos is not yet supported by the binary; use bun scripts/ship-pr.ts",
            1,
        ),
        Platform::Unknown => fail(
            &format!(
                "unknown platform for remote '{}' ({url}); set SHIP_PLATFORM=azure|github",
                a.remote
            ),
            1,
        ),
    }
}

fn run_github(a: &Args, url: &str, title: &str, body: &str, source: &str, tags: &[String]) -> io::Result<u8> {
    if !parse_related_ids(&a.related).unwrap_or_default().is_empty() {
        eprintln!(
            ">> NOTE: --related is Azure-only; on GitHub write \"Refs #<id>\" in the body (unlike \"Closes\", it does not close the issue)"
        );
    }
    let Some((owner, repo)) = github_owner_repo(url) else {
        return fail(&format!("could not parse owner/repo from {url}"), 1);
    };
    let token = github::token(&owner);
    if token.is_empty() {
        return fail("no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`", 1);
    }
    let client = match github::Client::new(token, &owner, &repo) {
        Ok(c) => c,
        Err(e) => return fail(&format!("ship-pr failed: {e}"), 1),
    };

    let payload = github::create_payload(title, source, &a.target, a.draft, body);
    let created = match client.create_pr(&payload) {
        Ok(c) => c,
        Err(e) => return fail(&format!("ship-pr failed: {e}"), 1),
    };
    let mut out = Out::default();
    out.line("platform=github");
    out.line(&format!("pr_url={}", created.html_url));
    out.line(&format!("pr_number={}", created.number));

    if !tags.is_empty() {
        if let Err(e) = client.add_labels(created.number, tags) {
            return out.finish(fail(&format!("ship-pr failed: {e}"), 1));
        }
        for t in tags {
            out.line(&format!("tag_added={t}"));
        }
    }

    // `--no-reviewer` is Azure-only in the TS (it only suppresses SHIP_ADO_DEFAULT_REVIEWER):
    // GitHub always requests the reviewers it was given.
    let reviewers = parse_tags(&[a.reviewers.clone(), a.required_reviewers.clone()].concat());
    if !reviewers.is_empty() {
        if !parse_tags(&a.required_reviewers).is_empty() {
            eprintln!(
                ">> note: GitHub has no per-PR required reviewer (that's branch protection); requesting them as normal reviewers"
            );
        }
        match client.request_reviewers(created.number, &reviewers) {
            Ok(()) => {
                for r in &reviewers {
                    out.line(&format!("reviewer_added={r}"));
                }
            }
            Err(e) => eprintln!(">> WARNING: requesting reviewers failed ({e}); PR is open without them"),
        }
    }
    out.finish(Ok(0))
}

/// Stdout that keeps going after a failed write (a closed pipe): the PR already exists,
/// so the label and reviewer calls must still run. The first write error is reported at the end.
#[derive(Default)]
struct Out {
    err: Option<io::Error>,
}

impl Out {
    fn line(&mut self, s: &str) {
        if self.err.is_none() {
            let mut o = io::stdout().lock();
            if let Err(e) = writeln!(o, "{s}").and_then(|()| o.flush()) {
                self.err = Some(e);
            }
        }
    }

    fn finish(self, code: io::Result<u8>) -> io::Result<u8> {
        match (self.err, code) {
            (Some(e), Ok(0)) => Err(e),
            (_, code) => code,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::derive_tags;

    #[test]
    fn title_wins_over_branch() {
        let (t, note) = derive_tags("docs(finops): x", "fix/y");
        assert_eq!(t, ["docs", "finops"]);
        assert_eq!(note, ">> NOTE: no --tag given; derived 'docs,finops' from the title");
    }

    #[test]
    fn branch_prefix_when_title_untyped() {
        let (t, note) = derive_tags("update x", "Fix/y");
        assert_eq!(t, ["fix"]);
        assert_eq!(note, ">> NOTE: no --tag given; derived 'fix' from branch prefix 'fix/'");
    }

    #[test]
    fn needs_review_fallback_warns() {
        let (t, note) = derive_tags("update x", "y");
        assert_eq!(t, ["needs-review"]);
        assert_eq!(note, ">> WARNING: no type in title or branch 'y'; tagging 'needs-review'");
    }
}
