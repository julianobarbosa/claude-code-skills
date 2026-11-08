//! Integration tests: drive the real binary in scratch git repos (no bun needed).

use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};

static COUNTER: AtomicUsize = AtomicUsize::new(0);

/// Scratch directory under the system temp dir, removed on drop.
struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-preflight-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }

    /// A git repo on `main` with one commit (`init.txt`) and no upstream.
    fn repo(tag: &str) -> Self {
        let s = Self::new(tag);
        git(&s.0, &["init", "-q", "-b", "main"]);
        write(&s.0, "init.txt", "init\n");
        git(&s.0, &["add", "init.txt"]);
        commit(&s.0, "init");
        s
    }

    /// Like [`Scratch::repo`], plus a bare remote with `main` pushed and set as upstream.
    fn repo_with_upstream(tag: &str) -> (Self, Self) {
        let r = Self::repo(tag);
        let bare = Self::new(&format!("{tag}-bare"));
        git(&bare.0, &["init", "-q", "--bare", "-b", "main"]);
        git(&r.0, &["remote", "add", "origin", bare.0.to_str().unwrap()]);
        git(&r.0, &["push", "-q", "-u", "origin", "main"]);
        (r, bare)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

/// Isolate a command from the developer's git config and exported git env.
fn isolate(c: &mut Command) -> &mut Command {
    c.env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env_remove("GIT_DIR")
        .env_remove("GIT_WORK_TREE")
        .env_remove("GIT_INDEX_FILE")
}

fn git(dir: &Path, args: &[&str]) {
    let st = isolate(Command::new("git").current_dir(dir).args(args)).status().unwrap();
    assert!(st.success(), "git {args:?} failed");
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

fn preflight(dir: &Path, extra: &[&str]) -> Output {
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    isolate(c.current_dir(dir))
        .arg("preflight")
        .args(extra)
        .output()
        .unwrap()
}

fn stdout(o: &Output) -> String {
    String::from_utf8(o.stdout.clone()).unwrap()
}

fn stderr(o: &Output) -> String {
    String::from_utf8_lossy(&o.stderr).into_owned()
}

#[test]
fn clean_and_pushed_prints_zeros_and_no_warnings() {
    let (r, _bare) = Scratch::repo_with_upstream("clean");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert_eq!(
        stdout(&o),
        "branch=main\n\
         commits_ahead_of_upstream=0\n\
         staged=0\n\
         unstaged=0\n\
         untracked=0\n\
         scope_clean=true\n"
    );
    assert_eq!(stderr(&o), "");
}

#[test]
fn two_local_commits_after_upstream_count_as_ahead() {
    let (r, _bare) = Scratch::repo_with_upstream("ahead");
    for n in ["a", "b"] {
        write(&r.0, &format!("{n}.txt"), n);
        git(&r.0, &["add", "."]);
        commit(&r.0, n);
    }
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("commits_ahead_of_upstream=2\n"), "{}", stdout(&o));
    assert!(stdout(&o).ends_with("scope_clean=true\n"));
}

#[test]
fn no_upstream_reports_zero_ahead_and_exits_zero() {
    let r = Scratch::repo("noup");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert_eq!(
        stdout(&o),
        "branch=main\n\
         commits_ahead_of_upstream=0\n\
         staged=0\n\
         unstaged=0\n\
         untracked=0\n\
         scope_clean=true\n"
    );
}

#[test]
fn staged_only_is_clean() {
    let (r, _bare) = Scratch::repo_with_upstream("staged");
    write(&r.0, "a.txt", "a");
    write(&r.0, "b.txt", "b");
    git(&r.0, &["add", "a.txt", "b.txt"]);
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert_eq!(
        stdout(&o),
        "branch=main\n\
         commits_ahead_of_upstream=0\n\
         staged=2\n\
         unstaged=0\n\
         untracked=0\n\
         scope_clean=true\n"
    );
    assert_eq!(stderr(&o), "");
}

#[test]
fn mixed_tree_counts_each_and_warns_on_stderr() {
    let (r, _bare) = Scratch::repo_with_upstream("mixed");
    write(&r.0, "staged.txt", "s");
    git(&r.0, &["add", "staged.txt"]);
    write(&r.0, "init.txt", "changed\n"); // tracked, modified, not staged
    write(&r.0, "new.txt", "n");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert_eq!(
        stdout(&o),
        "branch=main\n\
         commits_ahead_of_upstream=0\n\
         staged=1\n\
         unstaged=1\n\
         untracked=1\n\
         scope_clean=false\n"
    );
    assert_eq!(
        stderr(&o),
        ">> WARNING: 1 file(s) changed but not staged: init.txt\n\
         >> WARNING: 1 untracked file(s): new.txt\n\
         >> Confirm these don't belong in this PR before committing (the PR #192 guard).\n"
    );
}

#[test]
fn rename_counts_once_as_staged() {
    let r = Scratch::repo("rename");
    git(&r.0, &["mv", "init.txt", "moved.txt"]);
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("staged=1\nunstaged=0\n"), "{}", stdout(&o));
    assert!(stdout(&o).ends_with("scope_clean=true\n"));
}

#[test]
fn modified_in_both_columns_counts_as_staged_and_unstaged() {
    let r = Scratch::repo("both");
    write(&r.0, "init.txt", "one\n");
    git(&r.0, &["add", "init.txt"]);
    write(&r.0, "init.txt", "two\n");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("staged=1\nunstaged=1\nuntracked=0\nscope_clean=false\n"), "{}", stdout(&o));
}

#[test]
fn ignored_files_are_not_counted() {
    let r = Scratch::repo("ignored");
    std::fs::create_dir_all(r.0.join(".git/info")).unwrap();
    write(&r.0, ".git/info/exclude", "junk.log\n");
    write(&r.0, "junk.log", "x");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert!(stdout(&o).contains("untracked=0\nscope_clean=true\n"), "{}", stdout(&o));
}

// The fixed TS bug: a lone unstaged change is the first (leading-space) porcelain
// line. TS trims it into `M b.txt` and reports staged=1 scope_clean=true.
#[test]
fn lone_unstaged_first_line_is_unstaged_not_staged() {
    let (r, _bare) = Scratch::repo_with_upstream("lead");
    write(&r.0, "b.txt", "v1\n");
    git(&r.0, &["add", "b.txt"]);
    commit(&r.0, "b");
    git(&r.0, &["push", "-q"]);
    write(&r.0, "b.txt", "v2\n");
    let o = preflight(&r.0, &[]);
    assert_eq!(o.status.code(), Some(0));
    assert_eq!(
        stdout(&o),
        "branch=main\n\
         commits_ahead_of_upstream=0\n\
         staged=0\n\
         unstaged=1\n\
         untracked=0\n\
         scope_clean=false\n"
    );
    assert_eq!(
        stderr(&o),
        ">> WARNING: 1 file(s) changed but not staged: b.txt\n\
         >> Confirm these don't belong in this PR before committing (the PR #192 guard).\n"
    );
}

#[test]
fn remote_argument_is_accepted_and_ignored() {
    let r = Scratch::repo("remote");
    let with = preflight(&r.0, &["whatever"]);
    let without = preflight(&r.0, &[]);
    assert_eq!(with.status.code(), Some(0));
    assert_eq!(stdout(&with), stdout(&without));
}

#[test]
fn outside_a_repo_prints_nothing_on_stdout_and_fails() {
    let d = Scratch::new("norepo");
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    let o = isolate(c.current_dir(&d.0))
        .env("GIT_CEILING_DIRECTORIES", std::env::temp_dir())
        .arg("preflight")
        .output()
        .unwrap();
    assert!(!o.status.success());
    assert_eq!(stdout(&o), "");
    assert!(stderr(&o).contains("ship:"));
}

#[test]
fn help_exits_zero() {
    let d = Scratch::new("help");
    for flag in ["--help", "-h"] {
        let o = preflight(&d.0, &[flag]);
        assert_eq!(o.status.code(), Some(0), "{flag}");
        assert!(stdout(&o).contains("Usage:"), "{flag}");
    }
}

#[test]
fn closed_stdout_pipe_is_a_quiet_success_and_keeps_the_scope_guard() {
    let (r, _bare) = Scratch::repo_with_upstream("pipe");
    write(&r.0, "new.txt", "n");
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    isolate(c.current_dir(&r.0))
        .arg("preflight")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = c.spawn().unwrap();
    // Close the read end before the child gets as far as printing.
    drop(child.stdout.take());
    let o = child.wait_with_output().unwrap();
    let err = stderr(&o);
    assert_eq!(o.status.code(), Some(0), "stderr: {err}");
    assert!(!err.contains("ship:"), "stderr: {err}");
    assert!(err.contains(">> WARNING: 1 untracked file(s)"), "stderr: {err}");
}
