//! `ship pr`: open a pull request on GitHub or, for an existing work item, on Azure Repos.

use crate::push::validate_target;
use crate::{
    Platform, ado_parts, azure, default_tags_from_title, detect_kind, git, github, github_owner_repo, http,
    parse_related_ids, parse_tags, parse_work_item, tag_from_branch_prefix,
};
use regex::Regex;
use std::io::{self, Write};
use std::sync::LazyLock;

/// `AB#<...>` placeholder left in the PR template for the work-item id.
static AB_PLACEHOLDER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"AB#<[^>]*>").unwrap());

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
    /// Azure: existing work item to link (default: the number in the branch name).
    pub work_item: Option<String>,
    /// Azure: never create a work item.
    pub no_create_work_item: bool,
    /// Azure: titles of work items to create, one each.
    pub tasks: Vec<String>,
    /// Azure: file with one title per line, appended after `tasks`.
    pub tasks_file: Option<String>,
    /// Azure: assignee of created items; `None` falls back to the env var, then the TS default.
    pub assignee: Option<String>,
    /// Azure: type of created items (empty means `Task`).
    pub work_item_type: String,
    /// Azure: state to move each linked work item to after the PR opens.
    pub transition: Option<String>,
    /// Azure: set "complete linked work items after merging" to false instead of true.
    pub no_complete_transition: bool,
}

/// The task titles: every `--task`, then each trimmed non-blank line of `--tasks-file`.
fn collect_tasks(tasks: &[String], file_text: Option<&str>) -> Vec<String> {
    let mut out = tasks.to_vec();
    if let Some(t) = file_text {
        out.extend(t.lines().map(str::trim).filter(|l| !l.is_empty()).map(str::to_string));
    }
    out
}

/// `--assignee`, else `SHIP_ADO_ASSIGNEE`, else the TS default. An explicit empty value
/// means unassigned.
fn resolve_assignee(flag: Option<&str>) -> String {
    match flag {
        Some(v) => v.to_string(),
        None => std::env::var("SHIP_ADO_ASSIGNEE")
            .ok()
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| "you@example.com".to_string()),
    }
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

    let tasks_text = match a.tasks_file.as_deref().filter(|f| !f.is_empty()) {
        Some(f) => match std::fs::read_to_string(f) {
            Ok(s) => Some(s),
            Err(e) => return fail(&format!("cannot read --tasks-file {f}: {e}"), 1),
        },
        None => None,
    };
    let tasks = collect_tasks(&a.tasks, tasks_text.as_deref());

    let mut tags = parse_tags(&a.tags);
    if tags.is_empty() && !a.no_tag {
        let (derived, line) = derive_tags(title, &source);
        eprintln!("{line}");
        tags = derived;
    }

    match kind {
        Platform::Github => run_github(a, &url, title, &body, &source, &tags),
        Platform::Azure => run_azure(a, &url, title, &body, &source, &tags, &tasks),
        Platform::Unknown => fail(
            &format!(
                "unknown platform for remote '{}' ({url}); set SHIP_PLATFORM=azure|github",
                a.remote
            ),
            1,
        ),
    }
}

/// Azure Repos: verify or create the work items, then create the PR in one call that carries
/// the links, the tags, the resolved reviewers and `--draft`. Then, best-effort, a PATCH sets the
/// PR's completion option and `--transition` moves each linked item (the create drops
/// `completionOptions`). `--related` is a later story and fails fast rather than being dropped.
#[allow(clippy::too_many_lines)]
fn run_azure(
    a: &Args,
    url: &str,
    title: &str,
    body: &str,
    source: &str,
    tags: &[String],
    tasks: &[String],
) -> io::Result<u8> {
    let mut reviewers = parse_tags(&a.reviewers);
    let required = parse_tags(&a.required_reviewers);
    let related = parse_related_ids(&a.related).unwrap_or_default();
    if !related.is_empty() {
        return fail(
            "ship pr: --related is not yet supported on Azure by the binary; use bun scripts/ship-pr.ts",
            1,
        );
    }
    // A PR with no reviewer record leaves no trace that anyone was asked: with no reviewer
    // given, SHIP_ADO_DEFAULT_REVIEWER supplies an optional one.
    if reviewers.is_empty() && required.is_empty() && !a.no_reviewer {
        let fallback = std::env::var("SHIP_ADO_DEFAULT_REVIEWER").unwrap_or_default();
        let fallback = fallback.trim();
        if !fallback.is_empty() {
            reviewers.extend(parse_tags(&[fallback.to_string()]));
            eprintln!(">> NOTE: no reviewer given; using SHIP_ADO_DEFAULT_REVIEWER ({fallback})");
        }
    }

    let Some(parts) = ado_parts(url) else {
        return fail(&format!("could not parse org/project/repo from {url}"), 1);
    };

    let creds = azure::credentials();
    if creds.is_empty() {
        return fail("no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)", 1);
    }
    let mut client = match azure::Client::new(creds, &parts.org_url, &parts.project, &parts.repo) {
        Ok(c) => c,
        Err(e) => return fail(&format!("ship-pr failed: {e}"), 1),
    };

    // The work item: --work-item, else the number in the branch name (skipped when tasks were
    // given, so a number in the branch never preempts them), then verified by a read.
    let wanted = a
        .work_item
        .as_deref()
        .map(str::trim)
        .filter(|w| !w.is_empty())
        .map_or_else(
            || if tasks.is_empty() { parse_work_item(source) } else { String::new() },
            str::to_string,
        );
    let mut linked: Vec<u64> = Vec::new();
    let found = match wanted.parse::<u64>() {
        Ok(id) => match client.work_item_exists(id) {
            Ok(true) => Some(id),
            Ok(false) => None,
            Err(e) => return fail(&format!("ship-pr failed: {e}"), 1),
        },
        Err(_) => None,
    };
    // Created ids print as they come, before `platform=azure`, so a later failure leaves them visible.
    let mut out = Out::default();
    if let Some(id) = found {
        linked.push(id);
        eprintln!(">> linking existing work item {id}");
    } else if !a.no_create_work_item {
        let wi_type = if a.work_item_type.is_empty() { "Task" } else { a.work_item_type.as_str() };
        let assignee = resolve_assignee(a.assignee.as_deref());
        let titles: Vec<&str> = if tasks.is_empty() {
            vec![title]
        } else {
            tasks.iter().map(String::as_str).collect()
        };
        for t in titles {
            let id = match client.create_work_item(wi_type, t, &assignee) {
                Ok(id) => id,
                Err(e) => return out.finish(fail(&format!("ship-pr failed: {e}"), 1)),
            };
            let who = if assignee.is_empty() { "<unassigned>" } else { assignee.as_str() };
            eprintln!(">> created {wi_type} #{id} assigned to {who}: {t}");
            out.line(&format!("work_item_created={id}"));
            linked.push(id);
        }
    } else if !wanted.is_empty() {
        eprintln!(">> WARNING: work item {wanted} not found and --no-create-work-item set; PR will not link it");
    }

    // Back-fill the AB#<...> placeholder so the reference renders as a live link.
    let mut body = body.to_string();
    if !linked.is_empty() && AB_PLACEHOLDER.is_match(&body) {
        let refs: Vec<String> = linked.iter().map(|id| format!("AB#{id}")).collect();
        let refs = refs.join(" ");
        body = AB_PLACEHOLDER.replace_all(&body, regex::NoExpand(&refs)).into_owned();
        eprintln!(">> substituted AB# placeholder -> {refs}");
    }

    // Resolve reviewers (optional first, then required) so they ride in the create call.
    // Best-effort: an unresolved name is warned about and skipped, never blocking the PR.
    let mut resolved: Vec<(String, azure::Reviewer)> = Vec::new();
    // Each UPN is looked up once; one identity appears once, required if either list says so.
    let mut seen: std::collections::HashMap<String, Option<String>> = std::collections::HashMap::new();
    for (list, is_required) in [(&reviewers, false), (&required, true)] {
        for upn in list {
            if !seen.contains_key(upn) {
                let id = match client.resolve_identity(upn) {
                    Ok(id) => Some(id),
                    Err(why) => {
                        eprintln!(">> WARNING: could not resolve reviewer '{upn}' ({why}); skipping");
                        out.line(&format!("reviewer_skipped={upn}"));
                        None
                    }
                };
                seen.insert(upn.clone(), id);
            }
            let Some(id) = seen[upn].clone() else { continue };
            if let Some((_, r)) = resolved.iter_mut().find(|(_, r)| r.id.eq_ignore_ascii_case(&id)) {
                r.is_required |= is_required;
            } else {
                resolved.push((upn.clone(), azure::Reviewer { id, is_required }));
            }
        }
    }
    let refs: Vec<azure::Reviewer> = resolved.iter().map(|(_, r)| r.clone()).collect();

    let payload = azure::create_payload(source, &a.target, title, &body, a.draft, &linked, tags, &refs);
    let pr_id = match client.create_pr(&payload) {
        Ok(id) => id,
        Err(e) => return fail(&format!("ship-pr failed: {e}"), 1),
    };
    out.line("platform=azure");
    out.line(&format!("pr_id={pr_id}"));
    out.line(&format!(
        "pr_url={}/{}/_git/{}/pullrequest/{pr_id}",
        parts.org_url,
        http::encode_uri_component(&parts.project),
        http::encode_uri_component(&parts.repo)
    ));
    if !linked.is_empty() {
        let ids: Vec<String> = linked.iter().map(u64::to_string).collect();
        out.line(&format!("work_items={}", ids.join(" ")));
    }
    // Best-effort from here: the PR exists, so a failed PATCH warns and the run goes on.
    // completionOptions cannot ride in the create (ADO drops it). --no-complete-transition still
    // PATCHes an explicit false rather than skipping: left unset, the Complete dialog falls back
    // to the completer's last choice, which closed work item 1297 behind PR 1347 (TS history).
    let want = !a.no_complete_transition;
    match client.set_complete_transition(pr_id, want) {
        Ok(got) => out.line(&format!(
            "complete_transitions_work_items={}",
            got.map_or("unset".to_string(), |b| b.to_string())
        )),
        Err(e) => {
            eprintln!(">> WARNING: could not set \"complete linked work items\" to {want} on PR {pr_id}: {e}");
            out.line("complete_transitions_work_items=unset");
        }
    }
    if let Some(state) = a.transition.as_deref().map(str::trim).filter(|s| !s.is_empty()) {
        for id in &linked {
            eprintln!(">> transitioning work item {id} -> {state}");
            match client.transition_work_item(*id, state) {
                Ok(()) => out.line(&format!("work_item={id} state={state}")),
                Err(e) => eprintln!(">> WARNING: could not transition work item {id} -> {state}: {e}"),
            }
        }
    }
    for t in tags {
        out.line(&format!("tag_added={t}"));
    }
    for (upn, r) in &resolved {
        out.line(&format!("reviewer_added={upn} required={}", r.is_required));
    }
    out.finish(Ok(0))
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
