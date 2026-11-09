//! Integration tests for `ship pr` on GitHub: real binary, scratch repos, a mock
//! GitHub API on 127.0.0.1 (std `TcpListener`) and a stub `gh` first on PATH.
//! No network, no bun.

use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

const TOKEN: &str = "SECRET-TOKEN-123";
static COUNTER: AtomicUsize = AtomicUsize::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-pr-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn git(dir: &Path, args: &[&str]) {
    let st = Command::new("git")
        .current_dir(dir)
        .args(args)
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .status()
        .unwrap();
    assert!(st.success(), "git {args:?} failed");
}

/// Repo on branch `branch` with one commit and `origin` set to `url` (never contacted).
fn repo(tag: &str, branch: &str, url: &str) -> Scratch {
    let r = Scratch::new(tag);
    git(&r.0, &["init", "-q", "-b", branch]);
    std::fs::write(r.0.join("f.txt"), "x\n").unwrap();
    git(&r.0, &["add", "f.txt"]);
    git(
        &r.0,
        &["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"],
    );
    git(&r.0, &["remote", "add", "origin", url]);
    r
}

const GH_URL: &str = "git@github.com:acme/widgets.git";

#[derive(Debug, Clone)]
struct Req {
    method: String,
    path: String,
    headers: HashMap<String, String>,
    body: String,
}

impl Req {
    fn json(&self) -> serde_json::Value {
        serde_json::from_str(&self.body).unwrap()
    }
}

/// A canned reply: status, extra headers, JSON body.
type Reply = (u16, Vec<(String, String)>, String);

struct Mock {
    base: String,
    reqs: Arc<Mutex<Vec<Req>>>,
}

impl Mock {
    /// `overrides` maps a path suffix (e.g. `/labels`) to a reply; everything else
    /// gets the happy-path reply for its endpoint.
    fn start(overrides: Vec<(&'static str, Reply)>) -> Mock {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let base = format!("http://{}", listener.local_addr().unwrap());
        let reqs = Arc::new(Mutex::new(Vec::new()));
        let log = Arc::clone(&reqs);
        thread::spawn(move || {
            for stream in listener.incoming() {
                let Ok(stream) = stream else { break };
                if let Some(req) = read_request(stream.try_clone().unwrap()) {
                    let reply = overrides
                        .iter()
                        .find(|(suffix, _)| req.path.ends_with(suffix))
                        .map(|(_, r)| r.clone())
                        .unwrap_or_else(|| happy(&req.path));
                    log.lock().unwrap().push(req);
                    write_reply(stream, &reply);
                }
            }
        });
        Mock { base, reqs }
    }

    fn requests(&self) -> Vec<Req> {
        self.reqs.lock().unwrap().clone()
    }
}

fn happy(path: &str) -> Reply {
    if path.ends_with("/pulls") {
        (
            201,
            vec![],
            r#"{"html_url":"https://github.com/acme/widgets/pull/7","number":7}"#.into(),
        )
    } else if path.ends_with("/labels") {
        (200, vec![], r#"[{"name":"x"}]"#.into())
    } else {
        (201, vec![], "{}".into())
    }
}

fn read_request(mut s: TcpStream) -> Option<Req> {
    s.set_read_timeout(Some(Duration::from_secs(10))).ok()?;
    let mut buf = Vec::new();
    let mut chunk = [0u8; 4096];
    let head_end = loop {
        let n = s.read(&mut chunk).ok()?;
        if n == 0 {
            return None;
        }
        buf.extend_from_slice(&chunk[..n]);
        if let Some(i) = buf.windows(4).position(|w| w == b"\r\n\r\n") {
            break i + 4;
        }
    };
    let head = String::from_utf8_lossy(&buf[..head_end]).into_owned();
    let mut lines = head.split("\r\n");
    let mut first = lines.next()?.split(' ');
    let method = first.next()?.to_string();
    let path = first.next()?.to_string();
    let headers: HashMap<String, String> = lines
        .filter_map(|l| l.split_once(':'))
        .map(|(k, v)| (k.trim().to_lowercase(), v.trim().to_string()))
        .collect();
    let want: usize = headers.get("content-length").and_then(|v| v.parse().ok()).unwrap_or(0);
    while buf.len() < head_end + want {
        let n = s.read(&mut chunk).ok()?;
        if n == 0 {
            break;
        }
        buf.extend_from_slice(&chunk[..n]);
    }
    let body = String::from_utf8_lossy(&buf[head_end..]).into_owned();
    Some(Req { method, path, headers, body })
}

fn write_reply(mut s: TcpStream, (status, headers, body): &Reply) {
    let mut out = format!("HTTP/1.1 {status} X\r\nContent-Type: application/json\r\nConnection: close\r\n");
    for (k, v) in headers {
        out.push_str(&format!("{k}: {v}\r\n"));
    }
    out.push_str(&format!("Content-Length: {}\r\n\r\n{body}", body.len()));
    let _ = s.write_all(out.as_bytes());
}

fn err(status: u16, msg: &str) -> Reply {
    (status, vec![], format!(r#"{{"message":"{msg}"}}"#))
}

/// A `gh` stub on PATH. `auth token -u <owner>` prints `$STUB_OWNED`, plain
/// `auth token` prints `$STUB_ACTIVE`; each call is appended to `$STUB_LOG`.
fn gh_stub(dir: &Path) -> PathBuf {
    let bin = dir.join("bin");
    std::fs::create_dir_all(&bin).unwrap();
    let p = bin.join("gh");
    std::fs::write(
        &p,
        "#!/bin/sh\necho \"$*\" >> \"$STUB_LOG\"\n\
         if [ \"$3\" = \"-u\" ]; then [ -n \"$STUB_OWNED\" ] && echo \"$STUB_OWNED\" || exit 1\n\
         else [ -n \"$STUB_ACTIVE\" ] && echo \"$STUB_ACTIVE\" || exit 1; fi\n",
    )
    .unwrap();
    std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o755)).unwrap();
    bin
}

struct Run {
    out: Output,
    gh_log: String,
}

impl Run {
    fn stdout(&self) -> String {
        String::from_utf8_lossy(&self.out.stdout).into_owned()
    }
    fn stderr(&self) -> String {
        String::from_utf8_lossy(&self.out.stderr).into_owned()
    }
    fn code(&self) -> i32 {
        self.out.status.code().unwrap()
    }
}

/// Run `ship pr <args>` in `dir` with the mock API. `env_token` sets GH_TOKEN;
/// `owned`/`active` feed the stub `gh`.
fn ship_pr(
    dir: &Scratch,
    api: Option<&str>,
    env_token: Option<&str>,
    owned: &str,
    active: &str,
    args: &[&str],
) -> Run {
    ship_pr_env(dir, api, env_token, owned, active, &[], args)
}

/// [`ship_pr`] plus extra environment variables (e.g. `GITHUB_TOKEN`, `SHIP_PLATFORM`).
fn ship_pr_env(
    dir: &Scratch,
    api: Option<&str>,
    env_token: Option<&str>,
    owned: &str,
    active: &str,
    extra_env: &[(&str, &str)],
    args: &[&str],
) -> Run {
    let log = dir.0.join("gh.log");
    let mut c = base_command(dir, owned, active, args);
    if let Some(a) = api {
        c.env("SHIP_GITHUB_API_URL", a);
    }
    if let Some(t) = env_token {
        c.env("GH_TOKEN", t);
    }
    c.envs(extra_env.iter().copied());
    let out = c.output().unwrap();
    let gh_log = std::fs::read_to_string(&log).unwrap_or_default();
    Run { out, gh_log }
}

/// Hermetic `ship pr` command: stub `gh` first on PATH, no inherited platform or token env.
fn base_command(dir: &Scratch, owned: &str, active: &str, args: &[&str]) -> Command {
    let stubs = gh_stub(&dir.0);
    let log = dir.0.join("gh.log");
    let path = format!("{}:{}", stubs.display(), std::env::var("PATH").unwrap());
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    c.current_dir(&dir.0)
        .arg("pr")
        .args(args)
        .env("PATH", path)
        .env("STUB_LOG", &log)
        .env("STUB_OWNED", owned)
        .env("STUB_ACTIVE", active)
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env_remove("SHIP_PLATFORM")
        .env_remove("GH_TOKEN")
        .env_remove("GITHUB_TOKEN")
        .env_remove("SHIP_GITHUB_API_URL")
        .stdin(Stdio::null());
    c
}

/// The common case: token in the env, happy-path mock.
fn run_ok(dir: &Scratch, mock: &Mock, args: &[&str]) -> Run {
    ship_pr(dir, Some(&mock.base), Some(TOKEN), "", "", args)
}

fn paths(m: &Mock) -> Vec<String> {
    m.requests().iter().map(|r| format!("{} {}", r.method, r.path)).collect()
}

#[test]
fn typed_title_labels_from_title_and_prints_every_line() {
    let r = repo("typed", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "docs(finops): x"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        "platform=github\npr_url=https://github.com/acme/widgets/pull/7\npr_number=7\ntag_added=docs\ntag_added=finops\n"
    );
    assert!(run.stderr().contains(">> NOTE: no --tag given; derived 'docs,finops' from the title"));
    assert_eq!(
        paths(&m),
        ["POST /repos/acme/widgets/pulls", "POST /repos/acme/widgets/issues/7/labels"]
    );
    let reqs = m.requests();
    assert_eq!(reqs[0].json(), serde_json::json!({"title":"docs(finops): x","head":"feat/x","base":"main","draft":false}));
    assert_eq!(reqs[1].json(), serde_json::json!({"labels":["docs","finops"]}));
}

#[test]
fn branch_prefix_supplies_the_label() {
    let r = repo("prefix", "fix/y", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "update x"]);
    assert_eq!(run.code(), 0);
    assert!(run.stdout().ends_with("tag_added=fix\n"));
    assert!(run.stderr().contains(">> NOTE: no --tag given; derived 'fix' from branch prefix 'fix/'"));
    assert_eq!(m.requests()[1].json(), serde_json::json!({"labels":["fix"]}));
}

#[test]
fn untyped_everything_falls_back_to_needs_review_with_warning() {
    let r = repo("fallback", "y", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "update x"]);
    assert_eq!(run.code(), 0);
    assert!(run.stdout().ends_with("tag_added=needs-review\n"));
    assert!(run.stderr().contains(">> WARNING: no type in title or branch 'y'; tagging 'needs-review'"));
}

#[test]
fn explicit_tags_are_split_and_deduped_and_print_no_note() {
    let r = repo("explicit", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "docs: x", "--tag", "hotfix, wip,hotfix"]);
    assert_eq!(run.code(), 0);
    assert!(run.stdout().ends_with("tag_added=hotfix\ntag_added=wip\n"));
    assert!(!run.stderr().contains("NOTE"));
    assert_eq!(m.requests()[1].json(), serde_json::json!({"labels":["hotfix","wip"]}));
}

#[test]
fn no_tag_makes_no_labels_call() {
    let r = repo("notag", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "docs: x", "--no-tag"]);
    assert_eq!(run.code(), 0);
    assert_eq!(run.stdout(), "platform=github\npr_url=https://github.com/acme/widgets/pull/7\npr_number=7\n");
    assert_eq!(paths(&m), ["POST /repos/acme/widgets/pulls"]);
}

#[test]
fn reviewers_merge_dedupe_one_call_and_required_note() {
    let r = repo("rev", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(
        &r,
        &m,
        &["--title", "x", "--no-tag", "--reviewer", "a,b", "--required-reviewer", "c,a"],
    );
    assert_eq!(run.code(), 0);
    assert!(run.stdout().ends_with("reviewer_added=a\nreviewer_added=b\nreviewer_added=c\n"));
    assert!(run.stderr().contains(
        ">> note: GitHub has no per-PR required reviewer (that's branch protection); requesting them as normal reviewers"
    ));
    let reqs = m.requests();
    assert_eq!(reqs.len(), 2);
    assert_eq!(reqs[1].path, "/repos/acme/widgets/pulls/7/requested_reviewers");
    assert_eq!(reqs[1].json(), serde_json::json!({"reviewers":["a","b","c"]}));
}

#[test]
fn optional_only_reviewers_print_no_required_note() {
    let r = repo("revopt", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--reviewer", "a"]);
    assert_eq!(run.code(), 0);
    assert!(!run.stderr().contains("required reviewer"));
}

#[test]
fn reviewer_failure_warns_and_still_exits_zero() {
    let r = repo("revfail", "feat/x", GH_URL);
    let m = Mock::start(vec![("/requested_reviewers", err(422, "Reviews may only be requested from collaborators"))]);
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--reviewer", "ghost"]);
    assert_eq!(run.code(), 0);
    assert!(!run.stdout().contains("reviewer_added"));
    assert!(run.stderr().contains(">> WARNING: requesting reviewers failed (HTTP 422: Reviews may only be requested from collaborators); PR is open without them"));
}

#[test]
fn draft_literal_title_and_body_file_win_verbatim() {
    let r = repo("draft", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    std::fs::write(r.0.join("body.md"), "line 1 & more\n\n- `code` $(not run)\n").unwrap();
    let run = run_ok(
        &r,
        &m,
        &["--title", "a & b", "--body", "ignored", "--body-file", "body.md", "--draft", "--no-tag", "--target", "develop"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let j = m.requests()[0].json();
    assert_eq!(j["title"], "a & b");
    assert_eq!(j["body"], "line 1 & more\n\n- `code` $(not run)\n");
    assert_eq!(j["draft"], true);
    assert_eq!(j["base"], "develop");
}

#[test]
fn body_flag_is_sent_and_empty_body_is_omitted() {
    let r = repo("body", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    run_ok(&r, &m, &["--title", "x", "--no-tag", "--body", "hello"]);
    assert_eq!(m.requests()[0].json()["body"], "hello");
    let m2 = Mock::start(vec![]);
    run_ok(&r, &m2, &["--title", "x", "--no-tag"]);
    assert!(m2.requests()[0].json().get("body").is_none());
}

#[test]
fn source_flag_overrides_the_current_branch() {
    let r = repo("source", "main", GH_URL);
    let m = Mock::start(vec![]);
    run_ok(&r, &m, &["--title", "x", "--no-tag", "--source", "topic/z"]);
    assert_eq!(m.requests()[0].json()["head"], "topic/z");
}

#[test]
fn token_env_wins_over_gh() {
    let r = repo("tokenv", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr(&r, Some(&m.base), Some("ENV-TOKEN"), "OWNED", "ACTIVE", &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0);
    assert_eq!(m.requests()[0].headers["authorization"], "Bearer ENV-TOKEN");
    assert_eq!(run.gh_log, "");
}

#[test]
fn github_token_env_is_the_second_choice() {
    let r = repo("ghtok", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr_env(
        &r,
        Some(&m.base),
        None,
        "OWNED",
        "ACTIVE",
        &[("GITHUB_TOKEN", "GHT")],
        &["--title", "x", "--no-tag"],
    );
    assert_eq!(run.code(), 0);
    assert_eq!(m.requests()[0].headers["authorization"], "Bearer GHT");
    assert_eq!(run.gh_log, "", "gh must not be consulted when an env token is set");
}

#[test]
fn gh_token_beats_github_token() {
    let r = repo("both", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr_env(
        &r,
        Some(&m.base),
        Some("FIRST"),
        "OWNED",
        "ACTIVE",
        &[("GITHUB_TOKEN", "SECOND")],
        &["--title", "x", "--no-tag"],
    );
    assert_eq!(run.code(), 0);
    assert_eq!(m.requests()[0].headers["authorization"], "Bearer FIRST");
    assert_eq!(run.gh_log, "");
}

#[test]
fn gh_owner_token_beats_active_account() {
    let r = repo("owned", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr(&r, Some(&m.base), None, "OWNED-TOKEN", "ACTIVE-TOKEN", &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0);
    assert_eq!(m.requests()[0].headers["authorization"], "Bearer OWNED-TOKEN");
    assert_eq!(run.gh_log.trim(), "auth token -u acme");
}

#[test]
fn active_gh_account_is_the_last_resort() {
    let r = repo("active", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr(&r, Some(&m.base), None, "", "ACTIVE-TOKEN", &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0);
    assert_eq!(m.requests()[0].headers["authorization"], "Bearer ACTIVE-TOKEN");
    assert_eq!(run.gh_log.trim(), "auth token -u acme\nauth token");
}

#[test]
fn no_token_anywhere_exits_one_without_a_request() {
    let r = repo("notoken", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr(&r, Some(&m.base), None, "", "", &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`"));
    assert!(m.requests().is_empty());
}

#[test]
fn request_carries_the_documented_headers() {
    let r = repo("headers", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    run_ok(&r, &m, &["--title", "x", "--no-tag"]);
    let h = &m.requests()[0].headers;
    assert_eq!(h["authorization"], format!("Bearer {TOKEN}"));
    assert_eq!(h["accept"], "application/vnd.github+json");
    assert!(h.contains_key("x-github-api-version"));
    assert_eq!(h["user-agent"], concat!("ship/", env!("CARGO_PKG_VERSION")));
    assert!(h["content-type"].starts_with("application/json"));
}

#[test]
fn token_appears_only_in_the_authorization_header() {
    let r = repo("hygiene", "feat/x", GH_URL);
    let m = Mock::start(vec![("/labels", err(500, "boom"))]);
    let run = run_ok(&r, &m, &["--title", "x", "--reviewer", "a"]);
    assert!(!run.stdout().contains(TOKEN));
    assert!(!run.stderr().contains(TOKEN));
    for req in m.requests() {
        assert!(!req.path.contains(TOKEN));
        assert!(!req.body.contains(TOKEN));
        for (k, v) in &req.headers {
            assert_eq!(v.contains(TOKEN), k == "authorization", "header {k}");
        }
    }
}

#[test]
fn create_failure_prints_no_pr_lines_and_exits_one() {
    let r = repo("create422", "feat/x", GH_URL);
    let m = Mock::start(vec![("/pulls", err(422, "Validation Failed"))]);
    let run = run_ok(&r, &m, &["--title", "x"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("ship-pr failed: HTTP 422: Validation Failed"));
    assert_eq!(m.requests().len(), 1);
}

#[test]
fn create_404_exits_one() {
    let r = repo("create404", "feat/x", GH_URL);
    let m = Mock::start(vec![("/pulls", err(404, "Not Found"))]);
    let run = run_ok(&r, &m, &["--title", "x"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("ship-pr failed: HTTP 404: Not Found"));
}

#[test]
fn label_failure_exits_one_after_the_pr_lines() {
    let r = repo("label500", "feat/x", GH_URL);
    let m = Mock::start(vec![("/labels", err(500, "boom"))]);
    let run = run_ok(&r, &m, &["--title", "docs: x", "--reviewer", "a"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "platform=github\npr_url=https://github.com/acme/widgets/pull/7\npr_number=7\n");
    assert!(run.stderr().contains("ship-pr failed: HTTP 500: boom"));
    // The TS aborts here: reviewers are never requested.
    assert_eq!(m.requests().len(), 2);
}

#[test]
fn redirects_are_not_followed_so_the_token_stays_on_one_host() {
    let r = repo("redirect", "feat/x", GH_URL);
    let other = Mock::start(vec![]);
    let m = Mock::start(vec![(
        "/pulls",
        (307, vec![("Location".into(), format!("{}/stolen", other.base))], String::new()),
    )]);
    let run = run_ok(&r, &m, &["--title", "x"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("ship-pr failed: HTTP 307"));
    assert!(other.requests().is_empty(), "redirect target was contacted");
}

#[test]
fn unknown_remote_exits_one_naming_the_override() {
    let r = repo("unknown", "feat/x", "https://example.com/x.git");
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "x"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains(
        "unknown platform for remote 'origin' (https://example.com/x.git); set SHIP_PLATFORM=azure|github"
    ));
    assert!(m.requests().is_empty());
}

#[test]
fn ship_platform_github_still_needs_a_parseable_owner_repo() {
    let r = repo("forced", "feat/x", "git@example.com:acme/widgets.git");
    let m = Mock::start(vec![]);
    let run = ship_pr_env(
        &r,
        Some(&m.base),
        Some(TOKEN),
        "",
        "",
        &[("SHIP_PLATFORM", "github")],
        &["--title", "x", "--no-tag"],
    );
    // The URL has no "github" host, so owner/repo cannot be parsed: exit 1, nothing sent.
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("could not parse owner/repo from git@example.com:acme/widgets.git"));
    assert!(m.requests().is_empty());
}

#[test]
fn missing_title_exits_two() {
    let r = repo("notitle", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &[]);
    assert_eq!(run.code(), 2);
    assert!(run.stderr().contains("--title is required"));
    assert!(m.requests().is_empty());
}

#[test]
fn unsafe_refs_exit_two_before_any_request() {
    let r = repo("refs", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    for args in [
        vec!["--title", "x", "--source", "+evil"],
        vec!["--title", "x", "--target", "a:b"],
        vec!["--title", "x", "--remote", "--upload-pack=x"],
    ] {
        let run = run_ok(&r, &m, &args);
        assert_eq!(run.code(), 2, "{args:?}: {}", run.stderr());
    }
    assert!(m.requests().is_empty());
}

#[test]
fn related_prints_the_azure_only_note_and_still_opens_the_pr() {
    let r = repo("related", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--related", "12,AB#13"]);
    assert_eq!(run.code(), 0);
    assert!(run.stderr().contains(
        ">> NOTE: --related is Azure-only; on GitHub write \"Refs #<id>\" in the body (unlike \"Closes\", it does not close the issue)"
    ));
    let bad = run_ok(&r, &m, &["--title", "x", "--related", "abc"]);
    assert_eq!(bad.code(), 2);
}

#[test]
fn help_exits_zero() {
    let out = Command::new(env!("CARGO_BIN_EXE_ship")).args(["pr", "--help"]).output().unwrap();
    assert_eq!(out.status.code(), Some(0));
    let text = String::from_utf8_lossy(&out.stdout);
    for flag in ["--title", "--body-file", "--draft", "--tag", "--no-tag", "--required-reviewer", "--no-reviewer"] {
        assert!(text.contains(flag), "{flag} missing from help");
    }
}

#[test]
fn http_base_on_a_public_host_is_refused_without_a_request() {
    let r = repo("cleartext", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = ship_pr(&r, Some("http://example.com"), Some(TOKEN), "", "", &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("refusing SHIP_GITHUB_API_URL 'http://example.com'"));
    assert!(!run.stderr().contains(TOKEN));
    assert!(m.requests().is_empty());
}

#[test]
fn error_details_are_appended_to_the_failure_text() {
    let r = repo("errors", "feat/x", GH_URL);
    let body = r#"{"message":"Validation Failed","errors":[{"message":"A pull request already exists for acme:feat/x."},"x"]}"#;
    let m = Mock::start(vec![("/pulls", (422, vec![], body.to_string()))]);
    let run = run_ok(&r, &m, &["--title", "x"]);
    assert_eq!(run.code(), 1);
    assert!(
        run.stderr().ends_with(
            "ship-pr failed: HTTP 422: Validation Failed (A pull request already exists for acme:feat/x.; x)\n"
        ),
        "{}",
        run.stderr()
    );
}

#[test]
fn missing_body_file_exits_one_without_a_request() {
    let r = repo("nobodyfile", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let run = run_ok(&r, &m, &["--title", "x", "--body-file", "missing.md"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("cannot read --body-file missing.md"));
    assert!(m.requests().is_empty());
}

#[test]
fn closed_stdout_still_applies_labels_and_reviewers() {
    let r = repo("pipe", "feat/x", GH_URL);
    let m = Mock::start(vec![]);
    let mut c = base_command(&r, "", "", &["--title", "docs: x", "--reviewer", "a"]);
    c.env("SHIP_GITHUB_API_URL", &m.base).env("GH_TOKEN", TOKEN);
    c.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = c.spawn().unwrap();
    drop(child.stdout.take()); // the reader is gone before ship prints anything
    let out = child.wait_with_output().unwrap();
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(
        paths(&m),
        [
            "POST /repos/acme/widgets/pulls",
            "POST /repos/acme/widgets/issues/7/labels",
            "POST /repos/acme/widgets/pulls/7/requested_reviewers"
        ]
    );
}

#[test]
fn transition_flags_are_ignored_on_github() {
    let r = repo("transition", "feat/x", GH_URL);
    let plain = Mock::start(vec![]);
    let base = run_ok(&r, &plain, &["--title", "x", "--tag", "a"]);
    let flagged = Mock::start(vec![]);
    let with = run_ok(
        &r,
        &flagged,
        &[
            "--title",
            "x",
            "--tag",
            "a",
            "--transition",
            "Resolved",
            "--no-complete-transition",
        ],
    );
    assert_eq!(with.code(), 0, "{}", with.stderr());
    assert_eq!(with.stdout(), base.stdout());
    assert_eq!(with.stderr(), base.stderr());
    assert_eq!(paths(&flagged), paths(&plain));
    assert!(
        !with.stdout().contains("complete_transitions_work_items"),
        "{}",
        with.stdout()
    );
}
