//! Integration tests for `ship pr` on Azure Repos: real binary, scratch repos, a mock
//! Azure DevOps API on 127.0.0.1 (std `TcpListener`) and a stub `az` first on PATH.
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
const PAT: &str = "SECRET-PAT-456";
/// `base64(":" + PAT)`.
const PAT_B64: &str = "OlNFQ1JFVC1QQVQtNDU2";
const ADO_URL: &str = "https://acme@dev.azure.com/acme/My%20Project/_git/widgets";
const PR_URL: &str = "https://dev.azure.com/acme/My%20Project/_git/widgets/pullrequest/9";
static COUNTER: AtomicUsize = AtomicUsize::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-az-{}-{n}-{tag}", std::process::id()));
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

/// Repo on branch `branch` with one commit and `origin` set to the Azure URL (never contacted).
fn repo(tag: &str, branch: &str) -> Scratch {
    let r = Scratch::new(tag);
    git(&r.0, &["init", "-q", "-b", branch]);
    std::fs::write(r.0.join("f.txt"), "x\n").unwrap();
    git(&r.0, &["add", "f.txt"]);
    git(&r.0, &["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"]);
    git(&r.0, &["remote", "add", "origin", ADO_URL]);
    r
}

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
    fn auth(&self) -> &str {
        self.headers.get("authorization").map_or("", String::as_str)
    }
}

/// A canned reply: status, extra headers, body.
type Reply = (u16, Vec<(String, String)>, String);

fn json_reply(status: u16, body: &str) -> Reply {
    (status, vec![], body.to_string())
}

struct Mock {
    base: String,
    reqs: Arc<Mutex<Vec<Req>>>,
}

impl Mock {
    /// `handler` sees every request and returns `Some(reply)` to override the happy path.
    fn start(handler: impl Fn(&Req) -> Option<Reply> + Send + 'static) -> Mock {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let base = format!("http://{}", listener.local_addr().unwrap());
        let reqs = Arc::new(Mutex::new(Vec::new()));
        let log = Arc::clone(&reqs);
        thread::spawn(move || {
            // Work-item creates answer 501, 502, ... in order.
            let next_id = AtomicUsize::new(501);
            for stream in listener.incoming() {
                let Ok(stream) = stream else { break };
                if let Some(req) = read_request(stream.try_clone().unwrap()) {
                    let reply = handler(&req).unwrap_or_else(|| happy(&req, &next_id));
                    log.lock().unwrap().push(req);
                    write_reply(stream, &reply);
                }
            }
        });
        Mock { base, reqs }
    }

    fn happy() -> Mock {
        Mock::start(|_| None)
    }

    fn requests(&self) -> Vec<Req> {
        self.reqs.lock().unwrap().clone()
    }
}

/// Happy path: every work item exists, a work-item create answers the next id from 501,
/// the PR create answers id 9.
fn happy(req: &Req, next_id: &AtomicUsize) -> Reply {
    if req.method == "GET" && req.path.contains("/_apis/identities?") {
        // Identity id = "ID-" + the raw (still percent-encoded) filterValue.
        let fv = req.path.split("filterValue=").nth(1).unwrap().split('&').next().unwrap();
        json_reply(200, &format!(r#"{{"value":[{{"id":"ID-{fv}"}}]}}"#))
    } else if req.method == "GET" && req.path.contains("/_apis/wit/workitems/") {
        let id = req.path.rsplit('/').next().unwrap().split('?').next().unwrap();
        json_reply(200, &format!(r#"{{"id":{id}}}"#))
    } else if req.method == "POST" && req.path.contains("/_apis/wit/workitems/") {
        let id = next_id.fetch_add(1, Ordering::SeqCst);
        json_reply(200, &format!(r#"{{"id":{id}}}"#))
    } else if req.method == "POST" && req.path.contains("/pullrequests") {
        json_reply(201, r#"{"pullRequestId":9}"#)
    } else if req.method == "PATCH" && req.path.contains("/pullrequests/") {
        // Echo the requested completionOptions, as ADO does when it accepts them.
        let want = req.json()["completionOptions"].clone();
        json_reply(200, &format!(r#"{{"pullRequestId":9,"completionOptions":{want}}}"#))
    } else if req.method == "PATCH" && req.path.contains("/_apis/wit/workitems/") {
        let id = req.path.rsplit('/').next().unwrap().split('?').next().unwrap();
        json_reply(200, &format!(r#"{{"id":{id}}}"#))
    } else {
        json_reply(404, r#"{"message":"unexpected"}"#)
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

/// An `az` stub on PATH: `account get-access-token` prints `$STUB_AZ_TOKEN`, or exits 1
/// when it is empty (logged out).
fn az_stub(dir: &Path) -> PathBuf {
    let bin = dir.join("bin");
    std::fs::create_dir_all(&bin).unwrap();
    let p = bin.join("az");
    std::fs::write(
        &p,
        "#!/bin/sh\n[ -n \"$STUB_AZ_TOKEN\" ] && echo \"$STUB_AZ_TOKEN\" || exit 1\n",
    )
    .unwrap();
    std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o755)).unwrap();
    bin
}

struct Run {
    out: Output,
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

/// Run `ship pr <args>` hermetically against `api` with the given `az` token and PAT
/// (empty = absent). `extra` sets further environment variables.
fn ship_pr(dir: &Scratch, api: &str, az: &str, pat: &str, extra: &[(&str, &str)], args: &[&str]) -> Run {
    let stubs = az_stub(&dir.0);
    let path = format!("{}:{}", stubs.display(), std::env::var("PATH").unwrap());
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    c.current_dir(&dir.0)
        .arg("pr")
        .args(args)
        .env("PATH", path)
        .env("STUB_AZ_TOKEN", az)
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("SHIP_ADO_API_URL", api)
        .env_remove("SHIP_PLATFORM")
        .env_remove("AZURE_DEVOPS_EXT_PAT")
        .env_remove("AZURE_DEVOPS_PAT")
        .env_remove("SHIP_ADO_DEFAULT_REVIEWER")
        .env_remove("SHIP_ADO_ASSIGNEE")
        .stdin(Stdio::null());
    if !pat.is_empty() {
        c.env("AZURE_DEVOPS_EXT_PAT", pat);
    }
    c.envs(extra.iter().copied());
    Run { out: c.output().unwrap() }
}

fn run_ok(dir: &Scratch, m: &Mock, args: &[&str]) -> Run {
    ship_pr(dir, &m.base, TOKEN, "", &[], args)
}

fn paths(m: &Mock) -> Vec<String> {
    m.requests().iter().map(|r| format!("{} {}", r.method, r.path)).collect()
}

fn bearer() -> String {
    format!("Bearer {TOKEN}")
}

fn basic() -> String {
    format!("Basic {PAT_B64}")
}

const PR_PATH: &str = "POST /acme/My%20Project/_apis/git/repositories/widgets/pullrequests?api-version=7.1";
/// The completion PATCH that follows every PR create.
const COMPLETE_PATH: &str = "PATCH /acme/My%20Project/_apis/git/repositories/widgets/pullrequests/9?api-version=7.1";
/// Its stdout line on the happy path.
const COMPLETE: &str = "complete_transitions_work_items=true\n";

/// The PR create request (the last request is now the completion PATCH).
fn pr_create(m: &Mock) -> Req {
    m.requests().into_iter().find(|q| q.method == "POST" && q.path.contains("/pullrequests")).unwrap()
}

#[test]
fn existing_item_is_read_then_linked_in_one_create() {
    let r = repo("existing", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "docs(finops): x", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n{COMPLETE}tag_added=docs\ntag_added=finops\n")
    );
    assert!(run.stderr().contains(">> linking existing work item 42"), "{}", run.stderr());
    assert_eq!(paths(&m), ["GET /acme/_apis/wit/workitems/42?api-version=7.1", PR_PATH, COMPLETE_PATH]);
    let reqs = m.requests();
    assert_eq!(
        reqs[1].json(),
        serde_json::json!({
            "sourceRefName": "refs/heads/feat/x", "targetRefName": "refs/heads/main",
            "title": "docs(finops): x", "workItemRefs": [{"id": "42"}],
            "labels": [{"name": "docs"}, {"name": "finops"}]
        })
    );
    // az token on every call
    assert!(reqs.iter().all(|q| q.auth() == bearer()), "{reqs:?}");
}

#[test]
fn work_item_is_inferred_from_the_branch_and_verified() {
    let r = repo("branch", "feature/42-x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n{COMPLETE}"));
    assert_eq!(paths(&m)[0], "GET /acme/_apis/wit/workitems/42?api-version=7.1");
    assert_eq!(m.requests()[1].json()["workItemRefs"], serde_json::json!([{"id": "42"}]));
}

#[test]
fn bogus_branch_number_warns_and_opens_unlinked_with_no_create() {
    let r = repo("bogus", "feature/9999-x");
    let m = Mock::start(|q| {
        (q.method == "GET").then(|| json_reply(404, r#"{"message":"TF401232: Work item 9999 does not exist"}"#))
    });
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--no-create-work-item"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n{COMPLETE}"));
    assert!(
        run.stderr().contains(
            ">> WARNING: work item 9999 not found and --no-create-work-item set; PR will not link it"
        ),
        "{}",
        run.stderr()
    );
    let reqs = m.requests();
    assert_eq!(reqs.len(), 3);
    assert_eq!(reqs[1].json()["workItemRefs"], serde_json::json!([]));
}

const WI_PATH: &str = "POST /acme/My%20Project/_apis/wit/workitems/%24Task?api-version=7.1";

/// Env that pins the assignee so the tests do not depend on the host environment.
const ASSIGNEE_ENV: [(&str, &str); 1] = [("SHIP_ADO_ASSIGNEE", "a@b")];

fn run_assigned(dir: &Scratch, m: &Mock, args: &[&str]) -> Run {
    ship_pr(dir, &m.base, TOKEN, "", &ASSIGNEE_ENV, args)
}

#[test]
fn no_id_no_tasks_creates_one_item_from_the_title() {
    let r = repo("create-title", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x & y", "--no-tag"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!("work_item_created=501\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=501\n{COMPLETE}")
    );
    assert!(run.stderr().contains(">> created Task #501 assigned to a@b: x & y"), "{}", run.stderr());
    assert_eq!(paths(&m), [WI_PATH, PR_PATH, COMPLETE_PATH]);
    let reqs = m.requests();
    assert_eq!(reqs[0].headers.get("content-type").map(String::as_str), Some("application/json-patch+json"));
    assert_eq!(reqs[1].headers.get("content-type").map(String::as_str), Some("application/json"));
    assert_eq!(
        reqs[0].json(),
        serde_json::json!([
            {"op": "add", "path": "/fields/System.Title", "value": "x & y"},
            {"op": "add", "path": "/fields/System.AssignedTo", "value": "a@b"}
        ])
    );
    assert_eq!(reqs[1].json()["workItemRefs"], serde_json::json!([{"id": "501"}]));
}

#[test]
fn two_tasks_create_two_items_in_order() {
    let r = repo("two-tasks", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "A", "--task", "B"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "work_item_created=501\nwork_item_created=502\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=501 502\n{COMPLETE}"
        )
    );
    assert_eq!(paths(&m), [WI_PATH, WI_PATH, PR_PATH, COMPLETE_PATH]);
    let reqs = m.requests();
    assert_eq!(reqs[0].json()[0]["value"], "A");
    assert_eq!(reqs[1].json()[0]["value"], "B");
    assert_eq!(reqs[2].json()["workItemRefs"], serde_json::json!([{"id": "501"}, {"id": "502"}]));
}

#[test]
fn tasks_file_is_trimmed_skips_blanks_and_follows_task_flags() {
    let r = repo("tasks-file", "feat/x");
    std::fs::write(r.0.join("tasks.txt"), "  A  \n\n   \nB\n").unwrap();
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--tasks-file", "tasks.txt", "--task", "C"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let titles: Vec<String> =
        m.requests().iter().filter(|q| q.path.contains("workitems")).map(|q| q.json()[0]["value"].to_string()).collect();
    assert_eq!(titles, ["\"C\"", "\"A\"", "\"B\""]);
    assert!(run.stdout().contains("work_items=501 502 503\n"), "{}", run.stdout());
}

#[test]
fn unreadable_tasks_file_fails_before_any_request() {
    let r = repo("tasks-missing", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--tasks-file", "nope.txt"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("cannot read --tasks-file nope.txt: "), "{}", run.stderr());
    assert!(m.requests().is_empty());
}

#[test]
fn tasks_skip_branch_inference() {
    let r = repo("tasks-skip", "feature/42-x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "A"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m), [WI_PATH, PR_PATH, COMPLETE_PATH]);
    assert_eq!(m.requests()[1].json()["workItemRefs"], serde_json::json!([{"id": "501"}]));
}

#[test]
fn not_found_id_creates_one_item_from_the_title() {
    let r = repo("missing", "feat/x");
    let m = Mock::start(|q| (q.method == "GET").then(|| json_reply(404, r#"{"message":"gone"}"#)));
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--work-item", "9999"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m), ["GET /acme/_apis/wit/workitems/9999?api-version=7.1", WI_PATH, PR_PATH, COMPLETE_PATH]);
    assert!(run.stdout().starts_with("work_item_created=501\nplatform=azure\n"), "{}", run.stdout());
}

#[test]
fn type_and_assignee_flags_reach_the_request() {
    let r = repo("type", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(
        &r,
        &m,
        &["--title", "x", "--no-tag", "--work-item-type", "User Story", "--assignee", "c@d"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let reqs = m.requests();
    assert_eq!(reqs[0].path, "/acme/My%20Project/_apis/wit/workitems/%24User%20Story?api-version=7.1");
    assert_eq!(reqs[0].json()[1]["value"], "c@d");
    assert!(run.stderr().contains(">> created User Story #501 assigned to c@d: x"), "{}", run.stderr());
}

#[test]
fn empty_assignee_means_unassigned() {
    let r = repo("unassigned", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--assignee", ""]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(m.requests()[0].json().as_array().unwrap().len(), 1);
    assert!(run.stderr().contains("assigned to <unassigned>: x"), "{}", run.stderr());
}

#[test]
fn assignee_defaults_to_the_ts_default_without_env_or_flag() {
    let r = repo("default-assignee", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(m.requests()[0].json()[1]["value"], "you@example.com");
}

#[test]
fn no_create_work_item_never_creates() {
    let r = repo("no-create", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--no-create-work-item", "--task", "A"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m), [PR_PATH, COMPLETE_PATH]);
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n{COMPLETE}"));
}

#[test]
fn second_create_failing_keeps_the_first_line_and_opens_no_pr() {
    let r = repo("create-fails", "feat/x");
    let seen = Arc::new(AtomicUsize::new(0));
    let s = Arc::clone(&seen);
    let m = Mock::start(move |q| {
        (q.method == "POST" && q.path.contains("/workitems/") && s.fetch_add(1, Ordering::SeqCst) == 1)
            .then(|| json_reply(400, r#"{"message":"TF401320: bad field"}"#))
    });
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "A", "--task", "B"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "work_item_created=501\n");
    assert!(run.stderr().contains("ship-pr failed: HTTP 400: TF401320: bad field"), "{}", run.stderr());
    assert_eq!(paths(&m), [WI_PATH, WI_PATH]);
}

#[test]
fn bearer_401_on_the_create_falls_back_to_pat_for_the_rest() {
    let r = repo("create-fallback", "feat/x");
    let m = Mock::start(|q| q.auth().starts_with("Bearer ").then(|| json_reply(401, r#"{"message":"TF400813"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &ASSIGNEE_ENV, &["--title", "x", "--no-tag"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> bearer auth failed (401/403); falling back to pat").count(), 1);
    let reqs = m.requests();
    let auths: Vec<&str> = reqs.iter().map(Req::auth).collect();
    assert_eq!(auths, [bearer(), basic(), basic(), basic()]);
    assert_eq!(reqs[1].path, WI_PATH.trim_start_matches("POST "));
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stdout().contains(s) && !run.stderr().contains(s), "{s} leaked");
        assert!(reqs.iter().all(|q| !q.path.contains(s) && !q.body.contains(s)), "{s} in url/body");
    }
}

#[test]
fn no_id_at_all_with_no_create_opens_unlinked_silently() {
    let r = repo("noid", "main2");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--no-create-work-item"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("WARNING"), "{}", run.stderr());
    assert_eq!(paths(&m), [PR_PATH, COMPLETE_PATH]);
}

#[test]
fn tags_draft_literal_title_and_placeholder() {
    let r = repo("tags", "feat/x");
    std::fs::write(r.0.join("body.md"), "Fixes AB#<id>\nAlso AB#<work item>\n& more").unwrap();
    let m = Mock::happy();
    let run = run_ok(
        &r,
        &m,
        &["--title", "x & y", "--tag", "a,b", "--draft", "--work-item", "42", "--body-file", "body.md", "--target", "develop"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n{COMPLETE}tag_added=a\ntag_added=b\n")
    );
    assert!(run.stderr().contains(">> substituted AB# placeholder -> AB#42"), "{}", run.stderr());
    let body = m.requests()[1].json();
    assert_eq!(body["title"], "x & y");
    assert_eq!(body["isDraft"], true);
    assert_eq!(body["targetRefName"], "refs/heads/develop");
    assert_eq!(body["description"], "Fixes AB#42\nAlso AB#42\n& more");
    assert_eq!(body["labels"], serde_json::json!([{"name": "a"}, {"name": "b"}]));
}

#[test]
fn bearer_401_falls_back_to_pat_for_the_read_and_the_create() {
    let r = repo("fallback", "feat/x");
    let m = Mock::start(|q| (q.auth().starts_with("Bearer ")).then(|| json_reply(401, r#"{"message":"TF400813"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> bearer auth failed (401/403); falling back to pat").count(), 1);
    let reqs = m.requests();
    let auths: Vec<&str> = reqs.iter().map(Req::auth).collect();
    assert_eq!(auths, [bearer(), basic(), basic(), basic()]);
}

#[test]
fn pat_also_rejected_is_a_failure() {
    let r = repo("both-401", "feat/x");
    let m = Mock::start(|_| Some(json_reply(401, r#"{"message":"nope"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("ship-pr failed: HTTP 401: nope"), "{}", run.stderr());
    assert_eq!(m.requests().len(), 2, "one try per credential, no loop");
}

#[test]
fn logged_out_az_uses_the_pat_from_the_first_call() {
    let r = repo("loggedout", "feat/x");
    let m = Mock::happy();
    let run = ship_pr(&r, &m.base, "", PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("falling back"), "{}", run.stderr());
    assert!(m.requests().iter().all(|q| q.auth() == basic()));
}

#[test]
fn ext_pat_wins_over_plain_pat() {
    let r = repo("patorder", "feat/x");
    let m = Mock::happy();
    let run = ship_pr(
        &r,
        &m.base,
        "",
        PAT,
        &[("AZURE_DEVOPS_PAT", "OTHER")],
        &["--title", "x", "--no-tag", "--work-item", "42"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(m.requests().iter().all(|q| q.auth() == basic()));
}

#[test]
fn no_credential_at_all_fails_before_any_request() {
    let r = repo("nocred", "feat/x");
    let m = Mock::happy();
    let run = ship_pr(&r, &m.base, "", "", &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 1);
    assert!(
        run.stderr().contains("no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)"),
        "{}",
        run.stderr()
    );
    assert!(m.requests().is_empty());
}

#[test]
fn a_203_sign_in_page_counts_as_an_auth_failure() {
    // Bearer gets the 203 and falls back; the PAT is then accepted.
    let r = repo("203-fallback", "feat/x");
    let m = Mock::start(|q| q.auth().starts_with("Bearer ").then(|| (203, vec![], "<html>sign in</html>".into())));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains("falling back to pat"), "{}", run.stderr());

    // The PAT alone is answered with a 203: failure, not a silently "missing" item.
    let r = repo("203-fail", "feat/x");
    let m = Mock::start(|_| Some((203, vec![], "<html>sign in</html>".into())));
    let run = ship_pr(&r, &m.base, "", PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42", "--no-create-work-item"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("ship-pr failed: HTTP 203"), "{}", run.stderr());
    assert_eq!(m.requests().len(), 1);
}

#[test]
fn a_redirect_is_an_auth_failure_and_is_not_followed() {
    let r = repo("redirect", "feat/x");
    let sink = Mock::happy();
    let target = format!("{}/leak", sink.base);
    let m = Mock::start(move |_| Some((302, vec![("Location".into(), target.clone())], String::new())));
    let run = ship_pr(&r, &m.base, "", PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("ship-pr failed: HTTP 302"), "{}", run.stderr());
    assert!(sink.requests().is_empty(), "the credential must not follow a redirect");
}

const IDENT: &str = "GET /acme/_apis/identities?searchFilter=General&filterValue=";
const BASE_ARGS: [&str; 5] = ["--title", "x", "--no-tag", "--work-item", "42"];

fn with(extra: &[&'static str]) -> Vec<&'static str> {
    let mut v = vec!["--title", "x", "--no-tag", "--work-item", "42"];
    v.extend(extra);
    v
}

#[test]
fn optional_and_required_reviewers_are_resolved_and_ride_in_the_create() {
    let r = repo("rev-both", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--reviewer", "a@x,b@x", "--required-reviewer", "c@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n{COMPLETE}\
             reviewer_added=a@x required=false\nreviewer_added=b@x required=false\nreviewer_added=c@x required=true\n"
        )
    );
    let ps = paths(&m);
    assert_eq!(ps.len(), 6, "{ps:?}");
    assert!(ps[0].starts_with("GET /acme/_apis/wit/workitems/42"));
    for (i, who) in ["a%40x", "b%40x", "c%40x"].iter().enumerate() {
        assert_eq!(ps[i + 1], format!("{IDENT}{who}&api-version=7.1"));
    }
    assert_eq!(ps[4], PR_PATH);
    assert_eq!(
        m.requests()[4].json()["reviewers"],
        serde_json::json!([
            {"id": "ID-a%40x", "isRequired": false},
            {"id": "ID-b%40x", "isRequired": false},
            {"id": "ID-c%40x", "isRequired": true}
        ])
    );
}

#[test]
fn repeated_flags_are_split_and_deduped_per_list() {
    let r = repo("rev-dedupe", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--reviewer", "a@x,a@x", "--reviewer", "b@x,a@x", "--required-reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout().lines().filter(|l| l.starts_with("reviewer_added=")).collect::<Vec<_>>(),
        ["reviewer_added=a@x required=true", "reviewer_added=b@x required=false"]
    );
    let reqs = m.requests();
    assert_eq!(reqs.iter().filter(|q| q.path.contains("/identities")).count(), 2, "a@x looked up once");
    assert_eq!(
        pr_create(&m).json()["reviewers"],
        serde_json::json!([{"id": "ID-a%40x", "isRequired": true}, {"id": "ID-b%40x", "isRequired": false}])
    );
}

#[test]
fn an_empty_identity_id_is_no_match() {
    let r = repo("rev-empty-id", "feat/x");
    let m = Mock::start(|q| q.path.contains("/identities").then(|| json_reply(200, r#"{"value":[{"id":""}]}"#)));
    let run = run_ok(&r, &m, &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains("(no matching identity); skipping"), "{}", run.stderr());
    assert!(pr_create(&m).json().get("reviewers").is_none());
}

#[test]
fn a_203_on_the_bearer_lookup_resolves_on_the_pat() {
    let r = repo("rev-203", "feat/x");
    let m = Mock::start(|q| {
        (q.path.contains("/identities") && q.auth().starts_with("Bearer "))
            .then(|| (203, vec![], "<html>sign in</html>".into()))
    });
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> identity lookup got HTTP 203; retrying with the next credential").count(), 1);
    assert!(run.stdout().contains("reviewer_added=a@x required=false\n"), "{}", run.stdout());
}

#[test]
fn a_guid_passes_through_without_a_lookup() {
    let g = "1F0E2D3C-4B5A-6978-8A9B-0C1D2E3F4A5B";
    let r = repo("rev-guid", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--reviewer", g]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m).len(), 3, "no identities lookup");
    assert_eq!(m.requests()[1].json()["reviewers"], serde_json::json!([{"id": g, "isRequired": false}]));
    assert!(run.stdout().ends_with(&format!("reviewer_added={g} required=false\n")), "{}", run.stdout());
}

#[test]
fn an_unresolvable_reviewer_is_skipped_before_platform_and_the_pr_opens() {
    let r = repo("rev-empty", "feat/x");
    let m = Mock::start(|q| {
        (q.path.contains("filterValue=ghost")).then(|| json_reply(200, r#"{"count":0,"value":[]}"#))
    });
    let run = run_ok(&r, &m, &with(&["--reviewer", "ghost@x,a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "reviewer_skipped=ghost@x\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n{COMPLETE}\
             reviewer_added=a@x required=false\n"
        )
    );
    assert!(
        run.stderr().contains(">> WARNING: could not resolve reviewer 'ghost@x' (no matching identity); skipping"),
        "{}",
        run.stderr()
    );
    assert_eq!(run.stdout().matches("reviewer_skipped=").count(), 1);
    assert_eq!(pr_create(&m).json()["reviewers"], serde_json::json!([{"id": "ID-a%40x", "isRequired": false}]));
}

#[test]
fn only_unresolvable_reviewers_leave_the_reviewers_field_out() {
    let r = repo("rev-none", "feat/x");
    let m = Mock::start(|q| q.path.contains("/identities").then(|| json_reply(200, r#"{"value":[]}"#)));
    let run = run_ok(&r, &m, &with(&["--required-reviewer", "ghost@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(pr_create(&m).json().get("reviewers").is_none());
    assert!(!run.stdout().contains("reviewer_added"), "{}", run.stdout());
}

#[test]
fn a_lookup_http_error_is_a_warning_not_a_failure() {
    let r = repo("rev-500", "feat/x");
    let m = Mock::start(|q| q.path.contains("/identities").then(|| json_reply(500, r#"{"message":"boom"}"#)));
    let run = run_ok(&r, &m, &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains(">> WARNING: could not resolve reviewer 'a@x' (HTTP 500); skipping"), "{}", run.stderr());
    assert!(run.stdout().starts_with("reviewer_skipped=a@x\nplatform=azure\n"), "{}", run.stdout());
}

#[test]
fn a_transport_error_is_a_warning_not_a_failure() {
    // The identities host answers nothing: the connection is dropped.
    let r = repo("rev-transport", "feat/x");
    let m = Mock::start(|q| q.path.contains("/identities").then(|| (0, vec![], String::new())));
    let run = run_ok(&r, &m, &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains("could not resolve reviewer 'a@x' ("), "{}", run.stderr());
    assert!(run.stdout().contains("reviewer_skipped=a@x\n"), "{}", run.stdout());
}

#[test]
fn a_rejected_bearer_on_the_lookup_falls_back_to_the_pat() {
    let r = repo("rev-fallback", "feat/x");
    let m = Mock::start(|q| {
        (q.path.contains("/identities") && q.auth().starts_with("Bearer ")).then(|| json_reply(401, r#"{"message":"no"}"#))
    });
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> identity lookup got HTTP 401; retrying with the next credential").count(), 1);
    assert!(run.stdout().contains("reviewer_added=a@x required=false\n"), "{}", run.stdout());
    let reqs = m.requests();
    let idents: Vec<&str> = reqs.iter().filter(|q| q.path.contains("/identities")).map(Req::auth).collect();
    assert_eq!(idents, [bearer(), basic()]);
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stdout().contains(s) && !run.stderr().contains(s), "{s} leaked");
        assert!(reqs.iter().all(|q| !q.path.contains(s) && !q.body.contains(s)), "{s} in url/body");
    }
}

#[test]
fn a_lookup_rejected_by_every_credential_is_skipped() {
    let r = repo("rev-all-401", "feat/x");
    let m = Mock::start(|q| q.path.contains("/identities").then(|| json_reply(403, r#"{"message":"no"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains("(HTTP 403); skipping"), "{}", run.stderr());
    assert_eq!(m.requests().iter().filter(|q| q.path.contains("/identities")).count(), 2);
}

#[test]
fn the_lookup_starts_on_the_credential_the_earlier_calls_ended_on() {
    // The work-item read already fell back to the PAT; the lookup must not retry the bearer.
    let r = repo("rev-sticky", "feat/x");
    let m = Mock::start(|q| q.auth().starts_with("Bearer ").then(|| json_reply(401, r#"{"message":"no"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("identity lookup"), "{}", run.stderr());
    let reqs = m.requests();
    let ident = reqs.iter().find(|q| q.path.contains("/identities")).unwrap();
    assert_eq!(ident.auth(), basic());
}

#[test]
fn default_reviewer_env_is_added_as_optional_with_a_note() {
    let r = repo("defrev", "feat/x");
    let m = Mock::happy();
    let env = [("SHIP_ADO_DEFAULT_REVIEWER", "  boss@acme.com  ")];
    let run = ship_pr(&r, &m.base, TOKEN, "", &env, &BASE_ARGS);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(
        run.stderr().contains(">> NOTE: no reviewer given; using SHIP_ADO_DEFAULT_REVIEWER (boss@acme.com)"),
        "{}",
        run.stderr()
    );
    assert!(!run.stderr().contains("not applied yet"), "{}", run.stderr());
    assert_eq!(
        m.requests()[2].json()["reviewers"],
        serde_json::json!([{"id": "ID-boss%40acme.com", "isRequired": false}])
    );
    assert!(run.stdout().ends_with("reviewer_added=boss@acme.com required=false\n"), "{}", run.stdout());
}

#[test]
fn an_explicit_reviewer_overrides_the_default() {
    let r = repo("defrev-explicit", "feat/x");
    let m = Mock::happy();
    let env = [("SHIP_ADO_DEFAULT_REVIEWER", "boss@acme.com")];
    let run = ship_pr(&r, &m.base, TOKEN, "", &env, &with(&["--required-reviewer", "c@x"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("SHIP_ADO_DEFAULT_REVIEWER"), "{}", run.stderr());
    assert_eq!(paths(&m).iter().filter(|p| p.contains("/identities")).count(), 1);
}

#[test]
fn no_reviewer_adds_none_and_does_no_lookup() {
    let r = repo("defrev-off", "feat/x");
    let m = Mock::happy();
    let env = [("SHIP_ADO_DEFAULT_REVIEWER", "boss@acme.com")];
    let run = ship_pr(&r, &m.base, TOKEN, "", &env, &with(&["--no-reviewer"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("SHIP_ADO_DEFAULT_REVIEWER"), "{}", run.stderr());
    assert_eq!(paths(&m).len(), 3, "{:?}", paths(&m));
    assert!(m.requests()[1].json().get("reviewers").is_none());
}

#[test]
fn a_blank_default_reviewer_is_ignored() {
    let r = repo("defrev-blank", "feat/x");
    let m = Mock::happy();
    let run = ship_pr(&r, &m.base, TOKEN, "", &[("SHIP_ADO_DEFAULT_REVIEWER", "   ")], &BASE_ARGS);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("SHIP_ADO_DEFAULT_REVIEWER"), "{}", run.stderr());
    assert_eq!(paths(&m).len(), 3);
}

#[test]
fn the_upn_is_encoded_like_encode_uri_component() {
    let r = repo("rev-encode", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--reviewer", "o'b+x@y.com"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m)[1], format!("{IDENT}o'b%2Bx%40y.com&api-version=7.1"));
    assert!(run.stdout().contains("reviewer_added=o'b+x@y.com required=false\n"), "{}", run.stdout());
}

#[test]
fn reviewers_resolve_after_created_work_items_and_before_the_pr() {
    let r = repo("rev-order", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--reviewer", "a@x"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let ps = paths(&m);
    assert_eq!(ps[0], WI_PATH);
    assert!(ps[1].starts_with(IDENT), "{ps:?}");
    assert_eq!(ps[2], PR_PATH);
    assert!(run.stdout().starts_with("work_item_created=501\nplatform=azure\n"), "{}", run.stdout());
}

#[test]
fn a_cleartext_seam_also_guards_the_identities_origin() {
    let r = repo("rev-cleartext", "feat/x");
    let run = ship_pr(&r, "http://example.com", TOKEN, "", &[], &with(&["--reviewer", "a@x"]));
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("refusing SHIP_ADO_API_URL"), "{}", run.stderr());
}

#[test]
fn credentials_appear_only_in_authorization_headers() {
    let r = repo("secrets", "feat/x");
    let m = Mock::start(|q| q.auth().starts_with("Bearer ").then(|| json_reply(403, r#"{"message":"denied"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stdout().contains(s) && !run.stderr().contains(s), "{s} leaked");
    }
    for q in m.requests() {
        for s in [TOKEN, PAT, PAT_B64] {
            assert!(!q.path.contains(s) && !q.body.contains(s), "{s} in url/body");
        }
        for (k, v) in &q.headers {
            if k != "authorization" {
                assert!(!v.contains(TOKEN) && !v.contains(PAT_B64), "secret in header {k}");
            }
        }
    }
}

#[test]
fn create_failure_reports_the_api_message() {
    let r = repo("create-500", "feat/x");
    let m = Mock::start(|q| (q.method == "POST").then(|| json_reply(409, r#"{"message":"TF401179: active PR exists"}"#)));
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("ship-pr failed: HTTP 409: TF401179: active PR exists"), "{}", run.stderr());
}

#[test]
fn cleartext_api_seam_is_refused() {
    let r = repo("cleartext", "feat/x");
    let run = ship_pr(&r, "http://example.com", TOKEN, "", &[], &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains("refusing SHIP_ADO_API_URL"), "{}", run.stderr());
}

// --- Story 3.5: completion options and --transition ---

/// The work-item state PATCH for `id`.
fn state_path(id: u64) -> String {
    format!("PATCH /acme/My%20Project/_apis/wit/workitems/{id}?api-version=7.1")
}

#[test]
fn transition_and_completion_follow_work_items_in_ts_order() {
    let r = repo("tr-ac", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--tag", "feat", "--work-item", "42", "--transition", "Resolved"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n\
             complete_transitions_work_items=true\nwork_item=42 state=Resolved\ntag_added=feat\n"
        )
    );
    assert!(run.stderr().contains(">> transitioning work item 42 -> Resolved"), "{}", run.stderr());
    let ps = paths(&m);
    assert_eq!(ps[1..], [PR_PATH.to_string(), COMPLETE_PATH.to_string(), state_path(42)]);
    let reqs = m.requests();
    assert_eq!(reqs[2].headers.get("content-type").map(String::as_str), Some("application/json"));
    assert_eq!(reqs[2].json(), serde_json::json!({"completionOptions": {"transitionWorkItems": true}}));
    assert_eq!(reqs[3].headers.get("content-type").map(String::as_str), Some("application/json-patch+json"));
    assert_eq!(reqs[3].json(), serde_json::json!([{"op": "add", "path": "/fields/System.State", "value": "Resolved"}]));
    assert!(pr_create(&m).json().get("completionOptions").is_none(), "never in the create payload");
}

#[test]
fn no_complete_transition_patches_an_explicit_false() {
    let r = repo("tr-off", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--no-complete-transition"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().contains("\ncomplete_transitions_work_items=false\n"), "{}", run.stdout());
    let patch = m.requests().into_iter().find(|q| q.method == "PATCH").unwrap();
    assert_eq!(patch.json(), serde_json::json!({"completionOptions": {"transitionWorkItems": false}}));
}

#[test]
fn the_printed_value_is_read_back_not_echoed() {
    let r = repo("tr-readback", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "PATCH").then(|| json_reply(200, r#"{"completionOptions":{"transitionWorkItems":false}}"#))
    });
    let run = run_ok(&r, &m, &BASE_ARGS);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().contains("\ncomplete_transitions_work_items=false\n"), "{}", run.stdout());
}

#[test]
fn null_completion_options_print_unset() {
    let r = repo("tr-null", "feat/x");
    let m = Mock::start(|q| (q.method == "PATCH").then(|| json_reply(200, r#"{"completionOptions":null}"#)));
    let run = run_ok(&r, &m, &BASE_ARGS);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().contains("\ncomplete_transitions_work_items=unset\n"), "{}", run.stdout());
}

#[test]
fn a_failed_completion_patch_warns_and_tags_and_reviewers_still_print() {
    let r = repo("tr-500", "feat/x");
    let m = Mock::start(|q| (q.method == "PATCH").then(|| json_reply(500, r#"{"message":"boom"}"#)));
    let run = run_ok(&r, &m, &["--title", "x", "--tag", "feat", "--work-item", "42", "--reviewer", "a@x"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\ncomplete_transitions_work_items=unset\n\
             tag_added=feat\nreviewer_added=a@x required=false\n"
        )
    );
    assert!(
        run.stderr()
            .contains(">> WARNING: could not set \"complete linked work items\" to true on PR 9: HTTP 500: boom"),
        "{}",
        run.stderr()
    );
}

#[test]
fn created_items_transition_in_order() {
    let r = repo("tr-two", "feat/x");
    let m = Mock::happy();
    let run =
        run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "A", "--task", "B", "--transition", "Resolved"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(
        run.stdout().ends_with(
            "work_items=501 502\ncomplete_transitions_work_items=true\n\
             work_item=501 state=Resolved\nwork_item=502 state=Resolved\n"
        ),
        "{}",
        run.stdout()
    );
    let ps = paths(&m);
    assert_eq!(ps[ps.len() - 2..], [state_path(501), state_path(502)]);
}

#[test]
fn a_rejected_state_warns_and_the_next_item_still_transitions() {
    let r = repo("tr-bad", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "PATCH" && q.path.contains("/workitems/501"))
            .then(|| json_reply(400, r#"{"message":"TF401320: invalid state"}"#))
    });
    let run =
        run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "A", "--task", "B", "--transition", "Bogus"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stdout().contains("work_item=501 "), "{}", run.stdout());
    assert!(run.stdout().ends_with("work_item=502 state=Bogus\n"), "{}", run.stdout());
    assert!(
        run.stderr()
            .contains(">> WARNING: could not transition work item 501 -> Bogus: HTTP 400: TF401320: invalid state"),
        "{}",
        run.stderr()
    );
}

#[test]
fn transition_with_no_linked_item_sends_nothing_but_completion_still_runs() {
    let r = repo("tr-none", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--no-create-work-item", "--transition", "Resolved"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m), [PR_PATH, COMPLETE_PATH]);
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n{COMPLETE}"));
    assert!(!run.stderr().contains("transitioning"), "{}", run.stderr());
}

#[test]
fn an_empty_transition_is_ignored() {
    let r = repo("tr-empty", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--transition", ""]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!paths(&m).iter().any(|p| p.contains("/wit/workitems/") && p.starts_with("PATCH")));
    assert!(!run.stdout().contains("work_item="), "{}", run.stdout());
}

#[test]
fn bearer_401_on_a_patch_falls_back_to_pat_and_secrets_stay_in_headers() {
    let r = repo("tr-auth", "feat/x");
    let bearer_auth = bearer();
    let m = Mock::start(move |q| {
        (q.method == "PATCH" && q.auth() == bearer_auth).then(|| json_reply(401, r#"{"message":"nope"}"#))
    });
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--transition", "Resolved"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> bearer auth failed (401/403); falling back to pat").count(), 1);
    assert!(
        run.stdout().contains("complete_transitions_work_items=true\nwork_item=42 state=Resolved\n"),
        "{}",
        run.stdout()
    );
    let reqs = m.requests();
    let auths: Vec<&str> = reqs.iter().map(Req::auth).collect();
    // read + create on bearer, the completion PATCH rejected then retried on the PAT, which stays.
    assert_eq!(auths, [bearer(), bearer(), bearer(), basic(), basic()]);
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stdout().contains(s) && !run.stderr().contains(s), "{s} leaked");
    }
    for q in &reqs {
        for s in [TOKEN, PAT, PAT_B64] {
            assert!(!q.path.contains(s) && !q.body.contains(s), "{s} in url/body");
        }
    }
}

#[test]
fn every_credential_rejected_on_the_patches_only_warns() {
    let r = repo("tr-allauth", "feat/x");
    let m = Mock::start(|q| (q.method == "PATCH").then(|| json_reply(401, r#"{"message":"nope"}"#)));
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--transition", "Resolved"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().ends_with("work_items=42\ncomplete_transitions_work_items=unset\n"), "{}", run.stdout());
    assert!(
        run.stderr().contains(">> WARNING: could not set \"complete linked work items\" to true on PR 9"),
        "{}",
        run.stderr()
    );
    assert!(run.stderr().contains(">> WARNING: could not transition work item 42 -> Resolved"), "{}", run.stderr());
}

#[test]
fn the_state_is_trimmed_and_blank_means_none() {
    let r = repo("tr-trim", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--transition", " Resolved "]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().contains("work_item=42 state=Resolved\n"), "{}", run.stdout());
    let patch = m.requests().into_iter().find(|q| q.path.starts_with("/acme/My%20Project/_apis/wit/")).unwrap();
    assert_eq!(patch.json()[0]["value"], "Resolved");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &with(&["--transition", "   "]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stdout().contains("work_item="), "{}", run.stdout());
}

#[test]
fn repeated_transition_flags_take_the_last_value() {
    let r = repo("tr-repeat", "feat/x");
    let m = Mock::happy();
    let args = with(&[
        "--transition",
        "Active",
        "--transition",
        "Resolved",
        "--no-complete-transition",
        "--no-complete-transition",
    ]);
    let run = run_ok(&r, &m, &args);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(
        run.stdout().contains("complete_transitions_work_items=false\nwork_item=42 state=Resolved\n"),
        "{}",
        run.stdout()
    );
}

// --- Story 3.6: --related links the PR's own items Related, never the PR ---

/// The work-item read for `id` (org-level path).
fn read_path(id: u64) -> String {
    format!("GET /acme/_apis/wit/workitems/{id}?api-version=7.1")
}

/// The relation PATCH body that relates an own item to `rid` through PR 9.
fn relation_body(rid: u64) -> serde_json::Value {
    serde_json::json!([{
        "op": "add", "path": "/relations/-",
        "value": {
            "rel": "System.LinkTypes.Related",
            "url": format!("https://dev.azure.com/acme/_apis/wit/workItems/{rid}"),
            "attributes": {"comment": "Related via PR 9"}
        }
    }])
}

/// The work-item PATCHes (relation and state), in order.
fn wi_patches(m: &Mock) -> Vec<Req> {
    m.requests().into_iter().filter(|q| q.method == "PATCH" && q.path.contains("/_apis/wit/workitems/")).collect()
}

const MENTION_WARNING: &str = "mention #7; Azure Repos may link it to the PR, and Complete would then close it. \
                               Reword it (e.g. \"item 7\") before completing.";

#[test]
fn related_ids_are_verified_then_linked_from_the_own_item_only() {
    let r = repo("rel-happy", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7,AB#8"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n\
             related_linked=42->7\nrelated_linked=42->8\n{COMPLETE}"
        )
    );
    assert_eq!(
        paths(&m),
        [
            read_path(7),
            read_path(8),
            read_path(42),
            PR_PATH.to_string(),
            state_path(42),
            state_path(42),
            COMPLETE_PATH.to_string()
        ]
    );
    // The PR references only its own item; the related ids are nowhere in the create.
    let create = pr_create(&m);
    assert_eq!(create.json()["workItemRefs"], serde_json::json!([{"id": "42"}]));
    assert!(!create.body.contains("\"7\"") && !create.body.contains("\"8\""), "{}", create.body);
    let patches = wi_patches(&m);
    assert_eq!(patches.len(), 2);
    for (q, rid) in patches.iter().zip([7, 8]) {
        assert_eq!(q.headers.get("content-type").map(String::as_str), Some("application/json-patch+json"));
        assert_eq!(q.json(), relation_body(rid));
        assert_eq!(q.auth(), bearer());
    }
}

#[test]
fn the_acceptance_run_prints_exactly_and_the_relation_uses_the_real_org_url() {
    let r = repo("rel-ac", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--work-item", "42", "--related", "7", "--no-tag"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\nrelated_linked=42->7\n{COMPLETE}")
    );
    let patch = &wi_patches(&m)[0];
    let url = patch.json()[0]["value"]["url"].as_str().unwrap().to_string();
    assert!(url.starts_with("https://dev.azure.com/acme"), "{url}");
    assert!(!patch.body.contains(&m.base) && !patch.body.contains("127.0.0.1"), "{}", patch.body);
}

#[test]
fn created_own_items_are_each_related() {
    let r = repo("rel-created", "feat/x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--task", "a", "--task", "b", "--related", "7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "work_item_created=501\nwork_item_created=502\nplatform=azure\npr_id=9\npr_url={PR_URL}\n\
             work_items=501 502\nrelated_linked=501->7\nrelated_linked=502->7\n{COMPLETE}"
        )
    );
    assert_eq!(paths(&m)[0], read_path(7));
    let ps: Vec<String> = wi_patches(&m).iter().map(|q| q.path.clone()).collect();
    assert_eq!(
        ps,
        [
            "/acme/My%20Project/_apis/wit/workitems/501?api-version=7.1",
            "/acme/My%20Project/_apis/wit/workitems/502?api-version=7.1"
        ]
    );
    assert!(wi_patches(&m).iter().all(|q| q.json() == relation_body(7)));
}

#[test]
fn a_missing_related_item_exits_two_with_nothing_written() {
    let r = repo("rel-missing", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "GET" && q.path.contains("/workitems/7?"))
            .then(|| json_reply(404, r#"{"message":"TF401232: Work item 7 does not exist"}"#))
    });
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7,8"]);
    assert_eq!(run.code(), 2);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("--related 7: work item not found"), "{}", run.stderr());
    // Verification stops at the first missing id, before the own item and before any write.
    assert_eq!(paths(&m), [read_path(7)]);
}

#[test]
fn any_related_read_error_is_reported_as_not_found() {
    let r = repo("rel-500", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "GET" && q.path.contains("/workitems/8?")).then(|| json_reply(500, r#"{"message":"boom"}"#))
    });
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7,8"]);
    assert_eq!(run.code(), 2);
    assert!(run.stderr().contains("--related 8: work item not found"), "{}", run.stderr());
    assert!(m.requests().iter().all(|q| q.method == "GET"), "{:?}", paths(&m));
    // Every credential rejected on the read is "not found" too.
    let m = Mock::start(|q| (q.method == "GET").then(|| json_reply(401, r#"{"message":"nope"}"#)));
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7"]);
    assert_eq!(run.code(), 2);
    assert!(run.stderr().contains("--related 7: work item not found"), "{}", run.stderr());
    assert_eq!(paths(&m), [read_path(7)]);
}

#[test]
fn related_skips_branch_inference_and_creates_from_the_title() {
    // A two-digit id: branch inference needs 2-7 digits, so `feat/7-x` would not infer anyway.
    let r = repo("rel-branch", "feat/77-x");
    let m = Mock::happy();
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--related", "77"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "work_item_created=501\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=501\n\
             related_linked=501->77\n{COMPLETE}"
        )
    );
    assert_eq!(
        paths(&m),
        [
            read_path(77),
            WI_PATH.to_string(),
            PR_PATH.to_string(),
            state_path(501),
            COMPLETE_PATH.to_string()
        ]
    );
    assert_eq!(pr_create(&m).json()["workItemRefs"], serde_json::json!([{"id": "501"}]));
}

#[test]
fn the_same_id_as_work_item_and_related_exits_two_before_any_request() {
    let r = repo("rel-both", "feat/x");
    let m = Mock::happy();
    for related in ["7", "AB#7", "3,#7"] {
        let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "7", "--related", related]);
        assert_eq!(run.code(), 2, "{related}: {}", run.stderr());
        assert_eq!(run.stdout(), "");
        assert!(
            run.stderr().contains(
                "work item 7 is both --work-item and --related; a related item is never linked to the PR"
            ),
            "{}",
            run.stderr()
        );
    }
    assert!(m.requests().is_empty());
}

/// Make `refs/remotes/origin/main` the current commit, then commit `msg` on the branch.
fn commit_on_branch(r: &Scratch, msg: &str) {
    git(&r.0, &["update-ref", "refs/remotes/origin/main", "HEAD"]);
    std::fs::write(r.0.join("g.txt"), "y\n").unwrap();
    git(&r.0, &["add", "g.txt"]);
    git(&r.0, &["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg]);
}

#[test]
fn a_mention_in_the_body_and_a_commit_warns_and_the_pr_still_opens() {
    let r = repo("rel-mention", "feat/x");
    commit_on_branch(&r, "fixes #7");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7", "--body", "see AB#7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let err = run.stderr();
    let warning = format!(">> WARNING: the PR body and a commit message {MENTION_WARNING}");
    assert!(err.contains(&warning), "{err}");
    // TS order: verify, warn, then resolve the own item.
    assert!(err.find(&warning).unwrap() < err.find(">> linking existing work item 42").unwrap(), "{err}");
    assert!(run.stdout().contains("\nrelated_linked=42->7\n"), "{}", run.stdout());
    // The body is sent as written; the warning never rewrites it.
    assert_eq!(pr_create(&m).json()["description"], "see AB#7");
}

#[test]
fn a_mention_in_only_one_place_names_that_place() {
    let r = repo("rel-body-only", "feat/x");
    commit_on_branch(&r, "unrelated change");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7", "--body", "ab#7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains(&format!(">> WARNING: the PR body {MENTION_WARNING}")), "{}", run.stderr());

    let r = repo("rel-commit-only", "feat/x");
    commit_on_branch(&r, "subject\n\nRefs #7 for context");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7", "--body", "item 7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains(&format!(">> WARNING: a commit message {MENTION_WARNING}")), "{}", run.stderr());
}

#[test]
fn no_mention_or_an_unknown_range_gives_no_warning() {
    // `#70` and `x#7` are not mentions of 7; commits before origin/main are outside the range.
    let r = repo("rel-no-mention", "feat/x");
    commit_on_branch(&r, "touches #70");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7", "--body", "x#7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("mention #"), "{}", run.stderr());
    // No origin/main ref: git log fails, which counts as no commit text.
    let r = repo("rel-no-range", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "x", "--no-tag", "--work-item", "42", "--related", "7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("mention #"), "{}", run.stderr());
    assert!(run.stdout().contains("\nrelated_linked=42->7\n"), "{}", run.stdout());
}

#[test]
fn no_own_item_warns_nothing_linked_and_exits_zero() {
    let r = repo("rel-no-own", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "GET" && q.path.contains("/workitems/42?")).then(|| json_reply(404, r#"{"message":"gone"}"#))
    });
    let run =
        run_ok(&r, &m, &["--title", "x", "--no-tag", "--no-create-work-item", "--work-item", "42", "--related", "7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n{COMPLETE}"));
    assert!(
        run.stderr().contains(
            ">> WARNING: --related given but the PR has no work item of its own to relate it to; nothing linked"
        ),
        "{}",
        run.stderr()
    );
    assert_eq!(paths(&m), [read_path(7), read_path(42), PR_PATH.to_string(), COMPLETE_PATH.to_string()]);
    assert_eq!(pr_create(&m).json()["workItemRefs"], serde_json::json!([]));
}

#[test]
fn a_failed_link_warns_and_the_next_pair_and_later_steps_still_run() {
    let r = repo("rel-fail", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "PATCH" && q.body.contains("workItems/7\""))
            .then(|| json_reply(400, r#"{"message":"TF401035: bad relation"}"#))
    });
    let run = run_ok(
        &r,
        &m,
        &["--title", "x", "--tag", "feat", "--work-item", "42", "--related", "7,8", "--transition", "Resolved"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!(
            "platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\nrelated_linked=42->8\n\
             {COMPLETE}work_item=42 state=Resolved\ntag_added=feat\n"
        )
    );
    assert!(
        run.stderr().contains(">> WARNING: could not link work item 42 Related to 7: HTTP 400: TF401035: bad relation"),
        "{}",
        run.stderr()
    );
}

#[test]
fn a_rejected_bearer_on_the_relation_falls_back_to_pat_and_secrets_stay_in_headers() {
    let r = repo("rel-auth", "feat/x");
    let bearer_auth = bearer();
    let m = Mock::start(move |q| {
        (q.method == "PATCH" && q.auth() == bearer_auth).then(|| json_reply(401, r#"{"message":"nope"}"#))
    });
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--related", "7"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stderr().matches(">> bearer auth failed (401/403); falling back to pat").count(), 1);
    assert!(run.stdout().contains("\nrelated_linked=42->7\ncomplete_transitions_work_items=true\n"), "{}", run.stdout());
    let reqs = m.requests();
    let auths: Vec<&str> = reqs.iter().map(Req::auth).collect();
    // reads + create on bearer, the relation PATCH rejected then retried on the PAT, which stays.
    assert_eq!(auths, [bearer(), bearer(), bearer(), bearer(), basic(), basic()]);
    assert_eq!(reqs[4].json(), relation_body(7));
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stdout().contains(s) && !run.stderr().contains(s), "{s} leaked");
    }
    for q in &reqs {
        for s in [TOKEN, PAT, PAT_B64] {
            assert!(!q.path.contains(s) && !q.body.contains(s), "{s} in url/body");
        }
        for (k, v) in &q.headers {
            if k != "authorization" {
                assert!(!v.contains(TOKEN) && !v.contains(PAT_B64), "secret in header {k}");
            }
        }
    }
}

#[test]
fn every_credential_rejected_on_the_relation_only_warns() {
    let r = repo("rel-allauth", "feat/x");
    let m = Mock::start(|q| {
        (q.method == "PATCH" && q.body.contains("/relations/-")).then(|| json_reply(401, r#"{"message":"nope"}"#))
    });
    let run = ship_pr(&r, &m.base, TOKEN, PAT, &[], &with(&["--related", "7"]));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().ends_with(&format!("work_items=42\n{COMPLETE}")), "{}", run.stdout());
    assert!(run.stderr().contains(">> WARNING: could not link work item 42 Related to 7: HTTP 401"), "{}", run.stderr());
    for s in [TOKEN, PAT, PAT_B64] {
        assert!(!run.stderr().contains(s), "{s} leaked");
    }
}
