//! `ship open`: open a URL in the browser profile signed in with a chosen email.
//! Supports `--list-profiles`, `--set-default`, `<url> --dry-run`, and launching
//! the chosen profile on WSL, macOS, and Linux.

use serde_json::{Map, Value};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Browser {
    Edge,
    Chrome,
}

impl Browser {
    pub fn as_str(self) -> &'static str {
        match self {
            Browser::Edge => "edge",
            Browser::Chrome => "chrome",
        }
    }

    pub fn parse(s: &str) -> Option<Browser> {
        match s {
            "edge" => Some(Browser::Edge),
            "chrome" => Some(Browser::Chrome),
            _ => None,
        }
    }

    pub fn win_exe(self) -> &'static str {
        match self {
            Browser::Edge => "msedge.exe",
            Browser::Chrome => "chrome.exe",
        }
    }

    pub fn mac_app(self) -> &'static str {
        match self {
            Browser::Edge => "Microsoft Edge",
            Browser::Chrome => "Google Chrome",
        }
    }

    pub fn linux_bins(self) -> &'static [&'static str] {
        match self {
            Browser::Edge => &["microsoft-edge", "microsoft-edge-stable"],
            Browser::Chrome => &["google-chrome", "google-chrome-stable", "chromium"],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Os {
    Macos,
    Wsl,
    Linux,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Profile {
    pub dir: String,
    pub email: String,
    pub name: String,
}

/// What `resolve` wants said on stderr (the caller owns the browser name).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Note {
    None,
    /// The wanted email matched no profile.
    Miss,
    /// The stored default matched (no `--profile` given).
    StoredDefault,
}

pub struct Args {
    pub url: Option<String>,
    pub profile: Option<String>,
    pub browser: Option<String>,
    pub list_profiles: bool,
    pub set_default: Option<String>,
    pub dry_run: bool,
}

/// `Local State` path for a browser on an OS. `win_user` matters only on WSL.
pub fn local_state_path(browser: Browser, os: Os, home: &str, win_user: &str) -> PathBuf {
    let mnt_c = std::env::var("SHIP_OPEN_MNT_C").unwrap_or_else(|_| "/mnt/c".to_string());
    let p = match (browser, os) {
        (Browser::Edge, Os::Wsl) => {
            format!("{mnt_c}/Users/{win_user}/AppData/Local/Microsoft/Edge/User Data/Local State")
        }
        (Browser::Edge, Os::Macos) => {
            format!("{home}/Library/Application Support/Microsoft Edge/Local State")
        }
        (Browser::Edge, Os::Linux) => format!("{home}/.config/microsoft-edge/Local State"),
        (Browser::Chrome, Os::Wsl) => {
            format!("{mnt_c}/Users/{win_user}/AppData/Local/Google/Chrome/User Data/Local State")
        }
        (Browser::Chrome, Os::Macos) => {
            format!("{home}/Library/Application Support/Google/Chrome/Local State")
        }
        (Browser::Chrome, Os::Linux) => format!("{home}/.config/google-chrome/Local State"),
    };
    PathBuf::from(p)
}

/// Read `profile.info_cache` in file key order. Entries: dir = key, email = `user_name`
/// (default ""), name = `name` (default the dir). A missing cache reads as empty.
pub fn parse_profiles(text: &str) -> Result<Vec<Profile>, serde_json::Error> {
    let root: Value = serde_json::from_str(text)?;
    let Some(cache) = root
        .pointer("/profile/info_cache")
        .and_then(Value::as_object)
    else {
        return Ok(Vec::new());
    };
    let field = |v: &Value, key: &str, default: &str| match v.get(key) {
        None | Some(Value::Null) => default.to_string(),
        Some(Value::String(s)) => s.clone(),
        Some(other) => other.to_string(),
    };
    Ok(cache
        .iter()
        .map(|(dir, v)| Profile {
            dir: dir.clone(),
            email: field(v, "user_name", ""),
            name: field(v, "name", dir),
        })
        .collect())
}

/// Explicit flag, else the stored browser if installed, else the first installed
/// (`installed` is in chrome, edge order), else the stored browser.
pub fn pick_browser(
    explicit: Option<Browser>,
    stored: Option<Browser>,
    installed: &[Browser],
) -> Result<Browser, String> {
    if let Some(b) = explicit {
        return Ok(b);
    }
    if let Some(s) = stored.filter(|s| installed.contains(s)) {
        return Ok(s);
    }
    if let Some(first) = installed.first() {
        return Ok(*first);
    }
    stored.ok_or_else(|| {
        "no supported browser (edge/chrome) found — pass --browser or install one".to_string()
    })
}

/// Match `wanted` (already trimmed, case-insensitive) against the profiles; on a miss or
/// empty `wanted`, fall back to `Default`, else the first profile. `None` = no profiles.
pub fn resolve<'a>(
    profiles: &'a [Profile],
    wanted: &str,
    from_flag: bool,
) -> (Option<&'a Profile>, Note) {
    let mut note = Note::None;
    if !wanted.is_empty() {
        let lw = wanted.to_lowercase();
        // An account signed in under a different alias (UPN vs primary SMTP) keeps that
        // alias as its email, so also accept a signed-in profile the user NAMED after it.
        let hit = profiles
            .iter()
            .find(|p| p.email.to_lowercase() == lw)
            .or_else(|| {
                profiles
                    .iter()
                    .find(|p| !p.email.is_empty() && p.name.trim().to_lowercase() == lw)
            });
        if let Some(p) = hit {
            if !from_flag {
                note = Note::StoredDefault;
            }
            return (Some(p), note);
        }
        note = Note::Miss;
    }
    let chosen = profiles
        .iter()
        .find(|p| p.dir == "Default")
        .or_else(|| profiles.first());
    (chosen, note)
}

/// Existing keys (and their order) kept; `defaultProfileEmail` overwritten, `browser` too
/// when given.
pub fn merge_config(
    existing: &Map<String, Value>,
    email: &str,
    browser: Option<Browser>,
) -> Map<String, Value> {
    let mut next = existing.clone();
    next.insert("defaultProfileEmail".into(), Value::String(email.into()));
    if let Some(b) = browser {
        next.insert("browser".into(), Value::String(b.as_str().into()));
    }
    next
}

/// Missing, unparseable or non-object file reads as empty.
fn read_config(path: &Path) -> Map<String, Value> {
    std::fs::read_to_string(path)
        .ok()
        .and_then(|t| serde_json::from_str::<Value>(&t).ok())
        .and_then(|v| match v {
            Value::Object(m) => Some(m),
            _ => None,
        })
        .unwrap_or_default()
}

fn stored_browser(cfg: &Map<String, Value>) -> Option<Browser> {
    cfg.get("browser")
        .and_then(Value::as_str)
        .and_then(Browser::parse)
}

fn stored_email(cfg: &Map<String, Value>) -> &str {
    cfg.get("defaultProfileEmail")
        .and_then(Value::as_str)
        .unwrap_or("")
}

fn config_path(home: &str) -> PathBuf {
    match std::env::var("XDG_CONFIG_HOME") {
        Ok(x) if !x.is_empty() => PathBuf::from(x).join("ship/open.json"),
        _ => PathBuf::from(home).join(".config/ship/open.json"),
    }
}

fn detect_os() -> Os {
    match std::env::var("SHIP_OPEN_OS").as_deref() {
        Ok("macos") => return Os::Macos,
        Ok("wsl") => return Os::Wsl,
        Ok("linux") => return Os::Linux,
        _ => {}
    }
    if cfg!(target_os = "macos") {
        return Os::Macos;
    }
    if std::env::var_os("WSL_DISTRO_NAME").is_some_and(|v| !v.is_empty()) {
        return Os::Wsl;
    }
    if std::fs::read_to_string("/proc/version")
        .is_ok_and(|v| v.to_lowercase().contains("microsoft"))
    {
        return Os::Wsl;
    }
    if Path::new("/mnt/c").exists() {
        Os::Wsl
    } else {
        Os::Linux
    }
}

/// Windows username on WSL. `cmd.exe` prints a harmless UNC note to stderr; stdout is the name.
fn win_user() -> String {
    Command::new("cmd.exe")
        .args(["/c", "echo %USERNAME%"])
        .stdin(Stdio::null())
        .stderr(Stdio::null())
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

/// Single-quote a string for PowerShell, doubling internal single quotes.
pub fn ps_quote(s: &str) -> String {
    format!("'{}'", s.replace('\'', "''"))
}

#[derive(Debug, PartialEq, Eq, Clone)]
pub struct LaunchPlan {
    pub program: String,
    pub args: Vec<String>,
}

/// Locate an executable from a candidate list along PATH.
pub fn find_binary_on_path(candidates: &[&str], path_var: Option<&str>) -> Option<PathBuf> {
    let path = path_var?;
    for bin in candidates {
        for dir in std::env::split_paths(path) {
            let candidate = dir.join(bin);
            if candidate.is_file() {
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    if candidate
                        .metadata()
                        .is_ok_and(|meta| meta.permissions().mode() & 0o111 != 0)
                    {
                        return Some(candidate);
                    }
                }
                #[cfg(not(unix))]
                return Some(candidate);
            }
        }
    }
    None
}

/// Pure plan builder for browser launch per OS.
pub fn launch_plan(
    os: Os,
    browser: Browser,
    profile_dir: &str,
    url: &str,
    path_var: Option<&str>,
) -> Result<LaunchPlan, String> {
    match os {
        Os::Wsl => {
            let arg1 = format!("--profile-directory=\"{}\"", profile_dir);
            let arg_list = format!("{},{}", ps_quote(&arg1), ps_quote(url));
            let command_str = format!(
                "Start-Process {} -ArgumentList {}",
                browser.win_exe(),
                arg_list
            );
            Ok(LaunchPlan {
                program: "powershell.exe".into(),
                args: vec!["-NoProfile".into(), "-Command".into(), command_str],
            })
        }
        Os::Macos => Ok(LaunchPlan {
            program: "open".into(),
            args: vec![
                "-na".into(),
                browser.mac_app().into(),
                "--args".into(),
                format!("--profile-directory={}", profile_dir),
                url.into(),
            ],
        }),
        Os::Linux => {
            let candidates = browser.linux_bins();
            let bin = find_binary_on_path(candidates, path_var).ok_or_else(|| {
                format!(
                    "no {} binary found on PATH (tried {})",
                    browser.as_str(),
                    candidates.join(", ")
                )
            })?;
            Ok(LaunchPlan {
                program: bin.to_string_lossy().into_owned(),
                args: vec![format!("--profile-directory={}", profile_dir), url.into()],
            })
        }
    }
}

fn launch(plan: &LaunchPlan, os: Os) -> io::Result<()> {
    if let Ok(log_path) = std::env::var("SHIP_OPEN_LAUNCH_LOG") {
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(log_path)?;
        writeln!(f, "{}", plan.program)?;
        for a in &plan.args {
            writeln!(f, "{}", a)?;
        }
        return Ok(());
    }

    let mut cmd = Command::new(&plan.program);
    cmd.args(&plan.args)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    match os {
        Os::Wsl | Os::Macos => {
            let status = cmd.status()?;
            if !status.success() {
                return Err(io::Error::other(format!(
                    "exited with status {}",
                    status.code().unwrap_or(1)
                )));
            }
            Ok(())
        }
        Os::Linux => {
            #[cfg(unix)]
            {
                use std::os::unix::process::CommandExt;
                cmd.process_group(0);
            }
            cmd.spawn().map(|_| ())
        }
    }
}

/// A failure that prints its bare message to stderr and exits 2, or a real I/O error.
enum Fail {
    Msg(String),
    Io(io::Error),
}

impl From<io::Error> for Fail {
    fn from(e: io::Error) -> Self {
        Fail::Io(e)
    }
}

fn fail<T>(msg: impl Into<String>) -> Result<T, Fail> {
    Err(Fail::Msg(msg.into()))
}

/// Exit code: 0 on success, 2 on every usage or resolution error (and, until Story 4.2,
/// on a non-dry-run).
pub fn run(args: &Args) -> io::Result<u8> {
    match run_inner(args) {
        Ok(code) => Ok(code),
        Err(Fail::Msg(m)) => {
            eprintln!("{m}");
            Ok(2)
        }
        Err(Fail::Io(e)) => Err(e),
    }
}

fn run_inner(args: &Args) -> Result<u8, Fail> {
    let explicit = match args.browser.as_deref() {
        None => None,
        Some(b) => match Browser::parse(b) {
            Some(b) => Some(b),
            None => return fail(format!("--browser must be edge or chrome (got {b})")),
        },
    };
    let home = std::env::var("HOME").unwrap_or_default();
    let os = detect_os();
    let cfg_path = config_path(&home);
    let cfg = read_config(&cfg_path);
    let out = io::stdout();
    let mut out = out.lock();

    if let Some(email) = args.set_default.as_deref() {
        if email.is_empty() {
            return fail("--set-default needs an email");
        }
        let next = merge_config(&cfg, email, explicit);
        if let Some(dir) = cfg_path.parent() {
            std::fs::create_dir_all(dir)?;
        }
        let body =
            serde_json::to_string_pretty(&Value::Object(next.clone())).map_err(io::Error::other)?;
        std::fs::write(&cfg_path, format!("{body}\n"))?;
        // Echo the raw stored string, as the TS does with `next.browser`.
        let saved = next
            .get("browser")
            .and_then(Value::as_str)
            .filter(|b| !b.is_empty());
        let suffix = saved.map(|b| format!(" ({b})")).unwrap_or_default();
        eprintln!(
            ">> saved default profile {email}{suffix} to {}",
            cfg_path.display()
        );
        writeln!(out, "default_profile_email={email}")?;
        if let Some(b) = saved {
            writeln!(out, "browser={b}")?;
        }
        return Ok(0);
    }

    let user = if os == Os::Wsl {
        let u = win_user();
        if u.is_empty() {
            return fail("could not determine the Windows username (cmd.exe unavailable?)");
        }
        u
    } else {
        String::new()
    };
    let state_path = |b: Browser| local_state_path(b, os, &home, &user);

    let installed: Vec<Browser> = [Browser::Chrome, Browser::Edge]
        .into_iter()
        .filter(|b| state_path(*b).exists())
        .collect();
    let browser = pick_browser(explicit, stored_browser(&cfg), &installed).map_err(Fail::Msg)?;
    let name = browser.as_str();
    let ls_path = state_path(browser);
    if !ls_path.exists() {
        return fail(format!(
            "no {name} profile data found (looked for {}). Is {name} installed?",
            ls_path.display()
        ));
    }
    let profiles = std::fs::read_to_string(&ls_path)
        .map_err(|e| e.to_string())
        .and_then(|t| parse_profiles(&t).map_err(|e| e.to_string()))
        .or_else(|e| {
            fail(format!(
                "could not parse {name} Local State ({}): {e}",
                ls_path.display()
            ))
        })?;

    if args.list_profiles {
        eprintln!(">> {name} profiles from {}", ls_path.display());
        writeln!(out, "browser={name}")?;
        writeln!(out, "local_state={}", ls_path.display())?;
        for p in &profiles {
            let email = if p.email.is_empty() {
                "(no account)"
            } else {
                &p.email
            };
            writeln!(out, "profile={}\t{email}\t{}", p.dir, p.name)?;
        }
        return Ok(0);
    }

    let Some(url) = args.url.as_deref().filter(|u| !u.is_empty()) else {
        return fail("need a <url> to open (or use --list-profiles / --set-default)");
    };

    let flag = args.profile.as_deref().unwrap_or("");
    let wanted = if flag.is_empty() {
        stored_email(&cfg)
    } else {
        flag
    }
    .trim();
    let (chosen, note) = resolve(&profiles, wanted, !flag.is_empty());
    if note != Note::Miss
        && let Some(c) = chosen
        && !wanted.is_empty()
        && c.email.to_lowercase() != wanted.to_lowercase()
    {
        eprintln!(
            ">> {name} profile \"{}\" matched by name (signed in as {})",
            c.name, c.email
        );
    }
    match note {
        Note::Miss => eprintln!(
            ">> no {name} profile signed in as {wanted}; falling back to the Default profile"
        ),
        Note::StoredDefault => eprintln!(">> using stored default profile {wanted}"),
        Note::None => {}
    }
    let Some(chosen) = chosen else {
        return fail(format!("no {name} profiles found in {}", ls_path.display()));
    };

    let who = if chosen.email.is_empty() {
        String::new()
    } else {
        format!(" ({})", chosen.email)
    };

    if args.dry_run {
        eprintln!(
            ">> dry run — would open {name} profile \"{}\"{who}",
            chosen.dir
        );
    } else {
        eprintln!(">> opening in {name} profile \"{}\"{who}", chosen.dir);
        let path_var = std::env::var("PATH").ok();
        let plan =
            launch_plan(os, browser, &chosen.dir, url, path_var.as_deref()).map_err(Fail::Msg)?;
        launch(&plan, os)
            .map_err(|e| Fail::Msg(format!("failed to launch {}: {e}", plan.program)))?;
    }

    writeln!(out, "opened_url={url}")?;
    writeln!(out, "browser={name}")?;
    writeln!(out, "profile_dir={}", chosen.dir)?;
    writeln!(out, "profile_email={}", chosen.email)?;
    writeln!(out, "profile_name={}", chosen.name)?;
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn p(dir: &str, email: &str) -> Profile {
        Profile {
            dir: dir.into(),
            email: email.into(),
            name: dir.into(),
        }
    }

    #[test]
    fn paths_per_os_and_browser() {
        let s = |b, o| {
            local_state_path(b, o, "/h", "bob")
                .to_string_lossy()
                .into_owned()
        };
        assert_eq!(
            s(Browser::Chrome, Os::Linux),
            "/h/.config/google-chrome/Local State"
        );
        assert_eq!(
            s(Browser::Edge, Os::Linux),
            "/h/.config/microsoft-edge/Local State"
        );
        assert_eq!(
            s(Browser::Chrome, Os::Macos),
            "/h/Library/Application Support/Google/Chrome/Local State"
        );
        assert_eq!(
            s(Browser::Edge, Os::Macos),
            "/h/Library/Application Support/Microsoft Edge/Local State"
        );
        assert_eq!(
            s(Browser::Chrome, Os::Wsl),
            "/mnt/c/Users/bob/AppData/Local/Google/Chrome/User Data/Local State"
        );
        assert_eq!(
            s(Browser::Edge, Os::Wsl),
            "/mnt/c/Users/bob/AppData/Local/Microsoft/Edge/User Data/Local State"
        );
    }

    #[test]
    fn profiles_keep_file_order_and_defaults() {
        let t = r#"{"profile":{"info_cache":{
            "Profile 10":{"user_name":"z@x.com","name":"Z"},
            "Default":{},
            "Profile 2":{"user_name":"b@x.com","name":"Work"}}}}"#;
        let ps = parse_profiles(t).unwrap();
        let dirs: Vec<_> = ps.iter().map(|p| p.dir.as_str()).collect();
        assert_eq!(dirs, ["Profile 10", "Default", "Profile 2"]);
        assert_eq!(
            ps[1],
            Profile {
                dir: "Default".into(),
                email: "".into(),
                name: "Default".into()
            }
        );
        assert_eq!(ps[2].email, "b@x.com");
    }

    #[test]
    fn profiles_missing_cache_is_empty_and_bad_json_errors() {
        assert!(parse_profiles("{}").unwrap().is_empty());
        assert!(parse_profiles("not json").is_err());
    }

    #[test]
    fn browser_pick_order() {
        use Browser::*;
        assert_eq!(pick_browser(Some(Edge), Some(Chrome), &[Chrome]), Ok(Edge));
        assert_eq!(pick_browser(None, Some(Edge), &[Chrome, Edge]), Ok(Edge));
        assert_eq!(pick_browser(None, Some(Edge), &[Chrome]), Ok(Chrome));
        assert_eq!(pick_browser(None, None, &[Chrome, Edge]), Ok(Chrome));
        assert_eq!(pick_browser(None, Some(Edge), &[]), Ok(Edge));
        assert!(pick_browser(None, None, &[])
            .unwrap_err()
            .starts_with("no supported browser"));
    }

    #[test]
    fn resolve_hit_miss_fallback() {
        let ps = [p("Profile 2", "b@x.com"), p("Default", "a@x.com")];
        assert_eq!(resolve(&ps, "B@X.com", true), (Some(&ps[0]), Note::None));
        assert_eq!(
            resolve(&ps, "b@x.com", false),
            (Some(&ps[0]), Note::StoredDefault)
        );
        assert_eq!(resolve(&ps, "nope@x", true), (Some(&ps[1]), Note::Miss));
        assert_eq!(resolve(&ps, "", false), (Some(&ps[1]), Note::None));
        let no_default = [p("Profile 2", "b@x.com")];
        assert_eq!(resolve(&no_default, "", false).0, Some(&no_default[0]));
        assert_eq!(resolve(&[], "x", true), (None, Note::Miss));
    }

    #[test]
    fn resolve_by_name_when_alias_differs() {
        let named = |dir: &str, email: &str, name: &str| Profile {
            dir: dir.into(),
            email: email.into(),
            name: name.into(),
        };
        let ps = [
            named("Default", "a@x.com", "Personal"),
            named("Profile 3", "upn@corp.onmicrosoft.com", " Me@Corp.com "),
            named("Profile 4", "", "nobody@corp.com"),
        ];
        // Email wins over name; name is the fallback, trimmed and case-insensitive.
        assert_eq!(resolve(&ps, "me@corp.com", true), (Some(&ps[1]), Note::None));
        assert_eq!(
            resolve(&ps, "me@corp.com", false),
            (Some(&ps[1]), Note::StoredDefault)
        );
        // A profile with no signed-in account is never matched by name.
        assert_eq!(resolve(&ps, "nobody@corp.com", true), (Some(&ps[0]), Note::Miss));
    }

    #[test]
    fn merge_keeps_keys_and_order() {
        let existing: Map<String, Value> =
            serde_json::from_str(r#"{"browser":"chrome","x":1}"#).unwrap();
        let next = merge_config(&existing, "a@x", None);
        assert_eq!(
            serde_json::to_string(&next).unwrap(),
            r#"{"browser":"chrome","x":1,"defaultProfileEmail":"a@x"}"#
        );
        let next = merge_config(&existing, "a@x", Some(Browser::Edge));
        assert_eq!(
            serde_json::to_string(&next).unwrap(),
            r#"{"browser":"edge","x":1,"defaultProfileEmail":"a@x"}"#
        );
    }

    #[test]
    fn stored_values_of_wrong_type_are_ignored() {
        let cfg: Map<String, Value> =
            serde_json::from_str(r#"{"browser":"firefox","defaultProfileEmail":5}"#).unwrap();
        assert_eq!(stored_browser(&cfg), None);
        assert_eq!(stored_email(&cfg), "");
    }

    #[test]
    fn ps_quote_doubles_single_quotes() {
        assert_eq!(ps_quote("abc"), "'abc'");
        assert_eq!(ps_quote("it's cool"), "'it''s cool'");
        assert_eq!(
            ps_quote(r#"--profile-directory="Profile 2""#),
            r#"'--profile-directory="Profile 2"'"#
        );
    }

    #[test]
    fn wsl_launch_plan_quotes_args_and_preserves_url_and_spaces() {
        let plan = launch_plan(
            Os::Wsl,
            Browser::Edge,
            "Profile 2",
            "https://example.com/?a=1&b=2'test",
            None,
        )
        .unwrap();
        assert_eq!(plan.program, "powershell.exe");
        assert_eq!(plan.args[0], "-NoProfile");
        assert_eq!(plan.args[1], "-Command");
        assert_eq!(
            plan.args[2],
            "Start-Process msedge.exe -ArgumentList '--profile-directory=\"Profile 2\"','https://example.com/?a=1&b=2''test'"
        );
    }

    #[test]
    fn macos_launch_plan_constructs_open_args() {
        let plan = launch_plan(
            Os::Macos,
            Browser::Chrome,
            "Default",
            "https://example.com/pr/42",
            None,
        )
        .unwrap();
        assert_eq!(
            plan,
            LaunchPlan {
                program: "open".into(),
                args: vec![
                    "-na".into(),
                    "Google Chrome".into(),
                    "--args".into(),
                    "--profile-directory=Default".into(),
                    "https://example.com/pr/42".into(),
                ],
            }
        );
    }

    #[test]
    fn linux_launch_plan_finds_bin_or_fails() {
        // When not on path:
        let err = launch_plan(
            Os::Linux,
            Browser::Chrome,
            "Default",
            "https://example.com",
            Some("/nonexistent"),
        )
        .unwrap_err();
        assert_eq!(
            err,
            "no chrome binary found on PATH (tried google-chrome, google-chrome-stable, chromium)"
        );
    }

    #[test]
    fn linux_launch_plan_edge_candidates() {
        let err = launch_plan(
            Os::Linux,
            Browser::Edge,
            "Default",
            "https://example.com",
            Some("/nonexistent"),
        )
        .unwrap_err();
        assert_eq!(
            err,
            "no edge binary found on PATH (tried microsoft-edge, microsoft-edge-stable)"
        );
    }
}
