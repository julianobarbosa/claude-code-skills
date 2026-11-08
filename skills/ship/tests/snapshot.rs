//! Integration tests for `ship snapshot`: real binary, scratch repos, local bare
//! remotes, and a stub `az` first on PATH. No bun, no network.

use regex::Regex;
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
        let dir = std::env::temp_dir().join(format!("ship-snap-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }

    /// Repo on `main` with one commit.
    fn repo(tag: &str) -> Self {
        let r = Self::new(tag);
        git(&r.0, &["init", "-q", "-b", "main"]);
        write(&r.0, "init.txt", "init\n");
        git(&r.0, &["add", "init.txt"]);
        commit(&r.0, "init");
        r
    }

    /// Repo plus a bare remote named `origin`.
    fn repo_with_bare(tag: &str) -> (Self, Self) {
        let r = Self::repo(tag);
        let bare = Self::new(&format!("{tag}-bare"));
        git(&bare.0, &["init", "-q", "--bare", "-b", "main"]);
        git(&r.0, &["remote", "add", "origin", bare.0.to_str().unwrap()]);
        (r, bare)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

/// Isolated git config with a committer/tagger identity and signing off, so
/// `git tag -a` works on any machine.
fn isolate(c: &mut Command) -> &mut Command {
    c.env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_AUTHOR_NAME", "t")
        .env("GIT_AUTHOR_EMAIL", "t@example.com")
        .env("GIT_COMMITTER_NAME", "t")
        .env("GIT_COMMITTER_EMAIL", "t@example.com")
        .env("GIT_CONFIG_COUNT", "1")
        .env("GIT_CONFIG_KEY_0", "tag.gpgSign")
        .env("GIT_CONFIG_VALUE_0", "false")
        .env_remove("GIT_DIR")
        .env_remove("GIT_WORK_TREE")
        .env_remove("GIT_INDEX_FILE")
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
    git(dir, &["-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg]);
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
    match token {
        Some(t) => script(&d.0.join("az"), &format!("echo {t}")),
        None => script(&d.0.join("az"), "exit 1"),
    }
    d
}

struct Run(Output);

impl Run {
    fn stdout(&self) -> String {
        String::from_utf8_lossy(&self.0.stdout).into_owned()
    }
    fn stderr(&self) -> String {
        String::from_utf8_lossy(&self.0.stderr).into_owned()
    }
    fn code(&self) -> i32 {
        self.0.status.code().unwrap()
    }
    /// stdout as `key=value` lines, in order.
    fn kv(&self) -> Vec<(String, String)> {
        self.stdout()
            .lines()
            .map(|l| {
                let (k, v) = l.split_once('=').unwrap_or((l, ""));
                (k.to_string(), v.to_string())
            })
            .collect()
    }
    fn get(&self, key: &str) -> String {
        self.kv().into_iter().find(|(k, _)| k == key).map(|(_, v)| v).unwrap_or_default()
    }
}

fn snapshot(dir: &Path, args: &[&str], platform: Option<&str>, az: Option<&Path>) -> Run {
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    isolate(c.current_dir(dir)).arg("snapshot").args(args).stdin(Stdio::null());
    if let Some(p) = platform {
        c.env("SHIP_PLATFORM", p);
    }
    if let Some(az) = az {
        c.env("PATH", format!("{}:{}", az.display(), std::env::var("PATH").unwrap_or_default()));
    }
    Run(c.output().unwrap())
}

fn assert_no_token(r: &Run, repo: &Path) {
    assert!(!r.stdout().contains(TOKEN), "token in stdout");
    assert!(!r.stderr().contains(TOKEN), "token in stderr");
    let cfg = std::fs::read_to_string(repo.join(".git/config")).unwrap();
    assert!(!cfg.contains(TOKEN), "token in .git/config");
}

#[test]
fn default_name_is_dated_on_head_with_message_paragraphs() {
    let r = Scratch::repo("default");
    let run = snapshot(&r.0, &["-m", "why", "-m", "verified"], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let head = git_out(&r.0, &["rev-parse", "--short", "HEAD"]);
    let name = run.get("tag");
    assert!(Regex::new(r"^v\d{4}\.\d{2}\.\d{2}-\d{4}$").unwrap().is_match(&name), "{name}");

    let keys: Vec<_> = run.kv().into_iter().map(|(k, _)| k).collect();
    assert_eq!(keys, ["tag", "commit", "branch", "pushed"]);
    assert_eq!(run.get("commit"), head);
    assert_eq!(run.get("branch"), "main");
    assert_eq!(run.get("pushed"), "no");
    assert!(run.stderr().contains(&format!(">> created annotated tag {name} -> {head} (main)")));

    assert_eq!(git_out(&r.0, &["cat-file", "-t", &name]), "tag");
    assert_eq!(
        git_out(&r.0, &["rev-parse", &format!("{name}^{{commit}}")]),
        git_out(&r.0, &["rev-parse", "HEAD"])
    );
    let body = git_out(&r.0, &["tag", "-l", "--format=%(contents)", &name]);
    assert_eq!(body, format!("Snapshot {name} — main @ {head}\n\nwhy\n\nverified"));
}

#[test]
fn daily_name_has_no_time_part() {
    let r = Scratch::repo("daily");
    let run = snapshot(&r.0, &["--daily"], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let name = run.get("tag");
    assert!(Regex::new(r"^v\d{4}\.\d{2}\.\d{2}$").unwrap().is_match(&name), "{name}");
}

#[test]
fn exact_name_and_subject_only_without_messages() {
    let r = Scratch::repo("exact");
    let run = snapshot(&r.0, &["--name", "pre-migration"], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("tag"), "pre-migration");
    let head = git_out(&r.0, &["rev-parse", "--short", "HEAD"]);
    assert_eq!(git_out(&r.0, &["cat-file", "-t", "pre-migration"]), "tag");
    assert_eq!(
        git_out(&r.0, &["tag", "-l", "--format=%(contents)", "pre-migration"]),
        format!("Snapshot pre-migration — main @ {head}")
    );
}

#[test]
fn messages_are_passed_verbatim() {
    let r = Scratch::repo("verbatim");
    let run = snapshot(&r.0, &["--name", "v", "-m", "-x '$(touch pwned)' \"q\"", "--message", "line1\nline2"], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert!(!r.0.join("pwned").exists());
    let body = git_out(&r.0, &["tag", "-l", "--format=%(contents)", "v"]);
    assert!(body.ends_with("\n\n-x '$(touch pwned)' \"q\"\n\nline1\nline2"), "{body:?}");
}

#[test]
fn existing_tag_is_refused_with_exit_3_and_not_moved() {
    let r = Scratch::repo("collide");
    let run = snapshot(&r.0, &["--name", "t1"], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let before = git_out(&r.0, &["rev-parse", "t1"]);

    write(&r.0, "b.txt", "b\n");
    git(&r.0, &["add", "b.txt"]);
    commit(&r.0, "second");

    let run = snapshot(&r.0, &["--name", "t1", "-m", "again"], None, None);
    assert_eq!(run.code(), 3);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains(
        "tag 't1' already exists. Use --name <other>, or drop --daily for minute granularity."
    ));
    assert_eq!(git_out(&r.0, &["rev-parse", "t1"]), before);
}

#[test]
fn lightweight_tag_of_same_name_is_also_refused() {
    let r = Scratch::repo("light");
    git(&r.0, &["tag", "lw"]);
    let run = snapshot(&r.0, &["--name", "lw"], None, None);
    assert_eq!(run.code(), 3);
    assert_eq!(git_out(&r.0, &["cat-file", "-t", "lw"]), "commit");
}

#[test]
fn not_a_repo_or_no_commits_exits_2_with_empty_stdout() {
    let empty = Scratch::new("unborn");
    git(&empty.0, &["init", "-q", "-b", "main"]);
    let run = snapshot(&empty.0, &[], None, None);
    assert_eq!(run.code(), 2);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("not a git repo, or no commits yet — nothing to snapshot"));

    let outside = Scratch::new("outside");
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    isolate(c.current_dir(&outside.0)).arg("snapshot").env("GIT_CEILING_DIRECTORIES", outside.0.parent().unwrap());
    let run = Run(c.output().unwrap());
    assert_eq!(run.code(), 2);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("nothing to snapshot"));
}

#[test]
fn bad_names_are_refused_with_exit_2_and_nothing_created() {
    let (r, bare) = Scratch::repo_with_bare("badname");
    for name in ["+v1", "-x", "a:b", "a b", "a..b", "x.lock", "a~1", "HEAD"].iter() {
        let run = snapshot(&r.0, &["--push", &format!("--name={name}")], Some("github"), None);
        assert_eq!(run.code(), 2, "{name}: {}", run.stderr());
        assert_eq!(run.stdout(), "", "{name}");
        assert!(run.stderr().contains("invalid tag name"), "{name}: {}", run.stderr());
    }
    assert_eq!(git_out(&r.0, &["tag", "-l"]), "");
    assert_eq!(git_out(&bare.0, &["tag", "-l"]), "");
}

#[test]
fn github_push_puts_the_tag_on_the_remote() {
    let (r, bare) = Scratch::repo_with_bare("gh");
    let run = snapshot(&r.0, &["--name", "snap1", "--push"], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("pushed"), "yes");
    assert!(run.stderr().contains(">> pushing tag snap1 -> origin (github)"));
    assert_eq!(git_out(&bare.0, &["cat-file", "-t", "snap1"]), "tag");
    assert_eq!(
        git_out(&bare.0, &["rev-parse", "snap1^{commit}"]),
        git_out(&r.0, &["rev-parse", "HEAD"])
    );
    // `push -u` on a tag must not write branch tracking config.
    assert_eq!(git_out(&r.0, &["config", "--get-regexp", "^branch\\."]), "");
}

#[test]
fn azure_push_with_stub_token_reports_bearer_and_never_leaks() {
    let (r, bare) = Scratch::repo_with_bare("az-ok");
    let az = stub_az(Some(TOKEN));
    let run = snapshot(&r.0, &["--name", "snap1", "--push"], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("pushed"), "yes-oauth-bearer");
    assert!(run.stderr().contains(">> pushing tag snap1 -> origin (azure)"));
    assert_eq!(git_out(&bare.0, &["cat-file", "-t", "snap1"]), "tag");
    assert_no_token(&run, &r.0);
}

#[test]
fn azure_logged_out_falls_back_to_plain_push() {
    let (r, bare) = Scratch::repo_with_bare("az-out");
    let az = stub_az(None);
    let run = snapshot(&r.0, &["--name", "snap1", "--push"], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("pushed"), "yes");
    assert_eq!(git_out(&bare.0, &["cat-file", "-t", "snap1"]), "tag");
}

#[test]
fn failed_push_keeps_the_local_tag_and_exits_1() {
    let (r, bare) = Scratch::repo_with_bare("pushfail");
    let hooks = bare.0.join("hooks");
    std::fs::create_dir_all(&hooks).unwrap();
    script(&hooks.join("pre-receive"), "exit 1");
    let az = stub_az(Some(TOKEN));
    let run = snapshot(&r.0, &["--name", "snap1", "--push"], Some("azure"), Some(&az.0));
    assert_eq!(run.code(), 1);
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("tag 'snap1' created locally, but push failed"));
    assert_eq!(git_out(&r.0, &["cat-file", "-t", "snap1"]), "tag");
    assert_eq!(git_out(&bare.0, &["tag", "-l"]), "");
    assert_no_token(&run, &r.0);
}

#[test]
fn unknown_flag_exits_2_and_help_exits_0() {
    let r = Scratch::repo("args");
    assert_eq!(snapshot(&r.0, &["--bogus"], None, None).code(), 2);
    let help = snapshot(&r.0, &["--help"], None, None);
    assert_eq!(help.code(), 0);
    assert!(help.stdout().contains("--daily"));
    assert_eq!(git_out(&r.0, &["tag", "-l"]), "");
}

#[test]
fn separate_hyphen_name_arg_reaches_validation_and_exits_2() {
    let r = Scratch::repo("hyphen");
    let run = snapshot(&r.0, &["--name", "-x"], None, None);
    assert_eq!(run.code(), 2, "{}", run.stderr());
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains("invalid tag name"), "{}", run.stderr());
    assert_eq!(git_out(&r.0, &["tag", "-l"]), "");
}

#[test]
fn empty_name_falls_back_to_dated_name() {
    let r = Scratch::repo("emptyname");
    let run = snapshot(&r.0, &["--name", ""], None, None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    let name = run.get("tag");
    assert!(Regex::new(r"^v\d{4}\.\d{2}\.\d{2}-\d{4}$").unwrap().is_match(&name), "{name}");
}

#[test]
fn daily_name_collision_exits_3_and_leaves_the_tag() {
    let r = Scratch::repo("dailycollide");
    let today = String::from_utf8(Command::new("date").arg("+v%Y.%m.%d").output().unwrap().stdout)
        .unwrap()
        .trim()
        .to_string();
    git(&r.0, &["tag", "-a", &today, "-m", "old"]);
    let before = git_out(&r.0, &["rev-parse", &today]);
    write(&r.0, "b.txt", "b\n");
    git(&r.0, &["add", "b.txt"]);
    commit(&r.0, "second");

    let run = snapshot(&r.0, &["--daily"], None, None);
    assert_eq!(run.code(), 3, "{}", run.stderr());
    assert_eq!(run.stdout(), "");
    assert!(run.stderr().contains(&format!(
        "tag '{today}' already exists. Use --name <other>, or drop --daily for minute granularity."
    )));
    assert_eq!(git_out(&r.0, &["rev-parse", &today]), before);
}

#[test]
fn at_sign_tag_name_pushes_the_tag_not_the_branch() {
    let (r, bare) = Scratch::repo_with_bare("atsign");
    let run = snapshot(&r.0, &["--name", "@", "--push"], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("pushed"), "yes");
    assert_eq!(git_out(&bare.0, &["for-each-ref", "--format=%(refname)"]), "refs/tags/@");
}

#[test]
fn tag_sharing_a_branch_name_still_pushes_the_tag() {
    let (r, bare) = Scratch::repo_with_bare("samename");
    git(&r.0, &["branch", "snap1"]);
    let run = snapshot(&r.0, &["--name", "snap1", "--push"], Some("github"), None);
    assert_eq!(run.code(), 0, "{}", run.stderr());
    assert_eq!(run.get("pushed"), "yes");
    assert_eq!(git_out(&bare.0, &["cat-file", "-t", "refs/tags/snap1"]), "tag");
    assert_eq!(git_out(&bare.0, &["for-each-ref", "--format=%(refname)"]), "refs/tags/snap1");
}
