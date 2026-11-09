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
    if req.method == "GET" && req.path.contains("/_apis/wit/workitems/") {
        let id = req.path.rsplit('/').next().unwrap().split('?').next().unwrap();
        json_reply(200, &format!(r#"{{"id":{id}}}"#))
    } else if req.method == "POST" && req.path.contains("/_apis/wit/workitems/") {
        let id = next_id.fetch_add(1, Ordering::SeqCst);
        json_reply(200, &format!(r#"{{"id":{id}}}"#))
    } else if req.method == "POST" && req.path.contains("/pullrequests") {
        json_reply(201, r#"{"pullRequestId":9}"#)
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

#[test]
fn existing_item_is_read_then_linked_in_one_create() {
    let r = repo("existing", "feat/x");
    let m = Mock::happy();
    let run = run_ok(&r, &m, &["--title", "docs(finops): x", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(
        run.stdout(),
        format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\ntag_added=docs\ntag_added=finops\n")
    );
    assert!(run.stderr().contains(">> linking existing work item 42"), "{}", run.stderr());
    assert_eq!(paths(&m), ["GET /acme/_apis/wit/workitems/42?api-version=7.1", PR_PATH]);
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
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\n"));
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
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n"));
    assert!(
        run.stderr().contains(
            ">> WARNING: work item 9999 not found and --no-create-work-item set; PR will not link it"
        ),
        "{}",
        run.stderr()
    );
    let reqs = m.requests();
    assert_eq!(reqs.len(), 2);
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
        format!("work_item_created=501\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=501\n")
    );
    assert!(run.stderr().contains(">> created Task #501 assigned to a@b: x & y"), "{}", run.stderr());
    assert_eq!(paths(&m), [WI_PATH, PR_PATH]);
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
            "work_item_created=501\nwork_item_created=502\nplatform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=501 502\n"
        )
    );
    assert_eq!(paths(&m), [WI_PATH, WI_PATH, PR_PATH]);
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
    assert_eq!(paths(&m), [WI_PATH, PR_PATH]);
    assert_eq!(m.requests()[1].json()["workItemRefs"], serde_json::json!([{"id": "501"}]));
}

#[test]
fn not_found_id_creates_one_item_from_the_title() {
    let r = repo("missing", "feat/x");
    let m = Mock::start(|q| (q.method == "GET").then(|| json_reply(404, r#"{"message":"gone"}"#)));
    let run = run_assigned(&r, &m, &["--title", "x", "--no-tag", "--work-item", "9999"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(paths(&m), ["GET /acme/_apis/wit/workitems/9999?api-version=7.1", WI_PATH, PR_PATH]);
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
    assert_eq!(paths(&m), [PR_PATH]);
    assert_eq!(run.stdout(), format!("platform=azure\npr_id=9\npr_url={PR_URL}\n"));
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
    assert_eq!(auths, [bearer(), basic(), basic()]);
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
    assert_eq!(paths(&m), [PR_PATH]);
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
        format!("platform=azure\npr_id=9\npr_url={PR_URL}\nwork_items=42\ntag_added=a\ntag_added=b\n")
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
    assert_eq!(auths, [bearer(), basic(), basic()]);
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

#[test]
fn reviewer_and_related_flags_fail_fast_without_calling_the_api() {
    for flag in [["--reviewer", "a@b.c"], ["--required-reviewer", "a@b.c"], ["--related", "5"]] {
        let r = repo("unsupported", "feat/x");
        let m = Mock::happy();
        let mut args = vec!["--title", "x", "--no-tag", "--work-item", "42"];
        args.extend(flag);
        let run = run_ok(&r, &m, &args);
        assert_eq!(run.code(), 1, "{flag:?}");
        assert!(
            run.stderr().contains(&format!("{} is not yet supported on Azure by the binary", flag[0])),
            "{}",
            run.stderr()
        );
        assert!(m.requests().is_empty(), "{flag:?}");
    }
}

#[test]
fn default_reviewer_env_prints_a_note_and_does_not_block() {
    let r = repo("defrev", "feat/x");
    let m = Mock::happy();
    let env = [("SHIP_ADO_DEFAULT_REVIEWER", "boss@acme.com")];
    let run = ship_pr(&r, &m.base, TOKEN, "", &env, &["--title", "x", "--no-tag", "--work-item", "42"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(
        run.stderr().contains(">> NOTE: SHIP_ADO_DEFAULT_REVIEWER is not applied yet (Story 3.4)"),
        "{}",
        run.stderr()
    );
    assert!(m.requests()[1].json().get("reviewers").is_none());

    // --no-reviewer silences it
    let r = repo("defrev2", "feat/x");
    let run = ship_pr(&r, &m.base, TOKEN, "", &env, &["--title", "x", "--no-tag", "--work-item", "42", "--no-reviewer"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!run.stderr().contains("SHIP_ADO_DEFAULT_REVIEWER"), "{}", run.stderr());
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
