//! Integration tests for `ship tag`: real binary, scratch repos, a mock Azure DevOps / GitHub
//! API on 127.0.0.1 (std `TcpListener`) and stub `az` / `gh` first on PATH. No network, no bun.

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
const GH_URL: &str = "git@github.com:acme/widgets.git";
/// The Azure label collection of PR 9 (the path the mock sees).
const AZ_LABELS: &str = "/acme/My%20Project/_apis/git/repositories/widgets/pullRequests/9/labels";
static COUNTER: AtomicUsize = AtomicUsize::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-tag-{}-{n}-{tag}", std::process::id()));
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

/// Repo with one commit and `origin` set to `url` (never contacted).
fn repo(tag: &str, url: &str) -> Scratch {
    let r = Scratch::new(tag);
    git(&r.0, &["init", "-q", "-b", "main"]);
    std::fs::write(r.0.join("f.txt"), "x\n").unwrap();
    git(&r.0, &["add", "f.txt"]);
    git(&r.0, &["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"]);
    git(&r.0, &["remote", "add", "origin", url]);
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

fn reply(status: u16, body: &str) -> Reply {
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
            for stream in listener.incoming() {
                let Ok(stream) = stream else { break };
                if let Some(req) = read_request(stream.try_clone().unwrap()) {
                    let r = handler(&req).unwrap_or_else(|| happy(&req));
                    log.lock().unwrap().push(req);
                    write_reply(stream, &r);
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

    fn paths(&self) -> Vec<String> {
        self.requests().iter().map(|r| format!("{} {}", r.method, r.path)).collect()
    }
}

/// Happy path for both platforms: adds and removes succeed, the Azure list answers
/// `one`, `two` (and one nameless entry), the GitHub list answers `bug`, `wip`.
fn happy(req: &Req) -> Reply {
    let azure = req.path.contains("/_apis/git/");
    match (azure, req.method.as_str()) {
        (true, "POST") => reply(200, r#"{"id":"1","name":"x"}"#),
        (true, "DELETE") => reply(200, "{}"),
        (true, "GET") => reply(200, r#"{"count":3,"value":[{"name":"one"},{"id":"z"},{"name":"two"}]}"#),
        (false, "POST") => reply(200, r#"[{"name":"x"}]"#),
        (false, "DELETE") => reply(200, "[]"),
        (false, "GET") => reply(200, r#"[{"name":"bug"},{"name":"wip"}]"#),
        _ => reply(404, r#"{"message":"unexpected"}"#),
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

/// `az` and `gh` stubs on PATH. `az account get-access-token` prints `$STUB_AZ_TOKEN` (exit 1
/// when empty); `gh auth token` prints `$STUB_GH_TOKEN` (exit 1 when empty).
fn stubs(dir: &Path) -> PathBuf {
    let bin = dir.join("bin");
    std::fs::create_dir_all(&bin).unwrap();
    for (name, var) in [("az", "STUB_AZ_TOKEN"), ("gh", "STUB_GH_TOKEN")] {
        let p = bin.join(name);
        std::fs::write(&p, format!("#!/bin/sh\n[ -n \"${var}\" ] && echo \"${var}\" || exit 1\n")).unwrap();
        std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o755)).unwrap();
    }
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

/// Run `ship tag <args>` hermetically: stub CLIs, no inherited platform, token or API env.
fn ship_tag(dir: &Scratch, env: &[(&str, &str)], args: &[&str]) -> Run {
    let path = format!("{}:{}", stubs(&dir.0).display(), std::env::var("PATH").unwrap());
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    c.current_dir(&dir.0)
        .arg("tag")
        .args(args)
        .env("PATH", path)
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env_remove("SHIP_PLATFORM")
        .env_remove("SHIP_ADO_API_URL")
        .env_remove("SHIP_GITHUB_API_URL")
        .env_remove("AZURE_DEVOPS_EXT_PAT")
        .env_remove("AZURE_DEVOPS_PAT")
        .env_remove("GH_TOKEN")
        .env_remove("GITHUB_TOKEN")
        .env_remove("STUB_AZ_TOKEN")
        .env_remove("STUB_GH_TOKEN")
        .stdin(Stdio::null());
    c.envs(env.iter().copied());
    Run { out: c.output().unwrap() }
}

/// Azure: the `az` token is `TOKEN`, no PAT.
fn az(dir: &Scratch, m: &Mock, args: &[&str]) -> Run {
    ship_tag(dir, &[("SHIP_ADO_API_URL", &m.base), ("STUB_AZ_TOKEN", TOKEN)], args)
}

/// GitHub: `GH_TOKEN` is `TOKEN`.
fn gh(dir: &Scratch, m: &Mock, args: &[&str]) -> Run {
    ship_tag(dir, &[("SHIP_GITHUB_API_URL", &m.base), ("GH_TOKEN", TOKEN)], args)
}

fn no_secrets(run: &Run) {
    for s in [run.stdout(), run.stderr()] {
        for secret in [TOKEN, PAT, PAT_B64] {
            assert!(!s.contains(secret), "{secret} leaked in {s}");
        }
    }
}

// ---- Azure ----

#[test]
fn azure_add_posts_one_label_per_tag_deduped() {
    let r = repo("az-add", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["9", "--add", "a,b", "--add", "a"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_added=a\ntag_added=b\n");
    assert_eq!(
        m.paths(),
        [format!("POST {AZ_LABELS}?api-version=7.1"), format!("POST {AZ_LABELS}?api-version=7.1")]
    );
    let reqs = m.requests();
    assert_eq!(reqs[0].json(), serde_json::json!({"name": "a"}));
    assert_eq!(reqs[1].json(), serde_json::json!({"name": "b"}));
    assert_eq!(reqs[0].headers.get("content-type").map(String::as_str), Some("application/json"));
    assert!(reqs.iter().all(|q| q.auth() == format!("Bearer {TOKEN}")), "{reqs:?}");
    no_secrets(&run);
}

#[test]
fn azure_list_is_the_default() {
    let r = repo("az-list", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["9"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "platform=azure\none\ntwo\n");
    assert_eq!(m.paths(), [format!("GET {AZ_LABELS}?api-version=7.1")]);
}

#[test]
fn azure_add_remove_list_in_that_order() {
    let r = repo("az-all", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["9", "--add", "hotfix", "--remove", "wip", "--list"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_added=hotfix\ntag_removed=wip\nplatform=azure\none\ntwo\n");
    assert_eq!(
        m.paths(),
        [
            format!("POST {AZ_LABELS}?api-version=7.1"),
            format!("DELETE {AZ_LABELS}/wip?api-version=7.1"),
            format!("GET {AZ_LABELS}?api-version=7.1"),
        ]
    );
    assert_eq!(m.requests()[1].body, "");
}

#[test]
fn azure_add_then_list_flag() {
    let r = repo("az-addlist", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["--pr", "9", "--add", "hotfix", "--list"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_added=hotfix\nplatform=azure\none\ntwo\n");
}

#[test]
fn azure_remove_encodes_the_name() {
    let r = repo("az-enc", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["9", "--remove", "do not/merge"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_removed=do not/merge\n");
    assert_eq!(m.paths(), [format!("DELETE {AZ_LABELS}/do%20not%2Fmerge?api-version=7.1")]);
}

#[test]
fn azure_add_failure_is_fatal_and_stops_the_run() {
    let r = repo("az-500", ADO_URL);
    let m = Mock::start(|q| (q.method == "POST").then(|| reply(500, r#"{"message":"boom"}"#)));
    let run = az(&r, &m, &["9", "--add", "a,b", "--remove", "x"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert_eq!(run.stderr().trim(), "ship-tag failed: HTTP 500: boom");
    assert_eq!(m.requests().len(), 1, "no second add, no remove after a failed add");
    no_secrets(&run);
}

#[test]
fn azure_partial_add_failure_keeps_the_first_line_and_stops() {
    let r = repo("az-partial", ADO_URL);
    let m = Mock::start(|q| {
        (q.method == "POST" && q.body.contains(r#""b""#)).then(|| reply(500, r#"{"message":"boom"}"#))
    });
    let run = az(&r, &m, &["9", "--add", "a,b", "--remove", "x", "--list"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "tag_added=a\n");
    assert_eq!(run.stderr().trim(), "ship-tag failed: HTTP 500: boom");
    assert_eq!(m.requests().len(), 2, "no DELETE or GET after the failed add: {:?}", m.paths());
}

#[test]
fn azure_remove_accepts_204_with_an_empty_body() {
    let r = repo("az-204", ADO_URL);
    let m = Mock::start(|q| (q.method == "DELETE").then(|| reply(204, "")));
    let run = az(&r, &m, &["9", "--remove", "wip"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_removed=wip\n");
    assert_eq!(run.stderr(), "");
}

#[test]
fn azure_404_on_add_or_list_is_an_error_not_a_success() {
    let r = repo("az-404a", ADO_URL);
    let m = Mock::start(|_| Some(reply(404, r#"{"message":"TF401180: no such pull request"}"#)));
    let run = az(&r, &m, &["9", "--add", "a"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "", "no tag_added= for a 404");
    assert!(run.stderr().starts_with("ship-tag failed: HTTP 404"), "{}", run.stderr());

    let run = az(&r, &m, &["9"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "", "no platform= line for a failed list");
    assert!(run.stderr().starts_with("ship-tag failed: HTTP 404"), "{}", run.stderr());
}

#[test]
fn azure_remove_failure_warns_and_goes_on() {
    let r = repo("az-rm404", ADO_URL);
    let m = Mock::start(|q| {
        (q.method == "DELETE" && q.path.contains("/gone?")).then(|| reply(404, r#"{"message":"not on this PR"}"#))
    });
    let run = az(&r, &m, &["9", "--remove", "gone,wip"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_removed=wip\n");
    assert_eq!(run.stderr().trim(), ">> could not remove 'gone': HTTP 404: not on this PR");
    assert_eq!(m.requests().len(), 2);
}

#[test]
fn azure_falls_back_to_the_pat_and_stays_on_it() {
    let r = repo("az-fallback", ADO_URL);
    let m = Mock::start(|q| (q.auth() == format!("Bearer {TOKEN}")).then(|| reply(401, r#"{"message":"nope"}"#)));
    let run = ship_tag(
        &r,
        &[("SHIP_ADO_API_URL", &m.base), ("STUB_AZ_TOKEN", TOKEN), ("AZURE_DEVOPS_EXT_PAT", PAT)],
        &["9", "--add", "a", "--list"],
    );
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_added=a\nplatform=azure\none\ntwo\n");
    assert_eq!(run.stderr().trim(), ">> bearer auth failed (401/403); falling back to pat");
    let auths: Vec<String> = m.requests().iter().map(|q| q.auth().to_string()).collect();
    assert_eq!(
        auths,
        [format!("Bearer {TOKEN}"), format!("Basic {PAT_B64}"), format!("Basic {PAT_B64}")]
    );
    no_secrets(&run);
}

#[test]
fn azure_rejected_sign_in_page_with_no_credential_left_fails() {
    let r = repo("az-203", ADO_URL);
    let m = Mock::start(|_| Some(reply(203, "<html>sign in</html>")));
    let run = az(&r, &m, &["9", "--add", "a"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().starts_with("ship-tag failed: HTTP 203"), "{}", run.stderr());
    no_secrets(&run);
}

#[test]
fn azure_without_a_credential_exits_1_before_any_request() {
    let r = repo("az-nocred", ADO_URL);
    let m = Mock::happy();
    let run = ship_tag(&r, &[("SHIP_ADO_API_URL", &m.base)], &["9"]);
    assert_eq!(run.code(), 1);
    assert_eq!(
        run.stderr().trim(),
        "no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)"
    );
    assert!(m.requests().is_empty());
}

#[test]
fn cleartext_api_seam_is_refused() {
    let r = repo("az-clear", ADO_URL);
    let run = ship_tag(&r, &[("SHIP_ADO_API_URL", "http://example.com"), ("STUB_AZ_TOKEN", TOKEN)], &["9"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().starts_with("ship-tag failed: refusing SHIP_ADO_API_URL"), "{}", run.stderr());
    no_secrets(&run);
}

// ---- GitHub ----

#[test]
fn github_add_is_one_post_with_every_tag() {
    let r = repo("gh-add", GH_URL);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "--add", "new-label"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_added=new-label\n");
    assert_eq!(m.paths(), ["POST /repos/acme/widgets/issues/7/labels"]);
    assert_eq!(m.requests()[0].json(), serde_json::json!({"labels": ["new-label"]}));
    assert_eq!(m.requests()[0].auth(), format!("Bearer {TOKEN}"));
    no_secrets(&run);

    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "--add", "a, b", "--add", "b,c"]);
    assert_eq!(run.stdout(), "tag_added=a\ntag_added=b\ntag_added=c\n");
    assert_eq!(m.requests().len(), 1);
    assert_eq!(m.requests()[0].json(), serde_json::json!({"labels": ["a", "b", "c"]}));
}

#[test]
fn github_remove_of_a_missing_label_warns_and_exits_0() {
    let r = repo("gh-rm404", GH_URL);
    let m = Mock::start(|q| (q.method == "DELETE").then(|| reply(404, r#"{"message":"Label does not exist"}"#)));
    let run = gh(&r, &m, &["--pr", "7", "--remove", "gone"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "");
    assert_eq!(run.stderr().trim(), ">> could not remove 'gone': HTTP 404: Label does not exist");
    assert_eq!(m.paths(), ["DELETE /repos/acme/widgets/issues/7/labels/gone"]);
    no_secrets(&run);
}

#[test]
fn github_remove_then_list_and_encoding() {
    let r = repo("gh-rm", GH_URL);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "--remove", "needs review", "--list"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "tag_removed=needs review\nplatform=github\nbug\nwip\n");
    assert_eq!(
        m.paths(),
        [
            "DELETE /repos/acme/widgets/issues/7/labels/needs%20review",
            "GET /repos/acme/widgets/issues/7/labels"
        ]
    );
    no_secrets(&run);
}

#[test]
fn github_list_is_the_default() {
    let r = repo("gh-list", GH_URL);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "platform=github\nbug\nwip\n");
    assert_eq!(m.paths(), ["GET /repos/acme/widgets/issues/7/labels"]);
}

#[test]
fn github_add_failure_is_fatal() {
    let r = repo("gh-500", GH_URL);
    let m = Mock::start(|q| (q.method == "POST").then(|| reply(500, r#"{"message":"boom"}"#)));
    let run = gh(&r, &m, &["7", "--add", "a", "--remove", "x"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert_eq!(run.stderr().trim(), "ship-tag failed: HTTP 500: boom");
    assert_eq!(m.requests().len(), 1);
    no_secrets(&run);
}

#[test]
fn github_list_failure_is_fatal() {
    let r = repo("gh-list404", GH_URL);
    let m = Mock::start(|_| Some(reply(404, r#"{"message":"Not Found"}"#)));
    let run = gh(&r, &m, &["7"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert_eq!(run.stderr().trim(), "ship-tag failed: HTTP 404: Not Found");
    no_secrets(&run);
}

#[test]
fn github_list_with_a_non_array_body_is_an_error() {
    let r = repo("gh-nonarray", GH_URL);
    let m = Mock::start(|q| (q.method == "GET").then(|| reply(200, r#"{"message":"x"}"#)));
    let run = gh(&r, &m, &["7"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert_eq!(run.stderr().trim(), "ship-tag failed: unexpected response listing the labels");
    no_secrets(&run);
}

#[test]
fn github_cleartext_api_seam_is_refused() {
    let r = repo("gh-clear", GH_URL);
    let run = ship_tag(&r, &[("SHIP_GITHUB_API_URL", "http://example.com"), ("GH_TOKEN", TOKEN)], &["7"]);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().starts_with("ship-tag failed: refusing SHIP_GITHUB_API_URL"), "{}", run.stderr());
    no_secrets(&run);
}

#[test]
fn dot_names_are_never_sent_as_a_remove_path() {
    for (url, is_az) in [(ADO_URL, true), (GH_URL, false)] {
        let r = repo("dots", url);
        let m = Mock::happy();
        let run = if is_az { az(&r, &m, &["9", "--remove", ".,..,ok"]) } else { gh(&r, &m, &["7", "--remove", ".,..,ok"]) };
        assert_eq!(run.code(), 0, "{}", run.stderr());
        assert_eq!(run.stdout(), "tag_removed=ok\n");
        assert!(run.stderr().contains(">> could not remove '.': invalid tag name"), "{}", run.stderr());
        assert!(run.stderr().contains(">> could not remove '..': invalid tag name"), "{}", run.stderr());
        let deletes: Vec<_> = m.requests().into_iter().filter(|q| q.method == "DELETE").collect();
        assert_eq!(deletes.len(), 1, "{:?}", m.paths());
        assert!(deletes[0].path.contains("/labels/ok"), "{}", deletes[0].path);
    }
}

#[test]
fn list_flag_may_repeat() {
    let r = repo("list-twice", GH_URL);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "--list", "--list"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.stdout(), "platform=github\nbug\nwip\n");
}

#[test]
fn pr_flag_wins_over_a_positional_id() {
    let r = repo("pr-wins", GH_URL);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "--pr", "5"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(m.paths(), ["GET /repos/acme/widgets/issues/5/labels"]);
}

#[test]
fn closed_stdout_still_applies_tags() {
    let r = repo("pipe", ADO_URL);
    let m = Mock::happy();
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    let path = format!("{}:{}", stubs(&r.0).display(), std::env::var("PATH").unwrap());
    c.current_dir(&r.0)
        .args(["tag", "9", "--add", "a,b", "--remove", "x"])
        .env("PATH", path)
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("SHIP_ADO_API_URL", &m.base)
        .env("STUB_AZ_TOKEN", TOKEN)
        .env_remove("SHIP_PLATFORM")
        .env_remove("AZURE_DEVOPS_EXT_PAT")
        .env_remove("AZURE_DEVOPS_PAT")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = c.spawn().unwrap();
    drop(child.stdout.take()); // the reader is gone before ship prints anything
    let out = child.wait_with_output().unwrap();
    // A closed pipe is the reader's choice, not a failure.
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(
        m.paths(),
        [
            format!("POST {AZ_LABELS}?api-version=7.1"),
            format!("POST {AZ_LABELS}?api-version=7.1"),
            format!("DELETE {AZ_LABELS}/x?api-version=7.1"),
        ]
    );
}

#[test]
fn github_without_a_token_exits_1() {
    let r = repo("gh-notoken", GH_URL);
    let m = Mock::happy();
    let run = ship_tag(&r, &[("SHIP_GITHUB_API_URL", &m.base)], &["7"]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stderr().trim(), "no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`");
    assert!(m.requests().is_empty());
}

// ---- arguments and platform ----

#[test]
fn no_id_is_a_usage_error_with_no_request() {
    let r = repo("noid", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["--add", "a"]);
    assert_eq!(run.code(), 2);
    assert_eq!(run.stderr().trim(), "a pull request id is required (positional or --pr)");
    assert!(m.requests().is_empty());
}

#[test]
fn unknown_and_extra_args_exit_2() {
    let r = repo("badargs", ADO_URL);
    let m = Mock::happy();
    for args in [&["abc"][..], &["9", "--bogus"], &["9", "10"], &["--pr", "x1"]] {
        let run = az(&r, &m, args);
        assert_eq!(run.code(), 2, "{args:?}: {}", run.stderr());
        assert_eq!(run.stdout(), "");
    }
    assert!(m.requests().is_empty());
}

#[test]
fn a_remote_starting_with_a_dash_exits_2() {
    let r = repo("badremote", ADO_URL);
    let m = Mock::happy();
    let run = az(&r, &m, &["9", "-r", "--upload-pack=x"]);
    assert_eq!(run.code(), 2);
    assert!(run.stderr().contains("invalid remote"), "{}", run.stderr());
    assert!(m.requests().is_empty());
}

#[test]
fn the_remote_flag_picks_the_platform() {
    let r = repo("remote", "https://example.com/x.git");
    git(&r.0, &["remote", "add", "gh", GH_URL]);
    let m = Mock::happy();
    let run = gh(&r, &m, &["7", "-r", "gh"]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stdout().starts_with("platform=github\n"));
}

#[test]
fn unknown_platform_exits_1() {
    let r = repo("unknown", "https://example.com/x.git");
    let m = Mock::happy();
    let run = az(&r, &m, &["9"]);
    assert_eq!(run.code(), 1);
    assert_eq!(
        run.stderr().trim(),
        "unknown platform for remote 'origin' (https://example.com/x.git); set SHIP_PLATFORM=azure|github"
    );
    assert!(m.requests().is_empty());
}
