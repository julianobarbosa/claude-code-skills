//! Integration tests for `ship open` (Story 4.1): real binary, scratch HOME with a
//! fixture `Local State`, no browser, no network.

use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicUsize, Ordering};

static COUNTER: AtomicUsize = AtomicUsize::new(0);

const LOCAL_STATE: &str = r#"{"profile":{"info_cache":{
  "Default":{"name":"Person 1"},
  "Profile 2":{"user_name":"b@x.com","name":"Work"},
  "Profile 10":{"user_name":"c@x.com","name":"Other"}}}}"#;

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!("ship-open-{}-{n}-{tag}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        Scratch(dir)
    }

    fn xdg(&self) -> PathBuf {
        self.0.join("xdg")
    }

    fn config(&self) -> PathBuf {
        self.xdg().join("ship/open.json")
    }

    fn chrome_state(&self) -> PathBuf {
        self.0.join(".config/google-chrome/Local State")
    }

    fn edge_state(&self) -> PathBuf {
        self.0.join(".config/microsoft-edge/Local State")
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn put(path: &Path, text: &str) {
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(path, text).unwrap();
}

fn open_with_env(
    s: &Scratch,
    os: &str,
    path: Option<&str>,
    launch_log: Option<&Path>,
    mnt_c: Option<&Path>,
    args: &[&str],
) -> Output {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_ship"));
    cmd.arg("open")
        .args(args)
        .env("HOME", &s.0)
        .env("XDG_CONFIG_HOME", s.xdg())
        .env("SHIP_OPEN_OS", os)
        .env_remove("WSL_DISTRO_NAME");
    if let Some(p) = path {
        cmd.env("PATH", p);
    }
    if let Some(log) = launch_log {
        cmd.env("SHIP_OPEN_LAUNCH_LOG", log);
    }
    if let Some(m) = mnt_c {
        cmd.env("SHIP_OPEN_MNT_C", m);
    }
    cmd.output().unwrap()
}

fn open(s: &Scratch, os: &str, args: &[&str]) -> Output {
    open_with_env(s, os, None, None, None, args)
}

fn out(o: &Output) -> String {
    String::from_utf8_lossy(&o.stdout).into_owned()
}

fn err(o: &Output) -> String {
    String::from_utf8_lossy(&o.stderr).into_owned()
}

fn code(o: &Output) -> i32 {
    o.status.code().unwrap()
}

fn with_chrome() -> Scratch {
    let s = Scratch::new("chrome");
    put(&s.chrome_state(), LOCAL_STATE);
    s
}

#[test]
fn list_profiles_in_file_order() {
    let s = with_chrome();
    let o = open(&s, "linux", &["--list-profiles"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    let ls = s.chrome_state();
    assert_eq!(
        out(&o),
        format!(
            "browser=chrome\nlocal_state={}\nprofile=Default\t(no account)\tPerson 1\n\
             profile=Profile 2\tb@x.com\tWork\nprofile=Profile 10\tc@x.com\tOther\n",
            ls.display()
        )
    );
    assert_eq!(
        err(&o),
        format!(">> chrome profiles from {}\n", ls.display())
    );
}

#[test]
fn list_profiles_on_macos_uses_library_path() {
    let s = Scratch::new("mac");
    put(
        &s.0.join("Library/Application Support/Google/Chrome/Local State"),
        LOCAL_STATE,
    );
    let o = open(&s, "macos", &["--list-profiles"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).contains("Library/Application Support/Google/Chrome/Local State"));
}

#[test]
fn dry_run_hit_is_case_insensitive() {
    let s = with_chrome();
    let o = open(
        &s,
        "linux",
        &["https://x/pr/1", "--profile", "B@X.com", "--dry-run"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(
        out(&o),
        "opened_url=https://x/pr/1\nbrowser=chrome\nprofile_dir=Profile 2\nprofile_email=b@x.com\n"
    );
    assert_eq!(
        err(&o),
        ">> dry run — would open chrome profile \"Profile 2\" (b@x.com)\n"
    );
}

#[test]
fn unknown_email_falls_back_to_default() {
    let s = with_chrome();
    let o = open(&s, "linux", &["u", "--profile", "nope@x", "--dry-run"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).contains("profile_dir=Default\nprofile_email=\n"));
    assert!(err(&o).starts_with(
        ">> no chrome profile signed in as nope@x; falling back to the Default profile\n"
    ));
}

#[test]
fn stored_default_is_used_and_announced() {
    let s = with_chrome();
    put(&s.config(), r#"{"defaultProfileEmail":"b@x.com"}"#);
    let o = open(&s, "linux", &["u", "--dry-run"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).contains("profile_dir=Profile 2\n"));
    assert!(err(&o).starts_with(">> using stored default profile b@x.com\n"));
}

#[test]
fn profile_flag_beats_stored_default_without_note() {
    let s = with_chrome();
    put(&s.config(), r#"{"defaultProfileEmail":"b@x.com"}"#);
    let o = open(&s, "linux", &["u", "--profile", "c@x.com", "--dry-run"]);
    assert!(out(&o).contains("profile_dir=Profile 10\n"));
    assert!(!err(&o).contains("stored default"));
}

#[test]
fn last_profile_flag_wins() {
    let s = with_chrome();
    let o = open(
        &s,
        "linux",
        &[
            "u",
            "--profile",
            "b@x.com",
            "--profile",
            "c@x.com",
            "--dry-run",
        ],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).contains("profile_dir=Profile 10\n"));
}

#[test]
fn set_default_fresh_file_matches_ts_bytes() {
    let s = Scratch::new("set");
    let o = open(&s, "linux", &["--set-default", "a@x", "--browser", "edge"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(out(&o), "default_profile_email=a@x\nbrowser=edge\n");
    assert_eq!(
        err(&o),
        format!(
            ">> saved default profile a@x (edge) to {}\n",
            s.config().display()
        )
    );
    assert_eq!(
        std::fs::read_to_string(s.config()).unwrap(),
        "{\n  \"defaultProfileEmail\": \"a@x\",\n  \"browser\": \"edge\"\n}\n"
    );
}

#[test]
fn set_default_keeps_existing_keys_and_order() {
    let s = Scratch::new("keep");
    put(&s.config(), r#"{"browser":"chrome","x":1}"#);
    let o = open(&s, "linux", &["--set-default", "a@x"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(out(&o), "default_profile_email=a@x\nbrowser=chrome\n");
    assert_eq!(
        std::fs::read_to_string(s.config()).unwrap(),
        "{\n  \"browser\": \"chrome\",\n  \"x\": 1,\n  \"defaultProfileEmail\": \"a@x\"\n}\n"
    );
}

#[test]
fn set_default_runs_before_browser_detection_and_rejects_empty() {
    let s = Scratch::new("nobrowser");
    let o = open(&s, "linux", &["--set-default", "a@x"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(out(&o), "default_profile_email=a@x\n");
    let o = open(&s, "linux", &["--set-default", ""]);
    assert_eq!(code(&o), 2);
    assert_eq!(err(&o), "--set-default needs an email\n");
}

#[test]
fn unparseable_config_reads_as_empty() {
    let s = with_chrome();
    put(&s.config(), "{ nope");
    let o = open(&s, "linux", &["u", "--dry-run"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    let o = open(&s, "linux", &["--set-default", "a@x"]);
    assert_eq!(code(&o), 0);
    assert_eq!(
        std::fs::read_to_string(s.config()).unwrap(),
        "{\n  \"defaultProfileEmail\": \"a@x\"\n}\n"
    );
}

#[test]
fn stored_browser_is_used_when_its_state_exists() {
    let s = with_chrome();
    put(
        &s.edge_state(),
        r#"{"profile":{"info_cache":{"Default":{"user_name":"e@x.com"}}}}"#,
    );
    // Both installed: chrome wins by default.
    assert!(out(&open(&s, "linux", &["u", "--dry-run"])).contains("browser=chrome\n"));
    put(&s.config(), r#"{"browser":"edge"}"#);
    let o = open(&s, "linux", &["u", "--dry-run"]);
    assert!(out(&o).contains("browser=edge\n"), "{}", err(&o));
}

#[test]
fn no_browser_installed_exits_2() {
    let s = Scratch::new("none");
    let o = open(&s, "linux", &["u", "--dry-run"]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        "no supported browser (edge/chrome) found — pass --browser or install one\n"
    );
    assert_eq!(out(&o), "");
}

#[test]
fn explicit_browser_without_state_exits_2() {
    let s = with_chrome();
    let o = open(&s, "linux", &["u", "--browser", "edge", "--dry-run"]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        format!(
            "no edge profile data found (looked for {}). Is edge installed?\n",
            s.edge_state().display()
        )
    );
}

#[test]
fn unparseable_local_state_exits_2() {
    let s = Scratch::new("badstate");
    put(&s.chrome_state(), "not json");
    let o = open(&s, "linux", &["--list-profiles"]);
    assert_eq!(code(&o), 2);
    assert!(err(&o).starts_with(&format!(
        "could not parse chrome Local State ({}): ",
        s.chrome_state().display()
    )));
}

#[test]
fn no_profiles_exits_2() {
    let s = Scratch::new("noprofiles");
    put(&s.chrome_state(), "{}");
    let o = open(&s, "linux", &["u", "--dry-run"]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        format!(
            "no chrome profiles found in {}\n",
            s.chrome_state().display()
        )
    );
}

#[test]
fn bad_browser_value_exits_2() {
    let s = with_chrome();
    let o = open(&s, "linux", &["u", "--browser", "firefox"]);
    assert_eq!(code(&o), 2);
    assert_eq!(err(&o), "--browser must be edge or chrome (got firefox)\n");
}

#[test]
fn missing_url_exits_2() {
    let s = with_chrome();
    let o = open(&s, "linux", &[]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        "need a <url> to open (or use --list-profiles / --set-default)\n"
    );
}

#[test]
fn empty_url_string_exits_2() {
    let s = with_chrome();
    let o = open(&s, "linux", &[""]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        "need a <url> to open (or use --list-profiles / --set-default)\n"
    );
    assert_eq!(out(&o), "");
}

#[test]
fn unknown_flag_and_second_positional_exit_2() {
    let s = with_chrome();
    assert_eq!(code(&open(&s, "linux", &["u", "--bogus"])), 2);
    assert_eq!(code(&open(&s, "linux", &["u", "v", "--dry-run"])), 2);
}

#[test]
fn url_with_ampersand_is_intact() {
    let s = with_chrome();
    let o = open(&s, "linux", &["https://x/?a=1&b=2", "--dry-run"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).starts_with("opened_url=https://x/?a=1&b=2\n"));
}

#[test]
fn wsl_launch_runs_powershell_with_quotes() {
    let s = Scratch::new("wsl-launch");
    let bin = s.0.join("bin");
    std::fs::create_dir_all(&bin).unwrap();
    let stub = bin.join("cmd.exe");
    put(&stub, "#!/bin/sh\n[ \"$1\" = \"/c\" ] && echo testuser\n");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&stub, std::fs::Permissions::from_mode(0o755)).unwrap();
    }
    let ls =
        s.0.join("mnt/c/Users/testuser/AppData/Local/Google/Chrome/User Data/Local State");
    put(
        &ls,
        r#"{"profile":{"info_cache":{"Default":{"name":"Default","user_name":""},"Profile 2":{"name":"Work","user_name":"b@x.com"}}}}"#,
    );

    let log = s.0.join("launch.log");
    let mnt = s.0.join("mnt/c");
    let o = open_with_env(
        &s,
        "wsl",
        Some(bin.to_str().unwrap()),
        Some(&log),
        Some(&mnt),
        &["https://example.com/?a=1&b=2'test", "--profile", "b@x.com"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(
        err(&o),
        ">> opening in chrome profile \"Profile 2\" (b@x.com)\n"
    );
    assert_eq!(
        out(&o),
        "opened_url=https://example.com/?a=1&b=2'test\nbrowser=chrome\nprofile_dir=Profile 2\nprofile_email=b@x.com\n"
    );

    let logged = std::fs::read_to_string(&log).unwrap();
    let lines: Vec<&str> = logged.lines().collect();
    assert_eq!(lines[0], "powershell.exe");
    assert_eq!(lines[1], "-NoProfile");
    assert_eq!(lines[2], "-Command");
    assert_eq!(
        lines[3],
        "Start-Process chrome.exe -ArgumentList '--profile-directory=\"Profile 2\"','https://example.com/?a=1&b=2''test'"
    );
}

#[test]
fn macos_launch_runs_open_with_args() {
    let s = Scratch::new("macos-launch");
    let ls =
        s.0.join("Library/Application Support/Microsoft Edge/Local State");
    put(
        &ls,
        r#"{"profile":{"info_cache":{"Default":{"name":"Personal","user_name":"me@edge.com"}}}}"#,
    );

    let log = s.0.join("launch.log");
    let o = open_with_env(
        &s,
        "macos",
        None,
        Some(&log),
        None,
        &["https://example.com/pr/123", "--browser", "edge"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(
        err(&o),
        ">> opening in edge profile \"Default\" (me@edge.com)\n"
    );
    assert_eq!(
        out(&o),
        "opened_url=https://example.com/pr/123\nbrowser=edge\nprofile_dir=Default\nprofile_email=me@edge.com\n"
    );

    let logged = std::fs::read_to_string(&log).unwrap();
    let lines: Vec<&str> = logged.lines().collect();
    assert_eq!(lines[0], "open");
    assert_eq!(lines[1], "-na");
    assert_eq!(lines[2], "Microsoft Edge");
    assert_eq!(lines[3], "--args");
    assert_eq!(lines[4], "--profile-directory=Default");
    assert_eq!(lines[5], "https://example.com/pr/123");
}

#[test]
fn linux_launch_spawns_candidate_from_path() {
    let s = with_chrome();
    let bin_dir = s.0.join("bin");
    std::fs::create_dir_all(&bin_dir).unwrap();
    let stub = bin_dir.join("google-chrome");
    put(&stub, "#!/bin/sh\nexit 0\n");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&stub, std::fs::Permissions::from_mode(0o755)).unwrap();
    }

    let log = s.0.join("launch.log");
    let o = open_with_env(
        &s,
        "linux",
        Some(bin_dir.to_str().unwrap()),
        Some(&log),
        None,
        &["https://example.com/pr/456", "--profile", "b@x.com"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(
        err(&o),
        ">> opening in chrome profile \"Profile 2\" (b@x.com)\n"
    );
    assert_eq!(
        out(&o),
        "opened_url=https://example.com/pr/456\nbrowser=chrome\nprofile_dir=Profile 2\nprofile_email=b@x.com\n"
    );

    let logged = std::fs::read_to_string(&log).unwrap();
    let lines: Vec<&str> = logged.lines().collect();
    assert_eq!(lines[0], stub.to_str().unwrap());
    assert_eq!(lines[1], "--profile-directory=Profile 2");
    assert_eq!(lines[2], "https://example.com/pr/456");
}

#[test]
fn linux_launch_fails_when_no_binary_on_path() {
    let s = with_chrome();
    let empty_dir = s.0.join("empty");
    std::fs::create_dir_all(&empty_dir).unwrap();
    let o = open_with_env(
        &s,
        "linux",
        Some(empty_dir.to_str().unwrap()),
        None,
        None,
        &["https://example.com/pr/1", "--browser", "chrome"],
    );
    assert_eq!(code(&o), 2);
    assert!(err(&o).contains(
        "no chrome binary found on PATH (tried google-chrome, google-chrome-stable, chromium)"
    ));
    assert_eq!(out(&o), "");
}

#[test]
fn linux_launch_live_spawns_without_launch_log() {
    let s = with_chrome();
    let bin_dir = s.0.join("bin");
    std::fs::create_dir_all(&bin_dir).unwrap();
    let stub = bin_dir.join("google-chrome");
    put(&stub, "#!/bin/sh\nexit 0\n");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&stub, std::fs::Permissions::from_mode(0o755)).unwrap();
    }
    let o = open_with_env(
        &s,
        "linux",
        Some(bin_dir.to_str().unwrap()),
        None,
        None,
        &["https://example.com/pr/live", "--profile", "b@x.com"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(err(&o).contains(">> opening in chrome profile \"Profile 2\" (b@x.com)"));
    assert!(out(&o).contains("opened_url=https://example.com/pr/live"));
}

#[test]
fn launch_failure_exits_2_with_error_message() {
    let s = with_chrome();
    let bin_dir = s.0.join("bin");
    std::fs::create_dir_all(&bin_dir).unwrap();
    let stub = bin_dir.join("google-chrome");
    put(&stub, "#!/bin/sh\nexit 0\n");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&stub, std::fs::Permissions::from_mode(0o755)).unwrap();
    }
    let bad_log = s.0.join("nonexistent/dir/launch.log");
    let o = open_with_env(
        &s,
        "linux",
        Some(bin_dir.to_str().unwrap()),
        Some(&bad_log),
        None,
        &["https://example.com/pr/bad", "--profile", "b@x.com"],
    );
    assert_eq!(code(&o), 2, "stderr: {}", err(&o));
    assert!(
        err(&o).contains("failed to launch"),
        "stderr was: {}",
        err(&o)
    );
}

fn open_with_path(s: &Scratch, os: &str, path: &str, args: &[&str]) -> Output {
    open_with_env(s, os, Some(path), None, None, args)
}

#[test]
fn wsl_without_cmd_exe_exits_2() {
    let s = Scratch::new("wsl-nocmd");
    let empty = s.0.join("emptybin");
    std::fs::create_dir_all(&empty).unwrap();
    let o = open_with_path(
        &s,
        "wsl",
        empty.to_str().unwrap(),
        &["u", "--browser", "chrome", "--dry-run"],
    );
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        "could not determine the Windows username (cmd.exe unavailable?)\n"
    );
    assert_eq!(out(&o), "");
}

#[test]
fn wsl_username_reaches_the_mnt_c_path() {
    use std::os::unix::fs::PermissionsExt;
    let s = Scratch::new("wsl-stub");
    let bin = s.0.join("stubbin");
    std::fs::create_dir_all(&bin).unwrap();
    let cmd = bin.join("cmd.exe");
    std::fs::write(&cmd, "#!/bin/sh\necho stubuser\n").unwrap();
    std::fs::set_permissions(&cmd, std::fs::Permissions::from_mode(0o755)).unwrap();
    let path = format!("{}:/usr/bin:/bin", bin.display());
    let o = open_with_path(&s, "wsl", &path, &["u", "--browser", "chrome", "--dry-run"]);
    assert_eq!(code(&o), 2);
    assert_eq!(
        err(&o),
        "no chrome profile data found (looked for /mnt/c/Users/stubuser/AppData/Local/Google/Chrome/User Data/Local State). Is chrome installed?\n"
    );
}

#[test]
fn last_browser_and_last_set_default_win() {
    let s = with_chrome();
    put(
        &s.edge_state(),
        r#"{"profile":{"info_cache":{"Default":{"user_name":"e@x.com"}}}}"#,
    );
    let o = open(
        &s,
        "linux",
        &["u", "--browser", "edge", "--browser", "chrome", "--dry-run"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert!(out(&o).contains("browser=chrome\n"));
    let o = open(
        &s,
        "linux",
        &["--set-default", "a@x", "--set-default", "b@x"],
    );
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(out(&o), "default_profile_email=b@x\n");
}

#[test]
fn set_default_echoes_a_raw_stored_browser_string() {
    let s = Scratch::new("rawbrowser");
    put(&s.config(), r#"{"browser":"firefox"}"#);
    let o = open(&s, "linux", &["--set-default", "a@x"]);
    assert_eq!(code(&o), 0, "{}", err(&o));
    assert_eq!(out(&o), "default_profile_email=a@x\nbrowser=firefox\n");
    assert!(err(&o).contains("(firefox)"));
}
