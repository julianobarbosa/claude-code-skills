//! Integration tests for `ship push`: real binary, scratch repos, local bare remotes,
//! and a stub `az` first on PATH. No bun, no network.

use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};

const TOKEN: &str = "SECRET-TOKEN-123";
static COUNTER: AtomicUsize = AtomicUsize::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-push-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }

    /// Repo on `main` with one commit, plus a bare remote named `origin`
    /// (not yet pushed), and a feature branch `feat/x` checked out.
    fn repo_with_bare(tag: &str) -> (Self, Self) {
        let r = Self::new(tag);
        git(&r.0, &["init", "-q", "-b", "main"]);
        write(&r.0, "init.txt", "init\n");
        git(&r.0, &["add", "init.txt"]);
        commit(&r.0, "init");
        let bare = Self::new(&format!("{tag}-bare"));
        git(&bare.0, &["init", "-q", "--bare", "-b", "main"]);
        git(&r.0, &["remote", "add", "origin", bare.0.to_str().unwrap()]);
        git(&r.0, &["checkout", "-q", "-b", "feat/x"]);
        (r, bare)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn isolate(c: &mut Command) -> &mut Command {
    c.env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env_remove("GIT_DIR")
        .env_remove("GIT_WORK_TREE")
        .env_remove("GIT_INDEX_FILE")
        .env_remove("GIT_CONFIG_COUNT")
        .env_remove("SHIP_PLATFORM")
}

fn git(dir: &Path, args: &[&str]) {
    let st = isolate(Command::new("git").current_dir(dir).args(args)).status().unwrap();
    assert!(st.success(), "git {args:?} failed");
}

fn git_out(dir: &Path, args: &[&str]) -> String {
    let o = isolate(Command::new("git").current_dir(dir).args(args)).output().unwrap();
    String::from_utf8_lossy(&o.stdout).trim().to_string()
}

fn commit(dir: &Path, msg: &str) {
    git(
        dir,
        &[
            "-c", "user.name=t", "-c", "user.email=t@example.com",
            "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
            "commit", "-q", "-m", msg,
        ],
    );
}

fn write(dir: &Path, name: &str, body: &str) {
    std::fs::write(dir.join(name), body).unwrap();
}

fn script(path: &Path, body: &str) {
    std::fs::write(path, format!("#!/bin/sh\n{body}\n")).unwrap();
    std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o755)).unwrap();
}

/// A dir holding a stub `az`: prints the token, or exits 1 when `token` is None.
fn stub_az(token: Option<&str>) -> Scratch {
    let d = Scratch::new("az");
    let rec = d.0.join("argv");
    match token {
        Some(t) => script(&d.0.join("az"), &format!("echo \"$@\" > {}\necho {t}", rec.display())),
        None => script(&d.0.join("az"), &format!("echo \"$@\" > {}\nexit 1", rec.display())),
    }
    d
}

/// A dir with a `git` wrapper that appends each invocation's argv (one arg per
/// line, then `---`) to `log` and execs the real git.
fn git_wrapper() -> Scratch {
    let d = Scratch::new("gitw");
    let real = String::from_utf8(Command::new("sh").args(["-c", "command -v git"]).output().unwrap().stdout)
        .unwrap()
        .trim()
        .to_string();
    let log = d.0.join("log");
    script(
        &d.0.join("git"),
        &format!("for a in \"$@\"; do printf '%s\\n' \"$a\" >> {l}; done\necho --- >> {l}\n[ \"$1\" = push ] && echo \"$GIT_CONFIG_COUNT\" >> {l}.count\nexec {real} \"$@\"", l = log.display()),
    );
    d
}

/// Recorded git invocations, each as its argv.
fn wrapper_calls(w: &Scratch) -> Vec<Vec<String>> {
    let log = std::fs::read_to_string(w.0.join("log")).unwrap_or_default();
    log.split("---\n")
        .filter(|b| !b.is_empty())
        .map(|b| b.lines().map(String::from).collect())
        .collect()
}

fn push_calls(w: &Scratch) -> Vec<Vec<String>> {
    wrapper_calls(w).into_iter().filter(|c| c.first().map(String::as_str) == Some("push")).collect()
}

/// pre-receive hook that records the Bearer-related env it inherited from the push.
fn env_recording_hook(bare: &Path) -> PathBuf {
    let hooks = bare.join("hooks");
    std::fs::create_dir_all(&hooks).unwrap();
    let rec = bare.join("env.rec");
    script(
        &hooks.join("pre-receive"),
        &format!("env | grep -E '^GIT_(CONFIG_|TERMINAL_PROMPT)' | sort > {}", rec.display()),
    );
    rec
}

/// Value of `name` from an `env.rec` file; exact, so a trailing newline would show.
fn rec_get(rec: &Path, name: &str) -> Option<String> {
    std::fs::read_to_string(rec)
        .unwrap()
        .lines()
        .find_map(|l| l.strip_prefix(&format!("{name}=")).map(String::from))
}

/// A bare remote whose `feat/x` was advanced by another clone, and `r` diverged
/// from it. Returns (repo, bare, remote head).
fn diverged(tag: &str) -> (Scratch, Scratch, String) {
    let (r, bare) = Scratch::repo_with_bare(tag);
    git(&r.0, &["push", "-q", "origin", "feat/x"]);
    let other = Scratch::new("other");
    git(&other.0, &["clone", "-q", bare.0.to_str().unwrap(), "."]);
    git(&other.0, &["checkout", "-q", "feat/x"]);
    write(&other.0, "o.txt", "o\n");
    git(&other.0, &["add", "o.txt"]);
    commit(&other.0, "other");
    git(&other.0, &["push", "-q", "origin", "feat/x"]);
    let head = git_out(&bare.0, &["rev-parse", "feat/x"]);
    write(&r.0, "l.txt", "l\n");
    git(&r.0, &["add", "l.txt"]);
    commit(&r.0, "local");
    (r, bare, head)
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

fn push(dir: &Path, args: &[&str], platform: Option<&str>, az: Option<&Path>) -> Run {
    let path = az.map(|az| format!("{}:{}", az.display(), std::env::var("PATH").unwrap_or_default()));
    push_with(dir, args, platform, path, &[])
}

/// Like [`push`], with a full `PATH` override and extra env applied after `isolate`.
fn push_with(
    dir: &Path,
    args: &[&str],
    platform: Option<&str>,
    path: Option<String>,
    env: &[(&str, &str)],
) -> Run {
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    isolate(c.current_dir(dir)).arg("push").args(args).stdin(Stdio::null());
    if let Some(p) = platform {
        c.env("SHIP_PLATFORM", p);
    }
    if let Some(p) = path {
        c.env("PATH", p);
    }
    c.envs(env.iter().copied());
    Run { out: c.output().unwrap() }
}

fn orig_path() -> String {
    std::env::var("PATH").unwrap_or_default()
}

fn assert_no_token(r: &Run, repo: &Path) {
    assert!(!r.stdout().contains(TOKEN), "token in stdout");
    assert!(!r.stderr().contains(TOKEN), "token in stderr");
    let cfg = std::fs::read_to_string(repo.join(".git/config")).unwrap();
    assert!(!cfg.contains(TOKEN), "token in .git/config");
}

#[test]
fn github_push_sets_upstream_and_prints_normal() {
    let (r, bare) = Scratch::repo_with_bare("gh");
    let run = push(&r.0, &[], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=normal");
    assert!(run.stderr().contains(">> pushing feat/x -> origin (github)"));
    assert_eq!(git_out(&r.0, &["rev-parse", "--abbrev-ref", "@{u}"]), "origin/feat/x");
    assert_eq!(
        git_out(&bare.0, &["rev-parse", "feat/x"]),
        git_out(&r.0, &["rev-parse", "HEAD"])
    );
}

#[test]
fn azure_logged_in_uses_bearer_and_never_leaks_token() {
    let (r, _bare) = Scratch::repo_with_bare("az-ok");
    let az = stub_az(Some(TOKEN));
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=oauth-bearer");
    assert!(run.stderr().contains(">> pushing feat/x -> origin (azure)"));
    assert!(!run.stderr().contains("trying the stored git credential"));
    assert_no_token(&run, &r.0);
}

#[test]
fn azure_logged_out_falls_back_to_plain_push() {
    let (r, _bare) = Scratch::repo_with_bare("az-out");
    let az = stub_az(None);
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=normal");
    assert!(run.stderr().contains(
        ">> could not mint an az token (is 'az login' done?); trying the stored git credential"
    ));
}

#[test]
fn azure_bearer_rejected_falls_back_once() {
    let (r, bare) = Scratch::repo_with_bare("az-rej");
    // A local push passes the caller's env to the receiving hook, so the hook can
    // see the Bearer config and reject only that attempt.
    let hooks = bare.0.join("hooks");
    std::fs::create_dir_all(&hooks).unwrap();
    let marker = bare.0.join("attempts");
    script(
        &hooks.join("pre-receive"),
        &format!(
            "echo x >> {}\ncase \"$GIT_CONFIG_VALUE_1\" in *Bearer*) echo rejected >&2; exit 1;; esac",
            marker.display()
        ),
    );
    let az = stub_az(Some(TOKEN));
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=normal");
    assert!(run.stderr().contains(">> OAuth Bearer push failed; trying the stored git credential"));
    let attempts = std::fs::read_to_string(&marker).unwrap().lines().count();
    assert_eq!(attempts, 2, "expected exactly one Bearer attempt and one plain push");
    assert_no_token(&run, &r.0);
}

#[test]
fn azure_both_pushes_fail_exits_1() {
    let (r, bare) = Scratch::repo_with_bare("az-fail");
    let hooks = bare.0.join("hooks");
    std::fs::create_dir_all(&hooks).unwrap();
    script(&hooks.join("pre-receive"), "exit 1");
    let az = stub_az(Some(TOKEN));
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("push failed"));
    assert_no_token(&run, &r.0);
}

#[test]
fn rejected_push_never_forces() {
    let (r, bare, remote_head) = diverged("diverge");

    let run = push(&r.0, &[], Some("github"), None);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("push failed"));
    assert_eq!(git_out(&bare.0, &["rev-parse", "feat/x"]), remote_head);
}

#[test]
fn remote_and_branch_flags_long_and_short() {
    let (r, _bare) = Scratch::repo_with_bare("flags");
    let up = Scratch::new("up-bare");
    git(&up.0, &["init", "-q", "--bare", "-b", "main"]);
    git(&r.0, &["remote", "add", "up", up.0.to_str().unwrap()]);
    git(&r.0, &["branch", "other"]);

    let run = push(&r.0, &["-r", "up", "-b", "other"], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains(">> pushing other -> up (github)"));
    assert!(!git_out(&up.0, &["rev-parse", "--verify", "other"]).is_empty());

    let run = push(&r.0, &["--remote", "up", "--branch", "feat/x"], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(run.stderr().contains(">> pushing feat/x -> up (github)"));
}

#[test]
fn missing_remote_reports_unknown_and_fails() {
    let (r, _bare) = Scratch::repo_with_bare("nope");
    let run = push(&r.0, &["-r", "nope"], None, None);
    assert_eq!(run.code(), 1);
    assert!(run.stderr().contains(">> pushing feat/x -> nope (unknown)"));
    assert!(run.stderr().contains("push failed"));
    assert_eq!(run.stdout(), "");
}

#[test]
fn unknown_flag_exits_2_and_help_exits_0() {
    let (r, _bare) = Scratch::repo_with_bare("args");
    assert_eq!(push(&r.0, &["--bogus"], None, None).code(), 2);
    let help = push(&r.0, &["--help"], None, None);
    assert_eq!(help.code(), 0);
    assert!(help.stdout().contains("--remote"));
}

/// git's own "set up to track" line also lands on the inherited stdout (the TS does
/// the same); the contract is that `push_ok=` is the last line and appears once.
fn assert_push_ok(r: &Run, want: &str) {
    let out = r.stdout();
    assert_eq!(out.lines().last(), Some(want), "stdout: {out:?}");
    assert_eq!(out.lines().filter(|l| l.starts_with("push_ok=")).count(), 1);
}

#[test]
fn azure_never_forces_on_diverged_history() {
    let (r, bare, remote_head) = diverged("az-diverge");
    let az = stub_az(Some(TOKEN));
    let w = git_wrapper();
    let path = format!("{}:{}:{}", az.0.display(), w.0.display(), orig_path());
    let run = push_with(&r.0, &[], Some("azure"), Some(path), &[]);
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("push failed"));
    assert_eq!(git_out(&bare.0, &["rev-parse", "feat/x"]), remote_head);
    let pushes = push_calls(&w);
    assert_eq!(pushes.len(), 2, "one Bearer attempt and one plain push: {pushes:?}");
    assert!(pushes.iter().flatten().all(|a| !a.starts_with('+') && !a.contains("force")));
    assert_no_token(&run, &r.0);
}

#[test]
fn plus_refspec_branch_is_refused_before_any_push() {
    let (r, bare, remote_head) = diverged("plus");
    git(&r.0, &["branch", "main2"]);
    let w = git_wrapper();
    let path = format!("{}:{}", w.0.display(), orig_path());
    let run = push_with(&r.0, &["-b", "+feat/x"], Some("github"), Some(path), &[]);
    assert_eq!(run.code(), 2);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("invalid branch '+feat/x'"), "{}", run.stderr());
    assert_eq!(git_out(&bare.0, &["rev-parse", "feat/x"]), remote_head);
    assert!(push_calls(&w).is_empty());
}

#[test]
fn option_like_and_refspec_inputs_are_refused() {
    let (r, _bare) = Scratch::repo_with_bare("optlike");
    let w = git_wrapper();
    let path = format!("{}:{}", w.0.display(), orig_path());
    for args in [
        vec!["--remote=--force"],
        vec!["-r=--force"],
        vec!["--branch=--force"],
        vec!["-b", "feat/x:main"],
    ] {
        let run = push_with(&r.0, &args, Some("github"), Some(path.clone()), &[]);
        assert_eq!(run.code(), 2, "{args:?}: {}", run.stderr());
        assert_eq!(run.stdout(), "");
        assert!(run.stderr().contains("invalid"), "{args:?}: {}", run.stderr());
    }
    assert!(push_calls(&w).is_empty());
}

#[test]
fn az_is_invoked_with_the_exact_args_and_header_is_exact() {
    let (r, bare) = Scratch::repo_with_bare("exact");
    let rec = env_recording_hook(&bare.0);
    let az = stub_az(Some(TOKEN));
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=oauth-bearer");
    let argv = std::fs::read_to_string(az.0.join("argv")).unwrap();
    assert_eq!(
        argv.trim_end_matches('\n'),
        "account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv"
    );
    // File remote: unscoped key, header value exact, prompts disabled on this attempt.
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_0").as_deref(), Some("credential.helper"));
    assert_eq!(rec_get(&rec, "GIT_CONFIG_VALUE_0").as_deref(), Some(""));
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_1").as_deref(), Some("http.extraHeader"));
    assert_eq!(
        rec_get(&rec, "GIT_CONFIG_VALUE_1").as_deref(),
        Some("Authorization: Bearer SECRET-TOKEN-123")
    );
    assert_eq!(rec_get(&rec, "GIT_TERMINAL_PROMPT").as_deref(), Some("0"));
}

#[test]
fn plain_fallback_push_has_no_bearer_env_and_prompting_stays_on() {
    let (r, bare) = Scratch::repo_with_bare("plainenv");
    let rec = env_recording_hook(&bare.0);
    let az = stub_az(None);
    let run = push(&r.0, &[], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_0"), None);
    assert_eq!(rec_get(&rec, "GIT_TERMINAL_PROMPT"), None);
}

#[test]
fn token_never_appears_in_any_git_argv() {
    let (r, _bare) = Scratch::repo_with_bare("argv");
    let az = stub_az(Some(TOKEN));
    let w = git_wrapper();
    let path = format!("{}:{}:{}", az.0.display(), w.0.display(), orig_path());
    let run = push_with(&r.0, &[], Some("azure"), Some(path), &[]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=oauth-bearer");
    let calls = wrapper_calls(&w);
    assert!(calls.iter().flatten().all(|a| !a.contains(TOKEN) && a != "-c"), "{calls:?}");
    assert_eq!(push_calls(&w), vec![vec!["push", "-u", "--", "origin", "feat/x"]]);
}

#[test]
fn azure_without_az_on_path_falls_back() {
    let (r, _bare) = Scratch::repo_with_bare("noaz");
    let real = String::from_utf8(Command::new("sh").args(["-c", "command -v git"]).output().unwrap().stdout)
        .unwrap()
        .trim()
        .to_string();
    let only_git = Scratch::new("onlygit");
    std::os::unix::fs::symlink(real, only_git.0.join("git")).unwrap();
    let run = push_with(&r.0, &[], Some("azure"), Some(only_git.0.display().to_string()), &[]);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=normal");
    assert!(run.stderr().contains(
        ">> could not mint an az token (is 'az login' done?); trying the stored git credential"
    ));
}

#[test]
fn callers_own_git_config_env_survives_the_bearer_push() {
    let (r, bare) = Scratch::repo_with_bare("callercfg");
    let w = git_wrapper();
    let rec = env_recording_hook(&bare.0);
    let az = stub_az(Some(TOKEN));
    let path = format!("{}:{}:{}", az.0.display(), w.0.display(), orig_path());
    let env = [
        ("GIT_CONFIG_COUNT", "1"),
        ("GIT_CONFIG_KEY_0", "user.name"),
        ("GIT_CONFIG_VALUE_0", "callerval"),
    ];
    let run = push_with(&r.0, &[], Some("azure"), Some(path), &env);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_push_ok(&run, "push_ok=oauth-bearer");
    let counts = std::fs::read_to_string(w.0.join("log.count")).unwrap();
    assert_eq!(counts.lines().next(), Some("3"), "count seen by the Bearer push (git strips it from hooks)");
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_0").as_deref(), Some("user.name"));
    assert_eq!(rec_get(&rec, "GIT_CONFIG_VALUE_0").as_deref(), Some("callerval"));
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_1").as_deref(), Some("credential.helper"));
    assert_eq!(rec_get(&rec, "GIT_CONFIG_KEY_2").as_deref(), Some("http.extraHeader"));
    assert_eq!(
        rec_get(&rec, "GIT_CONFIG_VALUE_2").as_deref(),
        Some("Authorization: Bearer SECRET-TOKEN-123")
    );
}
