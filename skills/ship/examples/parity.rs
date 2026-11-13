//! Parity harness (Story 5.1): runs every `ship` subcommand through the TS scripts
//! (`bun scripts/ship-*.ts`) and the Rust binary side by side, diffs their `key=value`
//! stdout lines and exit codes, and times median startup per subcommand.
//!
//! ```sh
//! cargo build --release
//! cargo run --release --example parity -- --azure <clone> --github <clone> --github-pr 35
//! ```
//!
//! Safety model. The source clones are only read: `git clone --no-local` from them, and
//! `status` / `for-each-ref` / `config --list` with optional locks off to prove they did not
//! change. Every case runs in a scratch clone under the system temp dir. Its origin keeps
//! the real URL, so detection and Azure coordinate parsing behave as on a real clone, but
//! `url.<sink>.pushInsteadOf=<real url>` reroutes every push to a local bare repo. Each
//! implementation gets its own clone and sink. Only `--live` writes to the real remotes.
//!
//! Only stdout lines matching `^[a-z_]+=` and the exit code are compared; stderr is human
//! text. The report carries case labels, verdicts, exit codes and timings, never stdout
//! values (Azure org/project/repo names must not reach the public repo). See PARITY.md.

use std::ffi::OsString;
use std::fmt::Write as _;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};
use std::sync::mpsc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use std::{env, fs, thread};

use ship::Platform as Kind;

const USAGE: &str = "\
usage: cargo run --release --example parity -- --azure <clone> --github <clone> [options]

  --azure <clone>         Azure Repos clone (only read, never written)
  --github <clone>        GitHub clone (only read, never written)
  --azure-pr <id>         Azure PR id for the live `tag --list` read (skipped when absent)
  --github-pr <id>        GitHub PR number for the live `tag --list` read (skipped when absent)
  --open-profile <email>  Also compare `open <url> --dry-run --profile <email>`
  --runs <n>              Timed runs per implementation and subcommand (default 15)
  --report <file>         Write the case and timing tables there as markdown
  --live                  Also run the write paths against the real remotes (throwaway
                          draft PRs, tag add/remove/list), then clean up
  --ship <bin>            Rust binary (default target/release/ship)
  --scripts <dir>         TS scripts directory (default scripts/)
  -h, --help              Show this help

Exit: 0 when every compared case is `same` and every timing row passes;
1 on any DIFF, ERROR, timing FAIL, LEFTOVER or hygiene failure; 2 on a usage error.";

/// Timing rows, in report order. `detect` and `preflight` are timed on real runs; the
/// others need the network for a real run, so `--help` measures startup instead.
const TIMED: [&str; 7] = ["detect", "preflight", "push", "pr", "tag", "snapshot", "open"];
/// `detect` and `preflight` must also beat this absolute median on Linux (NFR9).
const FAST_SUBCOMMANDS: [&str; 2] = ["detect", "preflight"];
const FAST_LIMIT_MS: f64 = 50.0;
const DEFAULT_RUNS: usize = 15;
const MAX_RUNS: usize = 1000;

/// Upper bounds for child processes. A live `pr` makes several API round trips; a clone
/// of a large repo can take minutes. Nothing the harness starts may wait forever.
const CASE_TIMEOUT: Duration = Duration::from_secs(180);
const TIMING_TIMEOUT: Duration = Duration::from_secs(60);
const GIT_TIMEOUT: Duration = Duration::from_secs(600);
const TOOL_TIMEOUT: Duration = Duration::from_secs(120);
/// How long to wait for a pipe to close after the child exits: a grandchild that
/// inherited it (a browser, a credential daemon) must not hang the harness.
const PIPE_GRACE: Duration = Duration::from_secs(5);

const IDENT_NAME: &str = "ship parity";
const IDENT_EMAIL: &str = "ship-parity@example.invalid";
const FIXED_DATE: &str = "2026-01-01T00:00:00+0000";
const OPEN_URL: &str = "https://example.com/ship-parity";
const LIVE_TITLE: &str = "chore: ship parity check (throwaway)";
const LIVE_TAG: &str = "ship-parity";
/// Labels a live GitHub run can create on the repo: the explicit tag and the one `pr`
/// derives from the `chore:` title. Removed afterwards only if the run created them.
const WATCHED_LABELS: [&str; 2] = [LIVE_TAG, "chore"];
/// Azure DevOps API resource id (public constant, the same for every org).
const ADO_RESOURCE: &str = "499b84ac-1321-427f-aa17-267ca6975798";

/// Keys whose values carry ids that differ between two live runs by design.
const VOLATILE_KEYS: [&str; 4] = ["pr_url", "pr_id", "pr_number", "work_item"];

/// Removed from every child. `SHIP_PLATFORM` would change detection under both
/// implementations (the override case sets it explicitly); inherited `GIT_DIR`-style
/// variables would point git at another repository.
const SCRUBBED_ENV: [&str; 4] = ["SHIP_PLATFORM", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"];

fn main() -> ExitCode {
    let argv: Vec<String> = env::args().skip(1).collect();
    let opts = match parse_args(&argv) {
        Ok(Parsed::Help) => {
            println!("{USAGE}");
            return ExitCode::SUCCESS;
        }
        Ok(Parsed::Run(o)) => o,
        Err(msg) => {
            eprintln!("parity: {msg}\n\n{USAGE}");
            return ExitCode::from(2);
        }
    };
    let inputs = match validate(&opts) {
        Ok(i) => i,
        Err(errors) => {
            for e in errors {
                eprintln!("parity: {e}");
            }
            eprintln!("\n{USAGE}");
            return ExitCode::from(2);
        }
    };
    match execute(&opts, &inputs) {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::from(1),
        Err(msg) => {
            eprintln!("parity: {msg}");
            ExitCode::from(1)
        }
    }
}

// ---------------------------------------------------------------------------------------
// Arguments
// ---------------------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
struct Opts {
    azure: PathBuf,
    github: PathBuf,
    azure_pr: Option<String>,
    github_pr: Option<String>,
    open_profile: Option<String>,
    runs: usize,
    report: Option<PathBuf>,
    live: bool,
    ship: PathBuf,
    scripts: PathBuf,
}

#[derive(Debug, PartialEq)]
enum Parsed {
    Run(Box<Opts>),
    Help,
}

fn parse_args(argv: &[String]) -> Result<Parsed, String> {
    let mut azure = None;
    let mut github = None;
    let mut azure_pr = None;
    let mut github_pr = None;
    let mut open_profile = None;
    let mut runs = DEFAULT_RUNS;
    let mut report = None;
    let mut live = false;
    let mut ship = PathBuf::from("target/release/ship");
    let mut scripts = PathBuf::from("scripts");

    let mut i = 0;
    while i < argv.len() {
        let flag = argv[i].as_str();
        let mut value = || -> Result<String, String> {
            i += 1;
            argv.get(i).cloned().ok_or_else(|| format!("{flag} requires a value"))
        };
        match flag {
            "-h" | "--help" => return Ok(Parsed::Help),
            "--azure" => azure = Some(PathBuf::from(value()?)),
            "--github" => github = Some(PathBuf::from(value()?)),
            "--azure-pr" => azure_pr = Some(pr_id(flag, value()?)?),
            "--github-pr" => github_pr = Some(pr_id(flag, value()?)?),
            "--open-profile" => open_profile = Some(value()?),
            "--runs" => {
                let v = value()?;
                runs = v
                    .parse::<usize>()
                    .ok()
                    .filter(|n| (1..=MAX_RUNS).contains(n))
                    .ok_or_else(|| format!("--runs '{v}': expected a number from 1 to {MAX_RUNS}"))?;
            }
            "--report" => report = Some(PathBuf::from(value()?)),
            "--live" => live = true,
            "--ship" => ship = PathBuf::from(value()?),
            "--scripts" => scripts = PathBuf::from(value()?),
            other => return Err(format!("unknown argument '{other}'")),
        }
        i += 1;
    }
    let azure = azure.ok_or("missing --azure <clone> (an Azure Repos clone)")?;
    let github = github.ok_or("missing --github <clone> (a GitHub clone)")?;
    Ok(Parsed::Run(Box::new(Opts {
        azure,
        github,
        azure_pr,
        github_pr,
        open_profile,
        runs,
        report,
        live,
        ship,
        scripts,
    })))
}

fn pr_id(flag: &str, v: String) -> Result<String, String> {
    if !v.is_empty() && v.bytes().all(|b| b.is_ascii_digit()) {
        Ok(v)
    } else {
        Err(format!("{flag} '{v}': expected digits only"))
    }
}

// ---------------------------------------------------------------------------------------
// Input validation (runs before any scratch directory exists)
// ---------------------------------------------------------------------------------------

struct Source {
    name: &'static str,
    kind: Kind,
    path: PathBuf,
    url: String,
    pr: Option<String>,
}

struct Inputs {
    /// GitHub first, then Azure.
    sources: Vec<Source>,
    impls: Impls,
    bun_version: String,
    ship_version: String,
}

/// Every problem with the inputs, so one run names all of them. Nothing is written.
fn validate(o: &Opts) -> Result<Inputs, Vec<String>> {
    let mut errors = Vec::new();
    let github = check_source("--github", &o.github, Kind::Github, o.github_pr.clone());
    let azure = check_source("--azure", &o.azure, Kind::Azure, o.azure_pr.clone());

    let ship = match fs::canonicalize(&o.ship) {
        Ok(p) if p.is_file() => Some(p),
        _ => {
            errors.push(format!(
                "ship binary not built: {} not found (run `cargo build --release`, or pass --ship)",
                o.ship.display()
            ));
            None
        }
    };
    let scripts = match fs::canonicalize(&o.scripts) {
        Ok(dir) => {
            let missing: Vec<String> = TIMED
                .iter()
                .map(|s| format!("ship-{s}.ts"))
                .filter(|f| !dir.join(f).is_file())
                .collect();
            if missing.is_empty() {
                Some(dir)
            } else {
                errors.push(format!("TS scripts missing in {}: {}", o.scripts.display(), missing.join(", ")));
                None
            }
        }
        Err(_) => {
            errors.push(format!("TS scripts directory not found: {} (pass --scripts)", o.scripts.display()));
            None
        }
    };
    let bun_version = tool_version(Cmd::new("bun", vec!["--version".into()], Path::new(".")));
    if bun_version.is_none() {
        errors.push("bun not found on PATH (the TS reference implementation needs it)".into());
    }
    let ship_version = ship
        .as_ref()
        .and_then(|p| tool_version(Cmd::new(p.clone(), vec!["--version".into()], Path::new("."))));
    if ship.is_some() && ship_version.is_none() {
        errors.push(format!("{} --version failed: is it the ship binary?", o.ship.display()));
    }

    let mut sources = Vec::new();
    for s in [github, azure] {
        match s {
            Ok(src) => sources.push(src),
            Err(e) => errors.push(e),
        }
    }
    match (ship, scripts, bun_version, ship_version) {
        (Some(ship), Some(scripts), Some(bun_version), Some(ship_version)) if errors.is_empty() => Ok(Inputs {
            sources,
            impls: Impls { ship, scripts },
            bun_version,
            ship_version,
        }),
        _ => Err(errors),
    }
}

fn check_source(flag: &str, path: &Path, want: Kind, pr: Option<String>) -> Result<Source, String> {
    if let Some(e) = missing_path_error(flag, path) {
        return Err(e);
    }
    let path = fs::canonicalize(path).map_err(|e| format!("{flag} {}: {e}", path.display()))?;
    if read_git(&path, &["rev-parse", "--git-dir"]).is_err() {
        return Err(format!("{flag} {}: not a git repository", path.display()));
    }
    if read_git(&path, &["rev-parse", "--verify", "--quiet", "HEAD"]).is_err() {
        return Err(format!("{flag} {}: has no commits", path.display()));
    }
    let url = read_git(&path, &["remote", "get-url", "origin"])
        .ok()
        .filter(|u| !u.is_empty())
        .ok_or_else(|| format!("{flag} {}: has no origin remote", path.display()))?;
    let kind = ship::detect_kind(&url, None);
    if kind != want {
        return Err(format!(
            "{flag} {}: origin is detected as {}, expected {}",
            path.display(),
            kind.as_str(),
            want.as_str()
        ));
    }
    Ok(Source {
        name: want.as_str(),
        kind,
        path,
        url,
        pr,
    })
}

fn missing_path_error(flag: &str, path: &Path) -> Option<String> {
    match fs::metadata(path) {
        Ok(m) if m.is_dir() => None,
        Ok(_) => Some(format!("{flag} {}: not a directory", path.display())),
        Err(_) => Some(format!("{flag} {}: not found", path.display())),
    }
}

fn tool_version(cmd: Cmd) -> Option<String> {
    let r = run(&cmd, true, TOOL_TIMEOUT).ok()?;
    (r.exit == Some(0) && !r.timed_out).then(|| r.stdout.trim().to_string())
}

/// Refuse a binary older than the sources it is built from (only checkable when the
/// harness runs from `skills/ship`, as `cargo run --example` does): a PASS against a
/// stale build is not evidence.
fn check_fresh(ship: &Path) -> Result<(), String> {
    let Ok(built) = fs::metadata(ship).and_then(|m| m.modified()) else { return Ok(()) };
    // Only src/: an edit to Cargo.toml that cargo judges irrelevant to the binary (a new
    // example target, say) does not relink it, so its mtime would be a false alarm.
    let mut stamps: Vec<SystemTime> = Vec::new();
    let mut dirs = vec![PathBuf::from("src")];
    while let Some(d) = dirs.pop() {
        for e in fs::read_dir(&d).into_iter().flatten().flatten() {
            let Ok(m) = e.metadata() else { continue };
            if m.is_dir() {
                dirs.push(e.path());
            } else if let Ok(t) = m.modified() {
                stamps.push(t);
            }
        }
    }
    if stamps.into_iter().any(|t| t > built) {
        return Err(format!(
            "{} is older than src/; run `cargo build --release` first",
            ship.display()
        ));
    }
    Ok(())
}

// ---------------------------------------------------------------------------------------
// Pure comparison logic
// ---------------------------------------------------------------------------------------

type Kv = Vec<(String, String)>;

/// `^[a-z_]+=`: the machine-readable stdout lines of both implementations.
fn is_kv_line(line: &str) -> bool {
    match line.find('=') {
        Some(i) if i > 0 => line[..i].bytes().all(|b| b.is_ascii_lowercase() || b == b'_'),
        _ => false,
    }
}

fn parse_kv(stdout: &str) -> Kv {
    stdout
        .lines()
        .filter(|l| is_kv_line(l))
        .filter_map(|l| l.split_once('='))
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

/// Replace every run of ASCII digits with `<N>`.
fn mask_digits(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut in_digits = false;
    for c in s.chars() {
        if c.is_ascii_digit() {
            if !in_digits {
                out.push_str("<N>");
            }
            in_digits = true;
        } else {
            out.push(c);
            in_digits = false;
        }
    }
    out
}

fn normalize(kv: &Kv) -> Kv {
    kv.iter()
        .map(|(k, v)| {
            let v = if VOLATILE_KEYS.contains(&k.as_str()) { mask_digits(v) } else { v.clone() };
            (k.clone(), v)
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq)]
struct Outcome {
    /// `None` when the process was ended by a signal.
    exit: Option<i32>,
    kv: Kv,
}

/// `tag --list` prints `platform=<kind>` followed by bare label names: keep those lines
/// too (as `("", <line>)` pairs), so a missing or extra label is a DIFF. Values never
/// reach the report.
fn parse_with_bare_lines(stdout: &str) -> Kv {
    stdout
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| match l.split_once('=') {
            Some((k, v)) if is_kv_line(l) => (k.to_string(), v.to_string()),
            _ => (String::new(), l.to_string()),
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq)]
enum Verdict {
    Same,
    Diff {
        exit: Option<(Option<i32>, Option<i32>)>,
        output: bool,
    },
    /// Not run, by design (an optional input was not given). Not a pass, not a failure.
    Skipped(String),
    /// Could not be run or compared (spawn failure, timeout, setup failure). A failure.
    Error(String),
}

impl Verdict {
    fn is_failure(&self) -> bool {
        matches!(self, Verdict::Diff { .. } | Verdict::Error(_))
    }

    fn label(&self) -> String {
        match self {
            Verdict::Same => "same".into(),
            Verdict::Diff { exit, output } => {
                let mut parts = Vec::new();
                if let Some((t, r)) = exit {
                    parts.push(format!("exit {} vs {}", exit_text(*t), exit_text(*r)));
                }
                if *output {
                    parts.push("key=value lines".into());
                }
                format!("DIFF ({})", parts.join("; "))
            }
            Verdict::Skipped(why) => format!("skipped: {why}"),
            Verdict::Error(why) => format!("ERROR: {why}"),
        }
    }
}

fn exit_text(code: Option<i32>) -> String {
    code.map_or_else(|| "signal".into(), |c| c.to_string())
}

fn compare(ts: &Outcome, rs: &Outcome) -> Verdict {
    let exit = (ts.exit != rs.exit).then_some((ts.exit, rs.exit));
    let output = normalize(&ts.kv) != normalize(&rs.kv);
    if exit.is_none() && !output { Verdict::Same } else { Verdict::Diff { exit, output } }
}

#[derive(Debug, Clone)]
struct CaseResult {
    platform: &'static str,
    label: String,
    ts: Option<Outcome>,
    rs: Option<Outcome>,
    verdict: Verdict,
}

impl CaseResult {
    fn not_run(platform: &'static str, label: &str, verdict: Verdict) -> Self {
        CaseResult {
            platform,
            label: label.to_string(),
            ts: None,
            rs: None,
            verdict,
        }
    }
}

fn median_ms(samples: &[f64]) -> f64 {
    if samples.is_empty() {
        return f64::NAN;
    }
    let mut v = samples.to_vec();
    v.sort_by(f64::total_cmp);
    let mid = v.len() / 2;
    if v.len() % 2 == 1 { v[mid] } else { (v[mid - 1] + v[mid]) / 2.0 }
}

#[derive(Debug, Clone, PartialEq)]
struct TimingCheck {
    pass: bool,
    note: String,
}

/// The NFR9 rules: the binary median is below the TS median, every run exited 0, and on
/// Linux `detect`/`preflight` binary medians are under 50 ms (skipped, and noted, elsewhere).
fn timing_check(sub: &str, ts_ms: f64, rs_ms: f64, failed_runs: usize, on_linux: bool) -> TimingCheck {
    let fail = |note: String| TimingCheck { pass: false, note };
    if failed_runs > 0 {
        return fail(format!("{failed_runs} run(s) failed or exited non-zero"));
    }
    // NaN (no successful sample) compares as not-less, so it fails here too.
    if rs_ms.partial_cmp(&ts_ms) != Some(std::cmp::Ordering::Less) {
        return fail("binary median not below TS median".into());
    }
    if FAST_SUBCOMMANDS.contains(&sub) {
        if !on_linux {
            return TimingCheck {
                pass: true,
                note: format!("{FAST_LIMIT_MS:.0} ms rule skipped (not Linux)"),
            };
        }
        if rs_ms >= FAST_LIMIT_MS {
            return fail(format!("binary median not under {FAST_LIMIT_MS:.0} ms"));
        }
        return TimingCheck {
            pass: true,
            note: format!("under {FAST_LIMIT_MS:.0} ms"),
        };
    }
    TimingCheck {
        pass: true,
        note: String::new(),
    }
}

#[derive(Debug, Clone)]
struct TimingRow {
    subcommand: &'static str,
    measured: &'static str,
    ts_ms: f64,
    rs_ms: f64,
    check: TimingCheck,
}

#[derive(Debug, Clone, Default)]
struct Meta {
    generated: String,
    host: String,
    runs: usize,
    live: bool,
    bun_version: String,
    ship_version: String,
    sources_unchanged: bool,
    scratch_removed: bool,
    leftovers: usize,
}

#[derive(Debug, Default, PartialEq)]
struct Counts {
    same: usize,
    diff: usize,
    skipped: usize,
    error: usize,
    timing_pass: usize,
    timing_fail: usize,
}

fn counts(cases: &[CaseResult], timings: &[TimingRow]) -> Counts {
    let mut c = Counts::default();
    for case in cases {
        match case.verdict {
            Verdict::Same => c.same += 1,
            Verdict::Diff { .. } => c.diff += 1,
            Verdict::Skipped(_) => c.skipped += 1,
            Verdict::Error(_) => c.error += 1,
        }
    }
    for t in timings {
        if t.check.pass {
            c.timing_pass += 1;
        } else {
            c.timing_fail += 1;
        }
    }
    c
}

/// Exit 0 only when every compared case is `same`, every timing row passes, there is
/// at least one timing row, the run left the sources and the temp dir as it found them,
/// and the live tier (if run) cleaned up everything it created on the real remotes.
fn overall_pass(cases: &[CaseResult], timings: &[TimingRow], meta: &Meta) -> bool {
    !timings.is_empty()
        && cases.iter().all(|c| !c.verdict.is_failure())
        && timings.iter().all(|t| t.check.pass)
        && meta.sources_unchanged
        && meta.scratch_removed
        && meta.leftovers == 0
}

fn exit_cell(o: Option<&Outcome>) -> String {
    o.map_or_else(|| "—".into(), |o| exit_text(o.exit))
}

fn yes_no(b: bool) -> &'static str {
    if b { "yes" } else { "no" }
}

/// Markdown report: labels, verdicts, exit codes and timings only. Stdout values never
/// reach it, so the Azure org/project/repo names stay out of the public repo.
fn render_report(cases: &[CaseResult], timings: &[TimingRow], meta: &Meta) -> String {
    let c = counts(cases, timings);
    let pass = overall_pass(cases, timings, meta);
    let mut s = String::new();
    let _ = writeln!(s, "# ship parity report\n");
    let _ = writeln!(s, "- Generated: {}", meta.generated);
    let _ = writeln!(s, "- Host: {}", meta.host);
    let _ = writeln!(s, "- Implementations: bun {} vs {}", meta.bun_version, meta.ship_version);
    let _ = writeln!(s, "- Timed runs per implementation: {} (one warm-up discarded)", meta.runs);
    let _ = writeln!(s, "- Live tier: {}", if meta.live { "run" } else { "not run" });
    let _ = writeln!(s, "- Result: **{}**\n", if pass { "PASS" } else { "FAIL" });

    let _ = writeln!(s, "## Cases\n");
    let _ = writeln!(s, "| Platform | Case | TS exit | RS exit | Verdict |");
    let _ = writeln!(s, "|---|---|---|---|---|");
    for case in cases {
        let _ = writeln!(
            s,
            "| {} | `{}` | {} | {} | {} |",
            case.platform,
            case.label,
            exit_cell(case.ts.as_ref()),
            exit_cell(case.rs.as_ref()),
            case.verdict.label()
        );
    }
    let _ = writeln!(
        s,
        "\n{} same, {} DIFF, {} skipped, {} ERROR.\n",
        c.same, c.diff, c.skipped, c.error
    );

    let _ = writeln!(s, "## Startup timing (median ms)\n");
    let _ = writeln!(s, "| Subcommand | Measured | TS median | RS median | Verdict | Note |");
    let _ = writeln!(s, "|---|---|---|---|---|---|");
    for t in timings {
        let _ = writeln!(
            s,
            "| {} | {} | {:.1} | {:.1} | {} | {} |",
            t.subcommand,
            t.measured,
            t.ts_ms,
            t.rs_ms,
            if t.check.pass { "pass" } else { "FAIL" },
            t.check.note
        );
    }
    let _ = writeln!(s, "\n{} pass, {} FAIL.\n", c.timing_pass, c.timing_fail);

    let _ = writeln!(s, "## Hygiene\n");
    let _ = writeln!(s, "- Source clones unchanged (status, branches, tags, config): {}", yes_no(meta.sources_unchanged));
    let _ = writeln!(s, "- Scratch directory removed: {}", yes_no(meta.scratch_removed));
    if meta.live {
        let _ = writeln!(s, "- Live leftovers not cleaned up: {} (details on the console)", meta.leftovers);
    }
    s
}

/// Branch nonce: lowercase letters only, so `parse_work_item` finds no id in the branch
/// name and a live `pr` never links an unrelated work item.
fn nonce_from(seed: u128) -> String {
    let mut n = seed;
    let mut s = String::with_capacity(10);
    for _ in 0..10 {
        s.push(char::from(b'a' + (n % 26) as u8));
        n /= 26;
    }
    s
}

/// `YYYY-MM-DD HH:MM UTC` from Unix seconds (std has no calendar).
fn utc_stamp(secs: u64) -> String {
    let days = i64::try_from(secs / 86_400).unwrap_or(0);
    let rem = secs % 86_400;
    let (y, m, d) = civil_from_days(days);
    format!("{y:04}-{m:02}-{d:02} {:02}:{:02} UTC", rem / 3600, (rem % 3600) / 60)
}

/// Days since 1970-01-01 to a proleptic Gregorian date (Howard Hinnant's algorithm).
fn civil_from_days(z: i64) -> (i64, i64, i64) {
    let z = z + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = yoe + era * 400 + i64::from(m <= 2);
    (y, m, d)
}

/// Label names from `gh label list --json name`.
fn parse_label_names(json: &str) -> Result<Vec<String>, String> {
    let v: serde_json::Value = serde_json::from_str(json).map_err(|e| format!("label list is not JSON: {e}"))?;
    let arr = v.as_array().ok_or("label list is not a JSON array")?;
    arr.iter()
        .map(|l| {
            l.get("name")
                .and_then(serde_json::Value::as_str)
                .map(str::to_string)
                .ok_or_else(|| "label entry has no string name".to_string())
        })
        .collect()
}

// ---------------------------------------------------------------------------------------
// Processes
// ---------------------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Side {
    Ts,
    Rs,
}

impl Side {
    const BOTH: [Side; 2] = [Side::Ts, Side::Rs];

    fn tag(self) -> &'static str {
        match self {
            Side::Ts => "ts",
            Side::Rs => "rs",
        }
    }

    fn idx(self) -> usize {
        match self {
            Side::Ts => 0,
            Side::Rs => 1,
        }
    }
}

struct Impls {
    ship: PathBuf,
    scripts: PathBuf,
}

impl Impls {
    /// `bun scripts/ship-<sub>.ts <args>` or `ship <sub> <args>`, as an argument array.
    fn cmd(&self, side: Side, sub: &str, args: &[String], cwd: &Path) -> Cmd {
        let (program, mut argv): (OsString, Vec<OsString>) = match side {
            Side::Ts => ("bun".into(), vec![self.scripts.join(format!("ship-{sub}.ts")).into_os_string()]),
            Side::Rs => (self.ship.clone().into_os_string(), vec![sub.into()]),
        };
        argv.extend(args.iter().map(OsString::from));
        Cmd::new(program, argv, cwd)
    }
}

struct Cmd {
    program: OsString,
    args: Vec<OsString>,
    cwd: PathBuf,
    env: Vec<(String, String)>,
}

impl Cmd {
    fn new(program: impl Into<OsString>, args: Vec<OsString>, cwd: &Path) -> Self {
        Cmd {
            program: program.into(),
            args,
            cwd: cwd.to_path_buf(),
            env: Vec::new(),
        }
    }

    fn tool(program: &str, args: &[&str], cwd: &Path) -> Self {
        Cmd::new(program, args.iter().map(OsString::from).collect(), cwd)
    }

    fn envs(mut self, env: &[(String, String)]) -> Self {
        self.env.extend(env.iter().cloned());
        self
    }
}

struct Run {
    exit: Option<i32>,
    stdout: String,
    stderr: String,
    elapsed: Duration,
    timed_out: bool,
}

/// Run `cmd` from its argument array (never a shell), stdin closed, with a hard timeout.
/// `capture` pipes stdout/stderr; otherwise both go to /dev/null (timing runs).
fn run(cmd: &Cmd, capture: bool, timeout: Duration) -> Result<Run, String> {
    let mut c = Command::new(&cmd.program);
    c.args(&cmd.args)
        .current_dir(&cmd.cwd)
        .stdin(Stdio::null())
        .env("GIT_TERMINAL_PROMPT", "0");
    for k in SCRUBBED_ENV {
        c.env_remove(k);
    }
    for (k, v) in &cmd.env {
        c.env(k, v);
    }
    let pipe = || if capture { Stdio::piped() } else { Stdio::null() };
    c.stdout(pipe()).stderr(pipe());

    let start = Instant::now();
    let mut child = c
        .spawn()
        .map_err(|e| format!("cannot start {}: {e}", Path::new(&cmd.program).display()))?;
    let stdout = child.stdout.take().map(drain);
    let stderr = child.stderr.take().map(drain);
    // Poll rather than block so the timeout holds; 100 µs steps while the child is young
    // keep the timing bias far below the millisecond resolution the report uses.
    let (exit, elapsed, timed_out) = loop {
        match child.try_wait() {
            Ok(Some(status)) => break (status.code(), start.elapsed(), false),
            Ok(None) => {}
            Err(e) => {
                let _ = child.kill();
                return Err(format!("waiting for {} failed: {e}", Path::new(&cmd.program).display()));
            }
        }
        let waited = start.elapsed();
        if waited >= timeout {
            let _ = child.kill();
            let _ = child.wait();
            break (None, waited, true);
        }
        thread::sleep(if waited < Duration::from_millis(250) {
            Duration::from_micros(100)
        } else {
            Duration::from_millis(5)
        });
    };
    // A pipe still open after the grace period (a grandchild holding it) is an error, not
    // empty output: two silently empty stdouts would otherwise compare as `same`.
    let collect = |rx: Option<mpsc::Receiver<Vec<u8>>>, which: &str| -> Result<String, String> {
        match rx {
            None => Ok(String::new()),
            Some(rx) => rx
                .recv_timeout(PIPE_GRACE)
                .map(|b| String::from_utf8_lossy(&b).into_owned())
                .map_err(|_| format!("{which} of {} not collected", Path::new(&cmd.program).display())),
        }
    };
    Ok(Run {
        exit,
        stdout: collect(stdout, "stdout")?,
        stderr: collect(stderr, "stderr")?,
        elapsed,
        timed_out,
    })
}

fn drain<R: Read + Send + 'static>(mut r: R) -> mpsc::Receiver<Vec<u8>> {
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let mut buf = Vec::new();
        let _ = r.read_to_end(&mut buf);
        let _ = tx.send(buf);
    });
    rx
}

fn check(run: Result<Run, String>, what: &str) -> Result<String, String> {
    let r = run?;
    if r.timed_out {
        return Err(format!("{what} timed out"));
    }
    if r.exit != Some(0) {
        return Err(format!("{what} exited {}: {}", exit_text(r.exit), r.stderr.trim()));
    }
    Ok(r.stdout.trim_end().to_string())
}

fn git_env(cwd: &Path, args: &[&str], env: &[(String, String)]) -> Result<String, String> {
    let what = format!("git {}", args.first().copied().unwrap_or_default());
    check(run(&Cmd::tool("git", args, cwd).envs(env), true, GIT_TIMEOUT), &what)
}

fn git(cwd: &Path, args: &[&str]) -> Result<String, String> {
    git_env(cwd, args, &[])
}

/// Read-only git on a source clone: optional locks off, so `status` never refreshes
/// (writes) the index.
fn read_git(cwd: &Path, args: &[&str]) -> Result<String, String> {
    git_env(cwd, args, &[("GIT_OPTIONAL_LOCKS".into(), "0".into())])
}

/// What must not change in a source clone: working-tree status, branches, tags, local config.
fn fingerprint(repo: &Path) -> Result<String, String> {
    let status = read_git(repo, &["status", "--porcelain=v1", "--untracked-files=all"])?;
    let refs = read_git(repo, &["for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags"])?;
    let config = read_git(repo, &["config", "--local", "--list"])?;
    Ok(format!("{status}\n--refs--\n{refs}\n--config--\n{config}"))
}

fn path_str(p: &Path) -> Result<&str, String> {
    p.to_str().ok_or_else(|| format!("path is not UTF-8: {}", p.display()))
}

fn fixed_identity_env() -> Vec<(String, String)> {
    [
        ("GIT_AUTHOR_NAME", IDENT_NAME),
        ("GIT_AUTHOR_EMAIL", IDENT_EMAIL),
        ("GIT_AUTHOR_DATE", FIXED_DATE),
        ("GIT_COMMITTER_NAME", IDENT_NAME),
        ("GIT_COMMITTER_EMAIL", IDENT_EMAIL),
        ("GIT_COMMITTER_DATE", FIXED_DATE),
    ]
    .iter()
    .map(|(k, v)| (k.to_string(), v.to_string()))
    .collect()
}

/// `git` auth for an Azure remote, passed by environment so the token never shows in a
/// process listing: the binary's own Bearer env, with the header scoped to `url`'s origin
/// so the token is not sent on redirects to other hosts.
fn ado_bearer_env(url: &str) -> Option<Vec<(String, String)>> {
    let args = ["account", "get-access-token", "--resource", ADO_RESOURCE, "--query", "accessToken", "-o", "tsv"];
    let token = check(run(&Cmd::tool("az", &args, Path::new(".")), true, TOOL_TIMEOUT), "az").ok()?;
    let token = token.trim();
    if token.is_empty() {
        return None;
    }
    Some(ship::git::bearer_env(token, &ship::git::extra_header_key(url), 0))
}

/// `gh` auth for a GitHub repo, mirroring ship: an explicit GH_TOKEN/GITHUB_TOKEN wins,
/// else the token of the account that owns the repo, else gh's active account.
fn gh_env(owner: &str) -> Vec<(String, String)> {
    if env::var_os("GH_TOKEN").is_some() || env::var_os("GITHUB_TOKEN").is_some() {
        return Vec::new();
    }
    match check(run(&Cmd::tool("gh", &["auth", "token", "-u", owner], Path::new(".")), true, TOOL_TIMEOUT), "gh") {
        Ok(t) if !t.trim().is_empty() => vec![("GH_TOKEN".into(), t.trim().to_string())],
        _ => Vec::new(),
    }
}

// ---------------------------------------------------------------------------------------
// Scratch state
// ---------------------------------------------------------------------------------------

/// The temp directory every scratch clone and sink lives in. Removed explicitly at the
/// end (so removal can be reported) and on drop as a fallback for early returns.
struct ScratchRoot {
    path: PathBuf,
    removed: bool,
}

impl ScratchRoot {
    fn create(nonce: &str) -> Result<Self, String> {
        let path = env::temp_dir().join(format!("ship-parity-{nonce}"));
        // 0700: the scratch clones are full copies of possibly private repos.
        let mut builder = fs::DirBuilder::new();
        #[cfg(unix)]
        std::os::unix::fs::DirBuilderExt::mode(&mut builder, 0o700);
        builder.create(&path).map_err(|e| format!("cannot create {}: {e}", path.display()))?;
        let mut root = ScratchRoot { path, removed: false };
        root.path = fs::canonicalize(&root.path).map_err(|e| format!("cannot resolve {}: {e}", root.path.display()))?;
        Ok(root)
    }

    fn remove(&mut self) -> bool {
        let _ = fs::remove_dir_all(&self.path);
        self.removed = !self.path.exists();
        self.removed
    }
}

impl Drop for ScratchRoot {
    fn drop(&mut self) {
        if !self.removed {
            let _ = fs::remove_dir_all(&self.path);
        }
    }
}

struct Scratch {
    dir: PathBuf,
    sink: PathBuf,
}

impl Scratch {
    /// Refuse to run anything that pushes unless pushes land in the local sink while
    /// the fetch URL stays the real one.
    fn assert_pushes_to_sink(&self, real_url: &str) -> Result<(), String> {
        let fetch = git(&self.dir, &["remote", "get-url", "origin"])?;
        let push = git(&self.dir, &["remote", "get-url", "--push", "origin"])?;
        if fetch != real_url || push != path_str(&self.sink)? {
            return Err(format!("{}: origin is not rerouted to the local sink; refusing to run", self.dir.display()));
        }
        Ok(())
    }
}

fn make_scratch(root: &Path, src: &Source, side: Side, nonce: &str, hooks: &Path) -> Result<Scratch, String> {
    let dir = root.join(format!("{}-{}", src.name, side.tag()));
    let sink = root.join(format!("{}-{}-sink.git", src.name, side.tag()));
    let (dir_s, sink_s, src_s, hooks_s) = (path_str(&dir)?, path_str(&sink)?, path_str(&src.path)?, path_str(hooks)?);
    // --no-local: objects come over the file transport, so nothing is hard-linked to
    // (or written in) the source clone.
    // The empty hooks dir applies to the clone itself too (post-checkout runs during it).
    let no_hooks = format!("core.hooksPath={hooks_s}");
    git(root, &["-c", &no_hooks, "clone", "--no-local", "--quiet", src_s, dir_s])?;
    git(root, &["init", "--quiet", "--bare", sink_s])?;
    git(&dir, &["remote", "set-url", "origin", &src.url])?;
    git(&dir, &["config", &format!("url.{sink_s}.pushInsteadOf"), &src.url])?;
    for (k, v) in [
        ("user.name", IDENT_NAME),
        ("user.email", IDENT_EMAIL),
        ("commit.gpgSign", "false"),
        ("tag.gpgSign", "false"),
        // `tag.gpgSign=false` does not override a global forceSignAnnotated.
        ("tag.forceSignAnnotated", "false"),
        // The live push must not carry the snapshot tags to the real remote.
        ("push.followTags", "false"),
        // An empty hooks dir: the operator's global hooks must not run in scratch clones.
        ("core.hooksPath", hooks_s),
        // A global `status.showUntrackedFiles=no` hides untracked files from the TS
        // porcelain but not from Rust (`--untracked-files=normal`, Story 1.2's second
        // approved fix). Pin it so the comparison does not depend on the operator's config.
        ("status.showUntrackedFiles", "normal"),
    ] {
        git(&dir, &["config", k, v])?;
    }
    git(&dir, &["checkout", "--quiet", "-b", &format!("ship-parity-{nonce}")])?;
    let s = Scratch { dir, sink };
    s.assert_pushes_to_sink(&src.url)?;
    Ok(s)
}

/// Commit `file` with fixed identity and dates, so both clones get the same commit hash.
fn commit_fixture(dir: &Path, file: &str, content: &str) -> Result<(), String> {
    fs::write(dir.join(file), content).map_err(|e| format!("cannot write {file}: {e}"))?;
    git(dir, &["add", "--force", "--", file])?;
    // `-- <file>` commits only that path: anything else staged stays staged.
    git_env(
        dir,
        &["commit", "--quiet", "--no-verify", "-m", &format!("chore: ship parity fixture ({file})"), "--", file],
        &fixed_identity_env(),
    )?;
    Ok(())
}

/// Apply the same state change to both clones and prove they still share HEAD.
fn in_both(pair: &[Scratch; 2], step: impl Fn(&Path) -> Result<(), String>) -> Result<(), String> {
    for s in pair {
        step(&s.dir)?;
    }
    let heads = [git(&pair[0].dir, &["rev-parse", "HEAD"])?, git(&pair[1].dir, &["rev-parse", "HEAD"])?];
    if heads[0] != heads[1] {
        return Err("scratch clones diverged (different HEAD after the same setup)".into());
    }
    Ok(())
}

// ---------------------------------------------------------------------------------------
// The run
// ---------------------------------------------------------------------------------------

struct CaseSpec<'a> {
    platform: &'static str,
    label: String,
    sub: &'a str,
    args: [Vec<String>; 2],
    env: Vec<(String, String)>,
    /// Compare non-`key=value` lines too (`tag --list` label names).
    bare_lines: bool,
}

impl<'a> CaseSpec<'a> {
    fn same(platform: &'static str, label: &str, sub: &'a str, args: &[&str]) -> Self {
        let args: Vec<String> = args.iter().map(|a| a.to_string()).collect();
        let bare_lines = sub == "tag" && args.iter().any(|a| a == "--list");
        CaseSpec {
            platform,
            label: label.to_string(),
            sub,
            args: [args.clone(), args],
            env: Vec::new(),
            bare_lines,
        }
    }
}

struct Harness<'a> {
    impls: &'a Impls,
    nonce: String,
    cases: Vec<CaseResult>,
    timings: Vec<TimingRow>,
    leftovers: Vec<String>,
}

impl Harness<'_> {
    fn case(&mut self, spec: CaseSpec, cwds: [&Path; 2]) -> CaseResult {
        let mut outs: [Option<Outcome>; 2] = [None, None];
        let mut errors = Vec::new();
        for side in Side::BOTH {
            let i = side.idx();
            let cmd = self.impls.cmd(side, spec.sub, &spec.args[i], cwds[i]).envs(&spec.env);
            match run(&cmd, true, CASE_TIMEOUT) {
                Ok(r) if r.timed_out => errors.push(format!("{} timed out", side.tag())),
                Ok(r) => {
                    let kv = if spec.bare_lines { parse_with_bare_lines(&r.stdout) } else { parse_kv(&r.stdout) };
                    outs[i] = Some(Outcome { exit: r.exit, kv });
                }
                Err(e) => errors.push(format!("{}: {e}", side.tag())),
            }
        }
        let verdict = match (&outs, errors.is_empty()) {
            ([Some(t), Some(r)], true) => compare(t, r),
            _ => Verdict::Error(errors.join("; ")),
        };
        let [ts, rs] = outs;
        let result = CaseResult {
            platform: spec.platform,
            label: spec.label,
            ts,
            rs,
            verdict,
        };
        eprintln!(">> {} {}: {}", result.platform, result.label, result.verdict.label());
        if matches!(result.verdict, Verdict::Diff { .. }) {
            print_diff(&result);
        }
        self.cases.push(result.clone());
        result
    }

    fn run_all(&mut self, o: &Opts, inputs: &Inputs, root: &Path) -> Result<(), String> {
        let hooks = root.join("no-hooks");
        let host = root.join("host");
        for d in [&hooks, &host] {
            fs::create_dir(d).map_err(|e| format!("cannot create {}: {e}", d.display()))?;
        }
        let mut pairs = Vec::new();
        for src in &inputs.sources {
            eprintln!(">> {}: building scratch clones", src.name);
            let pair = [
                make_scratch(root, src, Side::Ts, &self.nonce, &hooks)?,
                make_scratch(root, src, Side::Rs, &self.nonce, &hooks)?,
            ];
            self.hermetic_cases(src, &pair)?;
            self.live_read(src, &pair);
            pairs.push(pair);
        }
        self.host_cases(o, &host);
        let timing_pair = inputs
            .sources
            .iter()
            .position(|s| s.kind == Kind::Github)
            .and_then(|i| pairs.get(i))
            .ok_or("no GitHub scratch clones to time in")?;
        self.timing(timing_pair, o.runs);
        if o.live {
            for (src, pair) in inputs.sources.iter().zip(&pairs) {
                self.live(src, pair);
            }
        }
        Ok(())
    }

    fn hermetic_cases(&mut self, src: &Source, pair: &[Scratch; 2]) -> Result<(), String> {
        let p = src.name;
        let cwds = [pair[0].dir.as_path(), pair[1].dir.as_path()];
        let other = if src.kind == Kind::Github { "azure" } else { "github" };
        let snap = format!("ship-parity-{}-snap", self.nonce);
        let snap_pushed = format!("ship-parity-{}-snap-pushed", self.nonce);

        self.case(CaseSpec::same(p, "detect", "detect", &[]), cwds);
        let mut spec = CaseSpec::same(p, &format!("detect (SHIP_PLATFORM={other})"), "detect", &[]);
        spec.env.push(("SHIP_PLATFORM".into(), other.into()));
        self.case(spec, cwds);
        self.case(CaseSpec::same(p, "preflight (clean)", "preflight", &[]), cwds);

        in_both(pair, |d| {
            commit_fixture(d, "ship-parity.txt", "ship parity\n")?;
            fs::write(d.join("ship-parity.txt"), "ship parity\nmodified\n").map_err(|e| e.to_string())?;
            fs::write(d.join("ship-parity-untracked.txt"), "untracked\n").map_err(|e| e.to_string())
        })?;
        // Not compared here: porcelain would list the worktree-only edit first
        // (` M ship-parity.txt`), the line the TS trim bug misreads. Story 1.2 recorded that
        // difference as an approved fix, and recorded deviations are out of the comparison.
        // A staged new file that sorts first (`-` < `.`) puts `A  …` on the first line, so
        // the same dirty tree compares with the bug out of play.
        in_both(pair, |d| {
            fs::write(d.join("ship-parity-a-staged.txt"), "staged\n").map_err(|e| e.to_string())?;
            git(d, &["add", "--force", "--", "ship-parity-a-staged.txt"]).map(drop)
        })?;
        self.case(CaseSpec::same(p, "preflight (staged + modified + untracked)", "preflight", &[]), cwds);
        self.case(CaseSpec::same(p, "push", "push", &[]), cwds);
        self.case(CaseSpec::same(p, "preflight (after push)", "preflight", &[]), cwds);

        in_both(pair, |d| commit_fixture(d, "ship-parity-2.txt", "ahead\n"))?;
        self.case(CaseSpec::same(p, "preflight (1 commit ahead)", "preflight", &[]), cwds);

        let snapshot_args = ["--name", snap.as_str(), "-m", "ship parity check"];
        self.case(CaseSpec::same(p, "snapshot --name -m", "snapshot", &snapshot_args), cwds);
        self.case(CaseSpec::same(p, "snapshot --name -m (tag exists)", "snapshot", &snapshot_args), cwds);
        self.case(CaseSpec::same(p, "snapshot --name --push", "snapshot", &["--name", &snap_pushed, "--push"]), cwds);
        self.case(CaseSpec::same(p, "push --bogus", "push", &["--bogus"]), cwds);
        self.case(CaseSpec::same(p, "snapshot --bogus", "snapshot", &["--bogus"]), cwds);
        self.case(CaseSpec::same(p, "pr (no --title)", "pr", &[]), cwds);
        self.case(CaseSpec::same(p, "tag (no id)", "tag", &[]), cwds);
        Ok(())
    }

    /// `tag --list <id>`: a real read against the remote, only when an id was given.
    fn live_read(&mut self, src: &Source, pair: &[Scratch; 2]) {
        let flag = if src.kind == Kind::Github { "--github-pr" } else { "--azure-pr" };
        match &src.pr {
            Some(id) => {
                let cwds = [pair[0].dir.as_path(), pair[1].dir.as_path()];
                self.case(CaseSpec::same(src.name, "tag --list <id> (live read)", "tag", &["--list", id]), cwds);
            }
            None => self.cases.push(CaseResult::not_run(
                src.name,
                "tag --list <id> (live read)",
                Verdict::Skipped(format!("no {flag}")),
            )),
        }
    }

    fn host_cases(&mut self, o: &Opts, host: &Path) {
        let cwds = [host, host];
        self.case(CaseSpec::same("host", "open --list-profiles", "open", &["--list-profiles"]), cwds);
        self.case(CaseSpec::same("host", "open <url> --dry-run", "open", &[OPEN_URL, "--dry-run"]), cwds);
        let label = "open <url> --dry-run --profile <email>";
        match &o.open_profile {
            Some(email) => {
                self.case(CaseSpec::same("host", label, "open", &[OPEN_URL, "--dry-run", "--profile", email]), cwds);
            }
            None => self
                .cases
                .push(CaseResult::not_run("host", label, Verdict::Skipped("no --open-profile".into()))),
        }
    }

    /// Median wall time per implementation. Runs alternate TS/RS order so drift (CPU
    /// frequency, page cache) does not favour one side; the first round is a warm-up.
    fn timing(&mut self, pair: &[Scratch; 2], runs: usize) {
        for sub in TIMED {
            let (args, measured): (Vec<String>, &'static str) = if FAST_SUBCOMMANDS.contains(&sub) {
                (Vec::new(), "real run")
            } else {
                (vec!["--help".into()], "--help")
            };
            let mut samples: [Vec<f64>; 2] = [Vec::new(), Vec::new()];
            let mut failed = 0;
            for round in 0..=runs {
                let order = if round % 2 == 0 { Side::BOTH } else { [Side::Rs, Side::Ts] };
                for side in order {
                    let cmd = self.impls.cmd(side, sub, &args, &pair[side.idx()].dir);
                    match run(&cmd, false, TIMING_TIMEOUT) {
                        Ok(r) if !r.timed_out && r.exit == Some(0) => {
                            if round > 0 {
                                samples[side.idx()].push(r.elapsed.as_secs_f64() * 1000.0);
                            }
                        }
                        _ => failed += 1,
                    }
                }
            }
            let (ts_ms, rs_ms) = (median_ms(&samples[0]), median_ms(&samples[1]));
            let check = timing_check(sub, ts_ms, rs_ms, failed, cfg!(target_os = "linux"));
            eprintln!(
                ">> timing {sub}: ts {ts_ms:.1} ms, rs {rs_ms:.1} ms: {}",
                if check.pass { "pass" } else { "FAIL" }
            );
            self.timings.push(TimingRow {
                subcommand: sub,
                measured,
                ts_ms,
                rs_ms,
                check,
            });
        }
    }

    /// The write paths against the real remote: push, draft PR, tag add/remove/list,
    /// then best-effort cleanup. Each side works on its own branch and PR.
    fn live(&mut self, src: &Source, pair: &[Scratch; 2]) {
        let p = src.name;
        let branches = Side::BOTH.map(|s| format!("ship-parity-{}-{}", self.nonce, s.tag()));
        let cwds = [pair[0].dir.as_path(), pair[1].dir.as_path()];

        for side in Side::BOTH {
            let s = &pair[side.idx()];
            let step = (|| -> Result<(), String> {
                let key = format!("url.{}.pushInsteadOf", path_str(&s.sink)?);
                git(&s.dir, &["config", "--unset-all", &key])?;
                git(&s.dir, &["checkout", "--quiet", "-b", &branches[side.idx()]])?;
                if git(&s.dir, &["remote", "get-url", "--push", "origin"])? != src.url {
                    return Err("push URL is not the real remote after the reroute was removed".into());
                }
                Ok(())
            })();
            if let Err(e) = step {
                // Raw git stderr stays on the console: it can name the remote and break the table.
                eprintln!("parity: {p}: live setup failed: {e}");
                self.cases.push(CaseResult::not_run(p, "live setup", Verdict::Error("live setup failed (see console)".into())));
                return;
            }
        }

        let gh_repo = ship::github_owner_repo(&src.url).map(|(o, r)| (format!("{o}/{r}"), gh_env(&o)));
        let labels_before = match &gh_repo {
            Some((repo, env)) if src.kind == Kind::Github => Some(gh_labels(repo, env)),
            None if src.kind == Kind::Github => {
                self.leftovers.push(format!(
                    "{p}: cannot parse GitHub owner/repo from origin; check by hand whether the run created {}",
                    WATCHED_LABELS.join(", ")
                ));
                None
            }
            _ => None,
        };

        self.case(CaseSpec::same(p, "live push", "push", &[]), cwds);
        let pr = self.case(
            // --no-reviewer: SHIP_ADO_DEFAULT_REVIEWER must not notify a real person about a throwaway PR.
            CaseSpec::same(
                p,
                "live pr --draft",
                "pr",
                &["--draft", "--title", LIVE_TITLE, "--no-create-work-item", "--no-reviewer"],
            ),
            cwds,
        );
        let id_key = if src.kind == Kind::Github { "pr_number" } else { "pr_id" };
        let ids = [pr.ts.as_ref(), pr.rs.as_ref()].map(|o| {
            o.and_then(|o| o.kv.iter().find(|(k, _)| k == id_key).map(|(_, v)| v.clone()))
        });

        let tag_steps: [(&str, Vec<&str>); 3] = [
            ("live tag --add", vec!["--add", LIVE_TAG]),
            ("live tag --remove", vec!["--remove", LIVE_TAG]),
            ("live tag --list", vec!["--list"]),
        ];
        for (label, extra) in tag_steps {
            match &ids {
                [Some(t), Some(r)] => {
                    let args = [t, r].map(|id| {
                        std::iter::once(id.clone()).chain(extra.iter().map(|a| a.to_string())).collect::<Vec<_>>()
                    });
                    let spec = CaseSpec {
                        platform: p,
                        label: label.to_string(),
                        sub: "tag",
                        args,
                        env: Vec::new(),
                        bare_lines: extra.contains(&"--list"),
                    };
                    self.case(spec, cwds);
                }
                _ => self.cases.push(CaseResult::not_run(
                    p,
                    label,
                    Verdict::Error("no PR id from both live `pr` runs".into()),
                )),
            }
        }

        // Cleanup: close or abandon each PR, then delete each branch still on the remote.
        // The branch delete is attempted even when `push` failed or timed out: it checks
        // `ls-remote` first, and a timed-out push may still have landed.
        for side in Side::BOTH {
            let i = side.idx();
            let dir = &pair[i].dir;
            if ids[i].is_none() {
                self.leftovers.push(format!(
                    "{p}: {} `pr` printed no {id_key}; if a draft PR was opened from {}, close it by hand",
                    side.tag(),
                    branches[i]
                ));
            }
            if let Some(id) = &ids[i] {
                let closed = match (&gh_repo, src.kind) {
                    (Some((repo, env)), Kind::Github) => check(
                        run(
                            &Cmd::tool("gh", &["pr", "close", id, "--repo", repo, "--delete-branch"], dir).envs(env),
                            true,
                            TOOL_TIMEOUT,
                        ),
                        "gh pr close",
                    ),
                    (None, Kind::Github) => Err("cannot parse GitHub owner/repo from origin".into()),
                    _ => match ship::ado_parts(&src.url) {
                        Some(parts) => check(
                            run(
                                &Cmd::tool(
                                    "az",
                                    &[
                                        "repos", "pr", "update", "--id", id, "--status", "abandoned", "--org",
                                        &parts.org_url, "--output", "none", "--only-show-errors",
                                    ],
                                    dir,
                                ),
                                true,
                                TOOL_TIMEOUT,
                            ),
                            "az repos pr update",
                        ),
                        None => Err("cannot parse the Azure org from origin".into()),
                    },
                };
                if let Err(e) = closed {
                    self.leftovers.push(format!("{p}: {} PR {id} not closed/abandoned: {e}", side.tag()));
                }
            }
            let auth = if src.kind == Kind::Azure { ado_bearer_env(&src.url) } else { None };
            if let Err(e) = delete_remote_branch(dir, &branches[i], auth.as_deref()) {
                self.leftovers.push(format!("{p}: branch {} not deleted (or not verifiable): {e}", branches[i]));
            }
        }

        if let (Some((repo, env)), Some(before)) = (&gh_repo, labels_before) {
            match (before, gh_labels(repo, env)) {
                (Ok(before), Ok(after)) => {
                    for name in WATCHED_LABELS {
                        let created = after.iter().any(|l| l == name) && !before.iter().any(|l| l == name);
                        if created {
                            let del = check(
                                run(
                                    &Cmd::tool("gh", &["label", "delete", name, "--repo", repo, "--yes"], Path::new("."))
                                        .envs(env),
                                    true,
                                    TOOL_TIMEOUT,
                                ),
                                "gh label delete",
                            );
                            if let Err(e) = del {
                                self.leftovers.push(format!("{p}: label '{name}' created by the run, not deleted: {e}"));
                            }
                        }
                    }
                }
                (Err(e), _) | (_, Err(e)) => self.leftovers.push(format!(
                    "{p}: could not compare repo labels ({e}); check whether the run created {}",
                    WATCHED_LABELS.join(", ")
                )),
            }
        }
        if src.kind == Kind::Azure {
            eprintln!(">> azure: note: tag definitions the live run used stay in the project (ADO keeps them)");
        }
    }
}

fn gh_labels(repo: &str, env: &[(String, String)]) -> Result<Vec<String>, String> {
    let out = check(
        run(
            &Cmd::tool("gh", &["label", "list", "--repo", repo, "--limit", "1000", "--json", "name"], Path::new("."))
                .envs(env),
            true,
            TOOL_TIMEOUT,
        ),
        "gh label list",
    )?;
    let names = parse_label_names(&out)?;
    // A full page may be truncated: a pre-existing label past the cut would look created
    // by the run and get deleted. Refuse to compare instead.
    if names.len() >= 1000 {
        return Err("label list may be truncated at 1000; not comparing".into());
    }
    Ok(names)
}

/// Delete `branch` on origin if it is still there. Azure tries the az Bearer first and
/// falls back to the stored credential, like `ship push`.
fn delete_remote_branch(dir: &Path, branch: &str, bearer: Option<&[(String, String)]>) -> Result<(), String> {
    let refname = format!("refs/heads/{branch}");
    let attempts: Vec<&[(String, String)]> = bearer.into_iter().chain(std::iter::once(&[][..])).collect();
    let mut last = String::from("no attempt");
    for auth in attempts {
        match git_env(dir, &["ls-remote", "--heads", "origin", &refname], auth) {
            Ok(out) if out.is_empty() => return Ok(()),
            Ok(_) => {}
            Err(e) => {
                last = e;
                continue;
            }
        }
        match git_env(dir, &["push", "--quiet", "--delete", "origin", &refname], auth) {
            Ok(_) => return Ok(()),
            Err(e) => last = e,
        }
    }
    Err(last)
}

fn print_diff(c: &CaseResult) {
    println!("DIFF {} / {}: {}", c.platform, c.label, c.verdict.label());
    for (side, o) in [("ts", &c.ts), ("rs", &c.rs)] {
        match o {
            Some(o) => {
                println!("  {side} (exit {}):", exit_text(o.exit));
                for (k, v) in normalize(&o.kv) {
                    println!("    {k}={v}");
                }
            }
            None => println!("  {side}: no outcome"),
        }
    }
}

fn host_label() -> String {
    let wsl = env::var_os("WSL_DISTRO_NAME").is_some();
    format!(
        "{} {}{}",
        env::consts::OS,
        env::consts::ARCH,
        if wsl { " (WSL2)" } else { "" }
    )
}

fn execute(o: &Opts, inputs: &Inputs) -> Result<bool, String> {
    check_fresh(&inputs.impls.ship)?;
    let before = inputs
        .sources
        .iter()
        .map(|s| fingerprint(&s.path))
        .collect::<Result<Vec<_>, _>>()?;

    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    let nonce = nonce_from(now.as_nanos() ^ (u128::from(std::process::id()) << 64));
    let mut root = ScratchRoot::create(&nonce)?;
    let mut h = Harness {
        impls: &inputs.impls,
        nonce,
        cases: Vec::new(),
        timings: Vec::new(),
        leftovers: Vec::new(),
    };
    if let Err(e) = h.run_all(o, inputs, &root.path) {
        eprintln!("parity: run aborted: {e}");
        h.cases.push(CaseResult::not_run("harness", "setup", Verdict::Error("run aborted (see console)".into())));
    }
    let scratch_removed = root.remove();

    let mut sources_unchanged = true;
    for (src, before) in inputs.sources.iter().zip(&before) {
        match fingerprint(&src.path) {
            Ok(after) if after == *before => {}
            Ok(_) => {
                sources_unchanged = false;
                eprintln!(
                    "parity: {} source clone changed during the run (status, branches, tags or config; \
                     concurrent work in that repo also shows here)",
                    src.name
                );
            }
            Err(e) => {
                sources_unchanged = false;
                eprintln!("parity: cannot re-read the {} source clone: {e}", src.name);
            }
        }
    }
    for l in &h.leftovers {
        println!("LEFTOVER {l}");
    }

    let meta = Meta {
        generated: utc_stamp(now.as_secs()),
        host: host_label(),
        runs: o.runs,
        live: o.live,
        bun_version: inputs.bun_version.clone(),
        ship_version: inputs.ship_version.clone(),
        sources_unchanged,
        scratch_removed,
        leftovers: h.leftovers.len(),
    };
    let report = render_report(&h.cases, &h.timings, &meta);
    println!("\n{report}");
    if let Some(path) = &o.report {
        fs::write(path, &report).map_err(|e| format!("cannot write report {}: {e}", path.display()))?;
        eprintln!(">> report written to {}", path.display());
    }
    Ok(overall_pass(&h.cases, &h.timings, &meta))
}

// ---------------------------------------------------------------------------------------
// Tests: pure logic only (no bun, network, clones or git), so they run in CI.
// ---------------------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn s(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    fn kv(pairs: &[(&str, &str)]) -> Kv {
        pairs.iter().map(|(k, v)| (k.to_string(), v.to_string())).collect()
    }

    fn outcome(exit: i32, pairs: &[(&str, &str)]) -> Outcome {
        Outcome { exit: Some(exit), kv: kv(pairs) }
    }

    fn cmp(ts: &Outcome, rs: &Outcome) -> Verdict {
        compare(ts, rs)
    }

    #[test]
    fn tag_list_label_lines_are_compared() {
        let ts = Outcome { exit: Some(0), kv: parse_with_bare_lines("platform=github\nbug\nwip\n") };
        let same = Outcome { exit: Some(0), kv: parse_with_bare_lines("platform=github\nbug\nwip\n") };
        let missing = Outcome { exit: Some(0), kv: parse_with_bare_lines("platform=github\nbug\n") };
        assert_eq!(cmp(&ts, &same), Verdict::Same);
        assert!(cmp(&ts, &missing).is_failure());
        // Plain kv parsing would have hidden the missing label.
        assert_eq!(parse_kv("platform=github\nbug\n"), parse_kv("platform=github\nbug\nwip\n"));
        // Only `tag ... --list` cases opt in.
        assert!(CaseSpec::same("github", "x", "tag", &["--list", "35"]).bare_lines);
        assert!(!CaseSpec::same("github", "x", "tag", &[]).bare_lines);
        assert!(!CaseSpec::same("github", "x", "open", &["--list-profiles"]).bare_lines);
    }

    #[test]
    fn live_leftovers_fail_the_run() {
        let timings = [row("detect", 280.0, 9.0)];
        let mut meta = clean_meta();
        assert!(overall_pass(&[case(Verdict::Same)], &timings, &meta));
        meta.leftovers = 1;
        assert!(!overall_pass(&[case(Verdict::Same)], &timings, &meta));
    }

    fn case(verdict: Verdict) -> CaseResult {
        CaseResult {
            platform: "github",
            label: "detect".into(),
            ts: Some(outcome(0, &[("platform", "github")])),
            rs: Some(outcome(0, &[("platform", "github")])),
            verdict,
        }
    }

    fn row(sub: &'static str, ts: f64, rs: f64) -> TimingRow {
        TimingRow {
            subcommand: sub,
            measured: "real run",
            ts_ms: ts,
            rs_ms: rs,
            check: timing_check(sub, ts, rs, 0, true),
        }
    }

    fn clean_meta() -> Meta {
        Meta {
            sources_unchanged: true,
            scratch_removed: true,
            runs: 15,
            ..Meta::default()
        }
    }

    #[test]
    fn only_lowercase_key_lines_are_compared() {
        let stdout = "platform=github\nUsage: ship\nKey=x\n  indented=x\nlabel-name\n=v\n\
                      profile=Default\ta@b.c\tWork\nwork_item=4242\n";
        assert_eq!(
            parse_kv(stdout),
            kv(&[("platform", "github"), ("profile", "Default\ta@b.c\tWork"), ("work_item", "4242")])
        );
        assert!(is_kv_line("scope_clean=false"));
        assert!(is_kv_line("pushed="));
        assert!(!is_kv_line("tag-added=x"));
        assert!(!is_kv_line("no equals"));
    }

    // Matrix row "All same, fast".
    #[test]
    fn all_same_and_fast_passes() {
        let c = cmp(&outcome(0, &[("branch", "x"), ("scope_clean", "true")]), &outcome(0, &[("branch", "x"), ("scope_clean", "true")]));
        assert_eq!(c, Verdict::Same);
        let timings = [row("detect", 280.0, 9.0), row("pr", 400.0, 3.0)];
        assert!(timings.iter().all(|t| t.check.pass));
        assert!(overall_pass(&[case(c)], &timings, &clean_meta()));
    }

    // Matrix row "Key differs".
    #[test]
    fn a_differing_value_is_a_diff_and_fails_the_run() {
        let v = cmp(&outcome(0, &[("scope_clean", "true")]), &outcome(0, &[("scope_clean", "false")]));
        assert_eq!(v, Verdict::Diff { exit: None, output: true });
        assert_eq!(v.label(), "DIFF (key=value lines)");
        assert!(!overall_pass(&[case(v)], &[row("detect", 280.0, 9.0)], &clean_meta()));
        // A missing or extra key is a difference too.
        let extra = cmp(&outcome(0, &[("a", "1")]), &outcome(0, &[("a", "1"), ("b", "2")]));
        assert!(extra.is_failure());
        // Order matters: the scripts' line order is part of the contract.
        let swapped = cmp(&outcome(0, &[("a", "1"), ("b", "2")]), &outcome(0, &[("b", "2"), ("a", "1")]));
        assert!(swapped.is_failure());
    }

    // Matrix row "Exit differs".
    #[test]
    fn a_differing_exit_code_is_labelled() {
        let v = cmp(&outcome(1, &[]), &outcome(2, &[]));
        assert_eq!(v.label(), "DIFF (exit 1 vs 2)");
        let both = cmp(&outcome(1, &[("a", "1")]), &Outcome { exit: None, kv: kv(&[("a", "2")]) });
        assert_eq!(both.label(), "DIFF (exit 1 vs signal; key=value lines)");
    }

    // Matrix row "Volatile ids".
    #[test]
    fn volatile_ids_are_normalized_but_other_digits_are_not() {
        let ts = outcome(0, &[("pr_number", "41"), ("pr_url", "https://github.com/o/r/pull/41"), ("tag_added", "chore")]);
        let rs = outcome(0, &[("pr_number", "42"), ("pr_url", "https://github.com/o/r/pull/42"), ("tag_added", "chore")]);
        assert_eq!(cmp(&ts, &rs), Verdict::Same);
        let az_ts = outcome(0, &[("pr_id", "1931"), ("work_item", "77")]);
        let az_rs = outcome(0, &[("pr_id", "1932"), ("work_item", "78")]);
        assert_eq!(cmp(&az_ts, &az_rs), Verdict::Same);
        let ahead = cmp(&outcome(0, &[("commits_ahead_of_upstream", "1")]), &outcome(0, &[("commits_ahead_of_upstream", "2")]));
        assert!(ahead.is_failure());
        // The URL around the id still has to match.
        let other_repo = outcome(0, &[("pr_url", "https://github.com/o/x/pull/42")]);
        assert!(cmp(&outcome(0, &[("pr_url", "https://github.com/o/r/pull/41")]), &other_repo).is_failure());
    }

    #[test]
    fn mask_digits_collapses_each_run() {
        assert_eq!(mask_digits("a12b3"), "a<N>b<N>");
        assert_eq!(mask_digits("no digits"), "no digits");
        assert_eq!(mask_digits("4242"), "<N>");
    }

    // Matrix row "Slow binary".
    #[test]
    fn a_slow_binary_fails_its_timing_row() {
        assert!(!timing_check("push", 200.0, 200.0, 0, true).pass);
        assert!(!timing_check("push", 200.0, 250.0, 0, true).pass);
        let slow = timing_check("detect", 300.0, 50.0, 0, true);
        assert!(!slow.pass);
        assert!(slow.note.contains("50 ms"));
        assert!(timing_check("preflight", 300.0, 49.9, 0, true).pass);
        // Only detect/preflight carry the absolute limit.
        assert!(timing_check("pr", 300.0, 120.0, 0, true).pass);
        // Off Linux the 50 ms rule is skipped and noted, the relative rule still holds.
        let mac = timing_check("detect", 300.0, 80.0, 0, false);
        assert!(mac.pass);
        assert!(mac.note.contains("skipped"));
        assert!(!timing_check("detect", 30.0, 80.0, 0, false).pass);
        // A failed run fails the row even when the medians look fine.
        assert!(!timing_check("detect", 300.0, 5.0, 1, true).pass);
        assert!(!timing_check("detect", f64::NAN, f64::NAN, 0, true).pass);
        let timings = [row("detect", 280.0, 9.0), row("open", 100.0, 120.0)];
        assert!(!overall_pass(&[case(Verdict::Same)], &timings, &clean_meta()));
    }

    #[test]
    fn median_handles_odd_even_and_empty() {
        assert_eq!(median_ms(&[3.0, 1.0, 2.0]), 2.0);
        assert_eq!(median_ms(&[4.0, 1.0, 3.0, 2.0]), 2.5);
        assert_eq!(median_ms(&[7.0]), 7.0);
        assert!(median_ms(&[]).is_nan());
    }

    // Matrix row "Missing input".
    #[test]
    fn missing_inputs_are_usage_errors() {
        let e = parse_args(&s(&["--github", "g"])).unwrap_err();
        assert!(e.contains("--azure"), "{e}");
        let e = parse_args(&s(&["--azure", "a"])).unwrap_err();
        assert!(e.contains("--github"), "{e}");
        assert!(parse_args(&s(&["--azure"])).unwrap_err().contains("requires a value"));
        assert!(parse_args(&s(&["--azure", "a", "--github", "g", "--runs", "0"])).is_err());
        assert!(parse_args(&s(&["--azure", "a", "--github", "g", "--github-pr", "35x"])).is_err());
        assert!(parse_args(&s(&["--azure", "a", "--github", "g", "--bogus"])).is_err());
        let gone = env::temp_dir().join("ship-parity-test-does-not-exist-qzx");
        assert!(missing_path_error("--azure", &gone).unwrap().contains("not found"));
        assert!(missing_path_error("--azure", &env::temp_dir()).is_none());
    }

    #[test]
    fn full_flag_set_parses() {
        let argv = s(&[
            "--azure", "a", "--github", "g", "--azure-pr", "7", "--github-pr", "35", "--open-profile", "me@x.y",
            "--runs", "3", "--report", "r.md", "--live", "--ship", "bin/ship", "--scripts", "ts",
        ]);
        let Parsed::Run(o) = parse_args(&argv).unwrap() else { panic!("expected Run") };
        assert_eq!(o.azure, PathBuf::from("a"));
        assert_eq!(o.github_pr.as_deref(), Some("35"));
        assert_eq!(o.azure_pr.as_deref(), Some("7"));
        assert_eq!(o.open_profile.as_deref(), Some("me@x.y"));
        assert_eq!(o.runs, 3);
        assert!(o.live);
        assert_eq!(o.ship, PathBuf::from("bin/ship"));
        assert_eq!(o.scripts, PathBuf::from("ts"));
        assert_eq!(o.report, Some(PathBuf::from("r.md")));
        let Parsed::Run(d) = parse_args(&s(&["--azure", "a", "--github", "g"])).unwrap() else { panic!() };
        assert_eq!(d.runs, DEFAULT_RUNS);
        assert_eq!(d.ship, PathBuf::from("target/release/ship"));
        assert_eq!(d.scripts, PathBuf::from("scripts"));
        assert!(!d.live);
        assert_eq!(parse_args(&s(&["--azure", "a", "-h"])).unwrap(), Parsed::Help);
    }

    // Matrix row "Optional live read".
    #[test]
    fn a_skipped_case_is_neither_pass_nor_failure() {
        let skipped = CaseResult::not_run("azure", "tag --list <id> (live read)", Verdict::Skipped("no --azure-pr".into()));
        assert!(!skipped.verdict.is_failure());
        let cases = [case(Verdict::Same), skipped];
        let c = counts(&cases, &[]);
        assert_eq!((c.same, c.skipped, c.diff, c.error), (1, 1, 0, 0));
        assert!(overall_pass(&cases, &[row("detect", 280.0, 9.0)], &clean_meta()));
        let report = render_report(&cases, &[], &clean_meta());
        assert!(report.contains("| azure | `tag --list <id> (live read)` | — | — | skipped: no --azure-pr |"));
    }

    #[test]
    fn errors_and_hygiene_failures_fail_the_run() {
        let timings = [row("detect", 280.0, 9.0)];
        assert!(!overall_pass(&[case(Verdict::Error("timed out".into()))], &timings, &clean_meta()));
        let dirty = Meta { sources_unchanged: false, ..clean_meta() };
        assert!(!overall_pass(&[case(Verdict::Same)], &timings, &dirty));
        let kept = Meta { scratch_removed: false, ..clean_meta() };
        assert!(!overall_pass(&[case(Verdict::Same)], &timings, &kept));
        assert!(!overall_pass(&[case(Verdict::Same)], &[], &clean_meta()));
    }

    #[test]
    fn report_has_both_tables_and_no_stdout_values() {
        let secret = CaseResult {
            platform: "azure",
            label: "detect".into(),
            ts: Some(outcome(0, &[("org_url", "https://dev.azure.com/acme"), ("project", "secret-proj")])),
            rs: Some(outcome(0, &[("org_url", "https://dev.azure.com/acme"), ("project", "other-proj")])),
            verdict: Verdict::Diff { exit: None, output: true },
        };
        let report = render_report(&[secret], &[row("detect", 280.0, 9.0)], &clean_meta());
        assert!(report.contains("| Platform | Case | TS exit | RS exit | Verdict |"));
        assert!(report.contains("| Subcommand | Measured | TS median | RS median | Verdict | Note |"));
        assert!(report.contains("| azure | `detect` | 0 | 0 | DIFF (key=value lines) |"));
        assert!(report.contains("| detect | real run | 280.0 | 9.0 | pass | under 50 ms |"));
        assert!(report.contains("**FAIL**"));
        for value in ["acme", "secret-proj", "other-proj", "dev.azure.com"] {
            assert!(!report.contains(value), "report leaked {value}");
        }
    }

    #[test]
    fn nonce_is_letters_only_and_names_no_work_item() {
        for seed in [0u128, 1, 4242, u128::MAX, 1_762_950_000_123_456_789] {
            let n = nonce_from(seed);
            assert_eq!(n.len(), 10);
            assert!(n.bytes().all(|b| b.is_ascii_lowercase()), "{n}");
            assert_eq!(ship::parse_work_item(&format!("ship-parity-{n}-ts")), "");
        }
        assert_ne!(nonce_from(1), nonce_from(2));
    }

    #[test]
    fn utc_stamp_matches_known_instants() {
        assert_eq!(utc_stamp(0), "1970-01-01 00:00 UTC");
        assert_eq!(utc_stamp(1_700_000_000), "2023-11-14 22:13 UTC");
        assert_eq!(utc_stamp(951_782_400), "2000-02-29 00:00 UTC");
        assert_eq!(utc_stamp(1_798_761_600), "2027-01-01 00:00 UTC");
    }

    #[test]
    fn label_names_parse_and_reject_bad_shapes() {
        assert_eq!(parse_label_names(r#"[{"name":"chore"},{"name":"ship-parity"}]"#).unwrap(), s(&["chore", "ship-parity"]));
        assert_eq!(parse_label_names("[]").unwrap(), Vec::<String>::new());
        assert!(parse_label_names(r#"{"name":"x"}"#).is_err());
        assert!(parse_label_names(r#"[{"id":1}]"#).is_err());
        assert!(parse_label_names("not json").is_err());
    }
}
