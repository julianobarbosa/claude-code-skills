//! Integration tests: drive the real binary in scratch git repos.

use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};

static COUNTER: AtomicUsize = AtomicUsize::new(0);

/// Scratch directory under the system temp dir, removed on drop.
struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-detect-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }

    /// A git repo on `branch` with one empty commit and `origin` set to `url`.
    fn repo(tag: &str, url: &str, branch: &str) -> Self {
        let s = Self::new(tag);
        git(&s.0, &["init", "-q", "-b", branch]);
        git(&s.0, &["remote", "add", "origin", url]);
        git(
            &s.0,
            &[
                "-c", "user.name=t", "-c", "user.email=t@example.com",
                "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                "commit", "-q", "--allow-empty", "-m", "init",
            ],
        );
        s
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

fn ship(dir: &Path) -> Command {
    let mut c = Command::new(env!("CARGO_BIN_EXE_ship"));
    c.current_dir(dir)
        .env_remove("SHIP_PLATFORM");
    isolate(&mut c);
    c
}

fn run(mut c: Command) -> Output {
    c.output().unwrap()
}

fn stdout(o: &Output) -> String {
    String::from_utf8(o.stdout.clone()).unwrap()
}

const AZURE: &str = "https://dev.azure.com/myorg/my%20proj/_git/myrepo";

#[test]
fn azure_https_with_work_item_prints_all_lines_in_order() {
    let r = Scratch::repo("az", AZURE, "feature/837-foo");
    let o = run({
        let mut c = ship(&r.0);
        c.arg("detect");
        c
    });
    assert!(o.status.success());
    assert_eq!(
        stdout(&o),
        "platform=azure\n\
         remote=origin\n\
         url=https://dev.azure.com/myorg/my%20proj/_git/myrepo\n\
         branch=feature/837-foo\n\
         org_url=https://dev.azure.com/myorg\n\
         project=my proj\n\
         repo=myrepo\n\
         work_item=837\n"
    );
}

#[test]
fn ship_platform_github_drops_azure_keys() {
    let r = Scratch::repo("override", AZURE, "feature/837-foo");
    let o = run({
        let mut c = ship(&r.0);
        c.arg("detect").env("SHIP_PLATFORM", "github");
        c
    });
    assert!(o.status.success());
    assert_eq!(
        stdout(&o),
        "platform=github\n\
         remote=origin\n\
         url=https://dev.azure.com/myorg/my%20proj/_git/myrepo\n\
         branch=feature/837-foo\n\
         work_item=837\n"
    );
}

#[test]
fn github_on_main_has_four_lines_and_no_work_item() {
    let r = Scratch::repo("gh", "https://github.com/julianobarbosa/claude-code-skills.git", "main");
    let o = run({
        let mut c = ship(&r.0);
        c.arg("detect");
        c
    });
    assert!(o.status.success());
    assert_eq!(
        stdout(&o),
        "platform=github\n\
         remote=origin\n\
         url=https://github.com/julianobarbosa/claude-code-skills.git\n\
         branch=main\n"
    );
}

#[test]
fn missing_remote_is_unknown_with_empty_url_and_exit_zero() {
    let r = Scratch::repo("nope", "https://github.com/a/b.git", "main");
    let o = run({
        let mut c = ship(&r.0);
        c.args(["detect", "nope"]);
        c
    });
    assert!(o.status.success());
    assert_eq!(stdout(&o), "platform=unknown\nremote=nope\nurl=\nbranch=main\n");
}

#[test]
fn outside_a_repo_prints_three_lines_then_fails() {
    let d = Scratch::new("norepo");
    let o = run({
        let mut c = ship(&d.0);
        c.arg("detect").env("GIT_CEILING_DIRECTORIES", std::env::temp_dir());
        c
    });
    assert!(!o.status.success());
    assert_eq!(stdout(&o), "platform=unknown\nremote=origin\nurl=\n");
    assert!(String::from_utf8_lossy(&o.stderr).contains("ship:"));
}

#[test]
fn closed_stdout_pipe_is_a_quiet_success() {
    let r = Scratch::repo("pipe", AZURE, "feature/837-foo");
    let mut c = ship(&r.0);
    c.arg("detect").stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = c.spawn().unwrap();
    // Close the read end before the child gets as far as printing.
    drop(child.stdout.take());
    let o = child.wait_with_output().unwrap();
    assert_eq!(o.status.code(), Some(0), "stderr: {}", String::from_utf8_lossy(&o.stderr));
    assert!(o.stderr.is_empty(), "stderr: {}", String::from_utf8_lossy(&o.stderr));
}

#[test]
fn help_exits_zero() {
    let d = Scratch::new("help");
    for args in [&["--help"][..], &["detect", "--help"][..]] {
        let o = run({
            let mut c = ship(&d.0);
            c.args(args);
            c
        });
        assert_eq!(o.status.code(), Some(0), "{args:?}");
        assert!(stdout(&o).contains("Usage:"), "{args:?}");
    }
}
