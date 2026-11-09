//! `ship tag`: add, remove and list the tags of an existing pull request (Azure PR tags,
//! GitHub labels). Adds run first, then removes, then the list.

use crate::push::validate_target;
use crate::{Platform, ado_parts, azure, detect_kind, git, github, github_owner_repo, parse_tags};
use std::io::{self, Write};

/// Parsed `tag` flags, before they are checked.
#[derive(Debug, Default)]
pub struct Args {
    /// The positional PR id.
    pub id: Option<String>,
    /// `--pr <id>`.
    pub pr: Option<String>,
    pub add: Vec<String>,
    pub remove: Vec<String>,
    pub list: bool,
    pub remote: String,
}

/// What to do, once the arguments are checked.
#[derive(Debug, PartialEq, Eq)]
pub struct Plan {
    pub id: u64,
    pub add: Vec<String>,
    pub remove: Vec<String>,
    pub list: bool,
}

/// Check the arguments. `Err` is the message for an exit-2 usage error.
pub fn plan(a: &Args) -> Result<Plan, String> {
    let digits = |s: &str| !s.is_empty() && s.bytes().all(|b| b.is_ascii_digit());
    let id = match (a.id.as_deref(), a.pr.as_deref()) {
        // As in the TS, `--pr` wins over a positional id.
        (_, Some(p)) => p,
        (Some(p), None) if !digits(p) => return Err(format!("unknown arg: {p}")),
        (Some(p), None) => p,
        (None, None) => return Err("a pull request id is required (positional or --pr)".to_string()),
    };
    // Digits only, so the id can never carry a path segment into the API URL.
    let id = Some(id)
        .filter(|s| digits(s))
        .and_then(|s| s.parse::<u64>().ok())
        .ok_or_else(|| format!("invalid pull request id: {id}"))?;
    let add = parse_tags(&a.add);
    let remove = parse_tags(&a.remove);
    // Listing is the default action.
    let list = a.list || (add.is_empty() && remove.is_empty());
    Ok(Plan { id, add, remove, list })
}

/// `.` and `..` would be read as path segments by a dot-normalizing server (`DELETE …/labels`).
fn unsafe_name(n: &str) -> bool {
    n == "." || n == ".."
}

fn fail(msg: &str, code: u8) -> io::Result<u8> {
    eprintln!("{msg}");
    Ok(code)
}

/// Stdout that keeps going after a failed write (a closed pipe): the adds and removes are
/// side effects that must still run. The first write error is reported at the end.
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

/// Run `ship tag`. Exit codes: 0 success (also when a remove failed), 1 for a platform,
/// credential or API failure on an add or the list, 2 for bad arguments.
pub fn run(a: &Args) -> io::Result<u8> {
    let plan = match plan(a) {
        Ok(p) => p,
        Err(msg) => return fail(&msg, 2),
    };
    if let Err(msg) = validate_target(&a.remote, None) {
        return fail(&format!("ship: {msg}"), 2);
    }
    let url = git::remote_url(&a.remote);
    let override_platform = std::env::var("SHIP_PLATFORM").ok();
    match detect_kind(&url, override_platform.as_deref()) {
        Platform::Azure => run_azure(&plan, &url),
        Platform::Github => run_github(&plan, &url),
        Platform::Unknown => fail(
            &format!(
                "unknown platform for remote '{}' ({url}); set SHIP_PLATFORM=azure|github",
                a.remote
            ),
            1,
        ),
    }
}

fn run_azure(p: &Plan, url: &str) -> io::Result<u8> {
    let Some(parts) = ado_parts(url) else {
        return fail(&format!("could not parse org/project/repo from {url}"), 1);
    };
    let creds = azure::credentials();
    if creds.is_empty() {
        return fail("no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)", 1);
    }
    let mut client = match azure::Client::new(creds, &parts.org_url, &parts.project, &parts.repo) {
        Ok(c) => c,
        Err(e) => return fail(&format!("ship-tag failed: {e}"), 1),
    };
    let mut out = Out::default();
    for name in &p.add {
        if let Err(e) = client.add_pr_label(p.id, name) {
            return out.finish(fail(&format!("ship-tag failed: {e}"), 1));
        }
        out.line(&format!("tag_added={name}"));
    }
    for name in &p.remove {
        if unsafe_name(name) {
            eprintln!(">> could not remove '{name}': invalid tag name");
            continue;
        }
        match client.remove_pr_label(p.id, name) {
            Ok(()) => out.line(&format!("tag_removed={name}")),
            Err(e) => eprintln!(">> could not remove '{name}': {e}"),
        }
    }
    if p.list {
        match client.list_pr_labels(p.id) {
            Ok(names) => {
                out.line("platform=azure");
                for n in names {
                    out.line(&n);
                }
            }
            Err(e) => return out.finish(fail(&format!("ship-tag failed: {e}"), 1)),
        }
    }
    out.finish(Ok(0))
}

fn run_github(p: &Plan, url: &str) -> io::Result<u8> {
    let Some((owner, repo)) = github_owner_repo(url) else {
        return fail(&format!("could not parse owner/repo from {url}"), 1);
    };
    let token = github::token(&owner);
    if token.is_empty() {
        return fail("no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`", 1);
    }
    let client = match github::Client::new(token, &owner, &repo) {
        Ok(c) => c,
        Err(e) => return fail(&format!("ship-tag failed: {e}"), 1),
    };
    let mut out = Out::default();
    // One call carries every tag; GitHub creates a label that does not exist yet.
    if !p.add.is_empty() {
        if let Err(e) = client.add_labels(p.id, &p.add) {
            return out.finish(fail(&format!("ship-tag failed: {e}"), 1));
        }
        for name in &p.add {
            out.line(&format!("tag_added={name}"));
        }
    }
    for name in &p.remove {
        if unsafe_name(name) {
            eprintln!(">> could not remove '{name}': invalid tag name");
            continue;
        }
        match client.remove_label(p.id, name) {
            Ok(()) => out.line(&format!("tag_removed={name}")),
            Err(e) => eprintln!(">> could not remove '{name}': {e}"),
        }
    }
    if p.list {
        match client.list_labels(p.id) {
            Ok(names) => {
                out.line("platform=github");
                for n in names {
                    out.line(&n);
                }
            }
            Err(e) => return out.finish(fail(&format!("ship-tag failed: {e}"), 1)),
        }
    }
    out.finish(Ok(0))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args() -> Args {
        Args { remote: "origin".into(), ..Args::default() }
    }

    fn v(s: &[&str]) -> Vec<String> {
        s.iter().map(|x| (*x).to_string()).collect()
    }

    #[test]
    fn positional_or_flag_id() {
        let p = plan(&Args { id: Some("9".into()), ..args() }).unwrap();
        assert_eq!(p, Plan { id: 9, add: vec![], remove: vec![], list: true });
        let p = plan(&Args { pr: Some("12".into()), ..args() }).unwrap();
        assert_eq!(p.id, 12);
    }

    #[test]
    fn pr_flag_wins_over_a_positional_id() {
        let p = plan(&Args { id: Some("7".into()), pr: Some("5".into()), ..args() }).unwrap();
        assert_eq!(p.id, 5);
        assert!(plan(&Args { id: Some("7".into()), pr: Some("x".into()), ..args() }).is_err());
    }

    #[test]
    fn missing_or_bad_id_is_a_usage_error() {
        assert_eq!(plan(&args()).unwrap_err(), "a pull request id is required (positional or --pr)");
        assert_eq!(plan(&Args { id: Some("abc".into()), ..args() }).unwrap_err(), "unknown arg: abc");
        assert_eq!(plan(&Args { id: Some("".into()), ..args() }).unwrap_err(), "unknown arg: ");
        assert_eq!(
            plan(&Args { pr: Some("x/../1".into()), ..args() }).unwrap_err(),
            "invalid pull request id: x/../1"
        );
        assert!(plan(&Args { pr: Some("-1".into()), ..args() }).is_err());
        assert!(plan(&Args { pr: Some("99999999999999999999999".into()), ..args() }).is_err());
    }

    #[test]
    fn add_and_remove_are_split_trimmed_and_deduped() {
        let p = plan(&Args {
            id: Some("9".into()),
            add: v(&["a, b", "a", " "]),
            remove: v(&["x,y", "x"]),
            ..args()
        })
        .unwrap();
        assert_eq!(p.add, ["a", "b"]);
        assert_eq!(p.remove, ["x", "y"]);
        assert!(!p.list);
    }

    #[test]
    fn list_is_the_default_only_when_nothing_changes() {
        // Blank values count as nothing to add.
        assert!(plan(&Args { id: Some("9".into()), add: v(&[" , "]), ..args() }).unwrap().list);
        assert!(plan(&Args { id: Some("9".into()), add: v(&["a"]), list: true, ..args() }).unwrap().list);
        assert!(!plan(&Args { id: Some("9".into()), remove: v(&["a"]), ..args() }).unwrap().list);
    }
}
