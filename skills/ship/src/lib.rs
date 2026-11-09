//! Shared helpers for the `ship` binary. Pure functions live here so they can be
//! tested without git; subprocess work is in [`git`], command output in [`detect`]
//! and [`preflight`].

pub mod azure;
pub mod detect;
pub mod git;
pub mod github;
pub mod http;
pub mod pr;
pub mod preflight;
pub mod push;
pub mod snapshot;

use regex::Regex;
use std::sync::LazyLock;

/// Delivery platform for a remote.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Platform {
    Azure,
    Github,
    Unknown,
}

impl Platform {
    pub fn as_str(self) -> &'static str {
        match self {
            Platform::Azure => "azure",
            Platform::Github => "github",
            Platform::Unknown => "unknown",
        }
    }
}

/// Azure DevOps coordinates parsed from a remote URL.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdoParts {
    pub org_url: String,
    pub project: String,
    pub repo: String,
}

/// Classify a remote URL. `override_platform` is the value of `SHIP_PLATFORM`;
/// only `azure` and `github` are honored, anything else is ignored.
pub fn detect_kind(url: &str, override_platform: Option<&str>) -> Platform {
    match override_platform {
        Some("azure") => return Platform::Azure,
        Some("github") => return Platform::Github,
        _ => {}
    }
    if url.contains("dev.azure.com") || url.contains("visualstudio.com") {
        Platform::Azure
    } else if url.contains("github") {
        Platform::Github
    } else {
        Platform::Unknown
    }
}

fn hex_val(b: u8) -> Option<u8> {
    match b {
        b'0'..=b'9' => Some(b - b'0'),
        b'a'..=b'f' => Some(b - b'a' + 10),
        b'A'..=b'F' => Some(b - b'A' + 10),
        _ => None,
    }
}

/// Percent-decoder equivalent to `decodeURIComponent`, falling back to the raw
/// segment on any invalid sequence (bad `%` escape or non-UTF-8 result).
pub fn decode_segment(s: &str) -> String {
    let bytes = s.as_bytes();
    let mut out = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' {
            let hi = bytes.get(i + 1).copied().and_then(hex_val);
            let lo = bytes.get(i + 2).copied().and_then(hex_val);
            match (hi, lo) {
                (Some(h), Some(l)) => {
                    out.push(h * 16 + l);
                    i += 3;
                }
                _ => return s.to_string(),
            }
        } else {
            out.push(bytes[i]);
            i += 1;
        }
    }
    String::from_utf8(out).unwrap_or_else(|_| s.to_string())
}

static ADO_DEV: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"dev\.azure\.com[^:/\s]*[:/]+(?:v3/)?([^/]+)/([^/]+)/(?:_git/)?([^/]+)$").unwrap()
});
static ADO_VS: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"([^/@.]+)\.visualstudio\.com/([^/]+)/(?:_git/)?([^/]+)$").unwrap()
});
static WI_AB: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"[Aa][Bb]#?([0-9]{1,7})").unwrap());
static WI_DELIM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?:^|[/_-])([0-9]{2,7})(?:[/_-]|$)").unwrap());
static GH_OWNER_REPO: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)^(?:[a-z+]+://)?(?:[^@/]+@)?([^:/]*github[^:/]*)[:/]([^/]+)/([^/]+?)(?:\.git)?/?$")
        .unwrap()
});

fn ado_from_caps(caps: &regex::Captures<'_>) -> AdoParts {
    let repo = &caps[3];
    let repo = repo.strip_suffix(".git").unwrap_or(repo);
    AdoParts {
        org_url: format!("https://dev.azure.com/{}", &caps[1]),
        project: decode_segment(&caps[2]),
        repo: decode_segment(repo),
    }
}

/// Parse an Azure DevOps remote URL (HTTPS, SSH v3, legacy visualstudio.com).
/// `None` when the URL is not an Azure DevOps URL. project/repo are decoded.
pub fn ado_parts(url: &str) -> Option<AdoParts> {
    if let Some(c) = ADO_DEV.captures(url) {
        return Some(ado_from_caps(&c));
    }
    ADO_VS.captures(url).map(|c| ado_from_caps(&c))
}

/// Best-effort work-item id from a branch name or commit subject; `""` if none.
pub fn parse_work_item(s: &str) -> String {
    if let Some(c) = WI_AB.captures(s) {
        return c[1].to_string();
    }
    if let Some(c) = WI_DELIM.captures(s) {
        return c[1].to_string();
    }
    String::new()
}

/// owner/repo from a GitHub remote, including SSH host aliases containing "github".
pub fn github_owner_repo(url: &str) -> Option<(String, String)> {
    GH_OWNER_REPO
        .captures(url.trim())
        .map(|c| (c[2].to_string(), c[3].to_string()))
}

static CC_TITLE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)^\s*([a-z]+)(?:\(([^)]+)\))?!?:").unwrap());

/// Split CSV and repeated-flag values into clean, de-duplicated names, keeping
/// first-seen order. Blank entries are dropped so they never reach a label API.
pub fn parse_tags<S: AsRef<str>>(values: &[S]) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for v in values {
        for part in v.as_ref().split(',') {
            let name = part.trim();
            if !name.is_empty() && !out.iter().any(|o| o == name) {
                out.push(name.to_string());
            }
        }
    }
    out
}

/// Default PR tags from a Conventional-Commit title: `docs(finops): x` gives
/// `docs`, `finops`; `fix: x` gives `fix`; anything else gives `needs-review`.
pub fn default_tags_from_title(title: &str) -> Vec<String> {
    let Some(c) = CC_TITLE.captures(title) else {
        return vec!["needs-review".to_string()];
    };
    let kind = c[1].to_lowercase();
    match c.get(2).map(|m| m.as_str().trim().to_lowercase()) {
        Some(scope) => parse_tags(&[format!("{kind},{scope}")]),
        None => parse_tags(&[kind]),
    }
}

/// Tag for a branch prefix (`fix/y` has prefix `fix`); `None` for an unmapped prefix.
pub fn tag_from_branch_prefix(prefix: &str) -> Option<&'static str> {
    Some(match prefix {
        "feat" | "feature" => "feat",
        "fix" | "hotfix" | "bugfix" => "fix",
        "docs" | "doc" => "docs",
        "chore" => "chore",
        "refactor" => "refactor",
        _ => return None,
    })
}

/// Work-item ids for `--related`: comma-separated and repeatable, deduped, in order.
/// Errors on anything that is not a positive integer (a leading `AB#` or `#` is stripped).
pub fn parse_related_ids<S: AsRef<str>>(values: &[S]) -> Result<Vec<u64>, String> {
    let mut out = Vec::new();
    for raw in values.iter().flat_map(|v| v.as_ref().split(',')) {
        let raw = raw.trim();
        // TS: `raw.trim().replace(/^(AB)?#/i, "")` - the `#` is required to strip anything.
        let after_ab = match raw.get(..2) {
            Some(p) if p.eq_ignore_ascii_case("ab") => &raw[2..],
            _ => raw,
        };
        let t = after_ab
            .strip_prefix('#')
            .or_else(|| raw.strip_prefix('#'))
            .unwrap_or(raw);
        if t.is_empty() {
            continue;
        }
        match t.parse::<u64>() {
            Ok(n) if !t.starts_with('0') && t.bytes().all(|b| b.is_ascii_digit()) => {
                if !out.contains(&n) {
                    out.push(n);
                }
            }
            _ => return Err(format!("--related: '{raw}' is not a work-item id")),
        }
    }
    Ok(out)
}

/// True when `text` mentions work item `id` the way Azure Repos turns into a link on a PR
/// description or a commit message: `#id` or `AB#id`, not as part of a longer number or word.
/// TS: `/(^|[^\w#])(AB)?#<id>(?!\d)/i`. Rust `regex` has no lookahead, so the trailing
/// non-digit is consumed instead (same truth value). The classes are ASCII, as JS `\w` and `\d`
/// are, and only `AB` folds case, so a non-ASCII letter before the `#` counts as a boundary.
pub fn mentions_work_item(text: &str, id: u64) -> bool {
    // `id` is a u64, so the pattern holds only digits from it and always compiles.
    Regex::new(&format!(r"(?:^|[^0-9A-Za-z_#])(?i:AB)?#{id}(?:[^0-9]|$)")).is_ok_and(|re| re.is_match(text))
}

/// Paths from `git status --porcelain`, split by what they need to be delivered.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct PorcelainStatus {
    pub staged: Vec<String>,
    pub unstaged: Vec<String>,
    pub untracked: Vec<String>,
}

/// Parse `git status --porcelain` (v1) output. Each line is `XY <path>`: X is the
/// index (staged) column, Y the worktree (unstaged) column. `??` is untracked,
/// `!!` ignored (skipped). A rename or copy line is `old -> new`; the new path is
/// recorded. A file changed in both columns shows in staged and unstaged.
/// The input must not be trimmed: a leading space is the Y-only column.
pub fn parse_porcelain_status(porcelain: &str) -> PorcelainStatus {
    let mut st = PorcelainStatus::default();
    for raw in porcelain.split('\n') {
        if raw.trim().is_empty() {
            continue;
        }
        let mut chars = raw.chars();
        let x = chars.next();
        let y = chars.next();
        let mut path = raw
            .char_indices()
            .nth(3)
            .map_or("", |(i, _)| &raw[i..]);
        if x == Some('?') && y == Some('?') {
            st.untracked.push(path.to_string());
            continue;
        }
        if x == Some('!') && y == Some('!') {
            continue; // ignored
        }
        // Rename/copy: "old -> new"; the new path is what changed.
        if let Some(arrow) = path.find(" -> ") {
            path = &path[arrow + 4..];
        }
        if x != Some(' ') && x != Some('?') {
            st.staged.push(path.to_string());
        }
        if y != Some(' ') && y != Some('?') {
            st.unstaged.push(path.to_string());
        }
    }
    st
}

/// Result of [`scope_audit`]. `ok` is false when anything is unstaged or untracked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScopeAudit {
    pub status: PorcelainStatus,
    pub ok: bool,
    /// One human-readable line naming the at-risk files; `None` when `ok`.
    /// The binary prints its own stderr lines (see [`preflight`]), not this.
    pub warning: Option<String>,
}

/// Audit the working tree for scope creep before a ship commit: the PR #192 miss,
/// a changed file left out of the PR because it was never staged.
pub fn scope_audit(porcelain: &str) -> ScopeAudit {
    let status = parse_porcelain_status(porcelain);
    let ok = status.unstaged.is_empty() && status.untracked.is_empty();
    let warning = (!ok).then(|| {
        let mut parts: Vec<String> = Vec::new();
        if !status.unstaged.is_empty() {
            parts.push(format!(
                "{} changed but not staged ({})",
                status.unstaged.len(),
                status.unstaged.join(", ")
            ));
        }
        if !status.untracked.is_empty() {
            parts.push(format!(
                "{} untracked ({})",
                status.untracked.len(),
                status.untracked.join(", ")
            ));
        }
        format!(
            "scope check: {} \u{2014} confirm these don't belong in this PR before committing",
            parts.join("; ")
        )
    });
    ScopeAudit { status, ok, warning }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parts(o: &str, p: &str, r: &str) -> Option<AdoParts> {
        Some(AdoParts {
            org_url: o.into(),
            project: p.into(),
            repo: r.into(),
        })
    }

    // parseWorkItem
    #[test]
    fn work_item_ab_hash() {
        assert_eq!(parse_work_item("AB#1234"), "1234");
    }
    #[test]
    fn work_item_branch() {
        assert_eq!(parse_work_item("feature/837-foo"), "837");
    }
    #[test]
    fn work_item_none() {
        assert_eq!(parse_work_item("main"), "");
    }

    // parseWorkItem quirks, pinned to the TS results
    #[test]
    fn work_item_ab_without_hash() {
        assert_eq!(parse_work_item("AB1234"), "1234");
    }
    #[test]
    fn work_item_single_digit_delimited_is_none() {
        assert_eq!(parse_work_item("feature/7-foo"), "");
    }
    #[test]
    fn work_item_ab_wins_over_delimited() {
        assert_eq!(parse_work_item("AB#5-x/123-y"), "5");
    }
    #[test]
    fn work_item_ab_matches_inside_a_word() {
        assert_eq!(parse_work_item("feature/tab12-fix"), "12");
    }
    #[test]
    fn work_item_ab_caps_at_seven_digits() {
        assert_eq!(parse_work_item("AB#12345678"), "1234567");
    }

    // detectKind
    #[test]
    fn kind_azure_https() {
        assert_eq!(detect_kind("https://dev.azure.com/org/proj/_git/repo", None), Platform::Azure);
    }
    #[test]
    fn kind_github_ssh() {
        assert_eq!(detect_kind("git@github.com:user/repo.git", None), Platform::Github);
    }
    #[test]
    fn kind_unknown() {
        assert_eq!(detect_kind("https://example.com/x.git", None), Platform::Unknown);
    }
    #[test]
    fn kind_empty_url_is_unknown() {
        assert_eq!(detect_kind("", None), Platform::Unknown);
    }
    #[test]
    fn kind_override() {
        let az = "https://dev.azure.com/org/proj/_git/repo";
        assert_eq!(detect_kind(az, Some("github")), Platform::Github);
        assert_eq!(detect_kind("", Some("azure")), Platform::Azure);
        assert_eq!(detect_kind(az, Some("bogus")), Platform::Azure);
        assert_eq!(detect_kind("https://example.com/x.git", Some("")), Platform::Unknown);
    }

    // adoParts
    #[test]
    fn ado_https() {
        assert_eq!(
            ado_parts("https://dev.azure.com/myorg/myproj/_git/myrepo"),
            parts("https://dev.azure.com/myorg", "myproj", "myrepo")
        );
    }
    #[test]
    fn ado_non_azure_is_none() {
        assert_eq!(ado_parts("git@github.com:user/repo.git"), None);
    }
    #[test]
    fn ado_ssh_v3() {
        assert_eq!(
            ado_parts("git@ssh.dev.azure.com:v3/org/proj/repo"),
            parts("https://dev.azure.com/org", "proj", "repo")
        );
    }
    #[test]
    fn ado_visualstudio_legacy() {
        assert_eq!(
            ado_parts("https://org.visualstudio.com/proj/_git/repo"),
            parts("https://dev.azure.com/org", "proj", "repo")
        );
    }
    #[test]
    fn ado_decodes_percent20_and_strips_git() {
        assert_eq!(
            ado_parts("https://dev.azure.com/myorg/my%20proj/_git/my%20repo.git"),
            parts("https://dev.azure.com/myorg", "my proj", "my repo")
        );
    }
    #[test]
    fn ado_invalid_percent_kept_raw() {
        assert_eq!(
            ado_parts("https://dev.azure.com/myorg/100%/_git/re%zzpo"),
            parts("https://dev.azure.com/myorg", "100%", "re%zzpo")
        );
    }
    #[test]
    fn decode_segment_edge_cases() {
        assert_eq!(decode_segment("a%20b"), "a b");
        assert_eq!(decode_segment("%C3%A9"), "é");
        assert_eq!(decode_segment("%"), "%");
        assert_eq!(decode_segment("%2"), "%2");
        assert_eq!(decode_segment("%FF"), "%FF"); // not valid UTF-8, kept raw
    }

    // githubOwnerRepo
    fn gh(o: &str, r: &str) -> Option<(String, String)> {
        Some((o.into(), r.into()))
    }
    #[test]
    fn gh_ssh() {
        assert_eq!(github_owner_repo("git@github.com:user/repo.git"), gh("user", "repo"));
    }
    #[test]
    fn gh_https_no_git() {
        assert_eq!(github_owner_repo("https://github.com/user/repo"), gh("user", "repo"));
    }
    #[test]
    fn gh_ssh_alias() {
        assert_eq!(
            github_owner_repo("git@github-julianomb:julianobarbosa/.dotfiles.git"),
            gh("julianobarbosa", ".dotfiles")
        );
    }
    #[test]
    fn gh_ssh_url_alias() {
        assert_eq!(
            github_owner_repo("ssh://git@github.com-work/org/svc.git"),
            gh("org", "svc")
        );
    }
    #[test]
    fn gh_non_github_is_none() {
        assert_eq!(github_owner_repo("https://dev.azure.com/org/proj/_git/repo"), None);
    }

    // parsePorcelainStatus
    fn v(items: &[&str]) -> Vec<String> {
        items.iter().map(|s| s.to_string()).collect()
    }
    #[test]
    fn porcelain_empty_tree() {
        assert_eq!(parse_porcelain_status(""), PorcelainStatus::default());
    }
    #[test]
    fn porcelain_staged_only() {
        let s = parse_porcelain_status("M  src/a.ts\nA  src/b.ts");
        assert_eq!(s.staged, v(&["src/a.ts", "src/b.ts"]));
        assert!(s.unstaged.is_empty());
        assert!(s.untracked.is_empty());
    }
    #[test]
    fn porcelain_unstaged_only() {
        let s = parse_porcelain_status(" M src/a.ts");
        assert!(s.staged.is_empty());
        assert_eq!(s.unstaged, v(&["src/a.ts"]));
    }
    #[test]
    fn porcelain_untracked() {
        let s = parse_porcelain_status("?? docs/index.md");
        assert_eq!(s.untracked, v(&["docs/index.md"]));
        assert!(s.staged.is_empty());
        assert!(s.unstaged.is_empty());
    }
    #[test]
    fn porcelain_ignored_entries_are_skipped() {
        assert_eq!(parse_porcelain_status("!! node_modules/"), PorcelainStatus::default());
    }
    #[test]
    fn porcelain_rename_records_new_path() {
        let s = parse_porcelain_status("R  old.ts -> new.ts");
        assert_eq!(s.staged, v(&["new.ts"]));
    }
    #[test]
    fn porcelain_modified_in_both_shows_in_both() {
        let s = parse_porcelain_status("MM src/a.ts");
        assert_eq!(s.staged, v(&["src/a.ts"]));
        assert_eq!(s.unstaged, v(&["src/a.ts"]));
    }
    #[test]
    fn porcelain_mixed_tree() {
        let s = parse_porcelain_status("M  staged.ts\n M unstaged.ts\n?? new.ts");
        assert_eq!(s.staged, v(&["staged.ts"]));
        assert_eq!(s.unstaged, v(&["unstaged.ts"]));
        assert_eq!(s.untracked, v(&["new.ts"]));
    }
    // Intended difference from TS: the first line keeps its leading space, so a lone
    // ` M b.txt` is unstaged (TS trims it to `M b.txt` and misreads it as staged).
    #[test]
    fn porcelain_unstaged_first_line_stays_unstaged() {
        let s = parse_porcelain_status(" M b.txt\n");
        assert!(s.staged.is_empty());
        assert_eq!(s.unstaged, v(&["b.txt"]));
    }

    // parseTags / defaultTagsFromTitle (ports of the ship-lib.test.ts groups)
    #[test]
    fn default_tags_type_and_scope() {
        assert_eq!(default_tags_from_title("docs(finops): OpenCost vs Infracost"), v(&["docs", "finops"]));
    }
    #[test]
    fn default_tags_type_only() {
        assert_eq!(default_tags_from_title("fix: handle null token"), v(&["fix"]));
    }
    #[test]
    fn default_tags_ignores_breaking_bang() {
        assert_eq!(default_tags_from_title("feat!: drop v1 API"), v(&["feat"]));
    }
    #[test]
    fn default_tags_fall_back_to_needs_review() {
        assert_eq!(default_tags_from_title("just some title"), v(&["needs-review"]));
    }
    #[test]
    fn default_tags_lowercase_and_dedupe() {
        assert_eq!(default_tags_from_title("FIX(Fix): x"), v(&["fix"]));
    }
    #[test]
    fn parse_tags_splits_trims_dedupes_drops_blanks() {
        assert_eq!(parse_tags(&["hotfix, do-not-merge", " hotfix ", ""]), v(&["hotfix", "do-not-merge"]));
    }
    #[test]
    fn branch_prefix_map() {
        assert_eq!(tag_from_branch_prefix("hotfix"), Some("fix"));
        assert_eq!(tag_from_branch_prefix("feature"), Some("feat"));
        assert_eq!(tag_from_branch_prefix("doc"), Some("docs"));
        assert_eq!(tag_from_branch_prefix("wip"), None);
    }
    #[test]
    fn related_ids_parse_and_reject() {
        assert_eq!(parse_related_ids(&["12, AB#34", "#12"]).unwrap(), vec![12, 34]);
        assert!(parse_related_ids(&["x"]).is_err());
        assert!(parse_related_ids(&["0"]).is_err());
        assert!(parse_related_ids(&["AB34"]).is_err());
        assert!(parse_related_ids(&["012"]).is_err());
        assert!(parse_related_ids(&["AB"]).is_err());
        assert_eq!(parse_related_ids(&["#", " , "]).unwrap(), Vec::<u64>::new());
        assert_eq!(parse_related_ids(&["ab#7"]).unwrap(), vec![7]);
    }
    // parseRelatedIds (ship-lib.test.ts)
    #[test]
    fn related_ids_csv_and_repeated_flags_deduped_with_prefixes() {
        assert_eq!(parse_related_ids(&["4242,1717", "AB#4242", " #77 "]).unwrap(), vec![4242, 1717, 77]);
        assert_eq!(parse_related_ids::<&str>(&[]).unwrap(), Vec::<u64>::new());
    }
    #[test]
    fn related_ids_non_numeric_errors_instead_of_becoming_a_link() {
        assert!(parse_related_ids(&["23a"]).unwrap_err().contains("is not a work-item id"));
        assert!(parse_related_ids(&["0"]).is_err());
    }

    // mentionsWorkItem (ship-lib.test.ts)
    #[test]
    fn mentions_hash_and_ab_hash() {
        assert!(mentions_work_item("pending (AB#4242): x", 4242));
        assert!(mentions_work_item("see #4242.", 4242));
        assert!(mentions_work_item("#4242", 4242));
    }
    #[test]
    fn mentions_not_a_longer_number_a_bare_number_or_a_word_attached_hash() {
        assert!(!mentions_work_item("#42420", 4242));
        assert!(!mentions_work_item("issue 4242", 4242));
        assert!(!mentions_work_item("x#4242", 4242));
    }
    #[test]
    fn mentions_edges_match_the_ts_regex() {
        // `i` flag: any case of AB.
        assert!(mentions_work_item("ab#7", 7));
        assert!(mentions_work_item("Ab#7 and more", 7));
        // Multi-line text (commit messages): a mention at a line start, and at the end.
        assert!(mentions_work_item("subject\n\nfixes #7", 7));
        assert!(mentions_work_item("subject\n#7\n", 7));
        // `_` is a word char; `#` before the hash is excluded; a longer id or a prefix is not it.
        assert!(!mentions_work_item("_#7", 7));
        assert!(!mentions_work_item("##7", 7));
        assert!(!mentions_work_item("#17", 7));
        assert!(!mentions_work_item("XAB#7", 7));
        assert!(!mentions_work_item("item 7", 7));
        assert!(!mentions_work_item("", 7));
        // JS `\w` is ASCII: a non-ASCII letter (even the Kelvin sign, which folds to `k`)
        // is a boundary, not part of a word.
        assert!(mentions_work_item("é#7", 7));
        assert!(mentions_work_item("\u{212A}#7", 7));
    }

    // scopeAudit
    #[test]
    fn audit_clean_when_only_staged() {
        let a = scope_audit("M  staged.ts");
        assert!(a.ok);
        assert_eq!(a.warning, None);
    }
    #[test]
    fn audit_clean_on_empty_tree() {
        assert!(scope_audit("").ok);
    }
    #[test]
    fn audit_not_ok_with_unstaged_warning_names_file() {
        let a = scope_audit(" M docs/index.md");
        assert!(!a.ok);
        let w = a.warning.unwrap();
        assert!(w.contains("docs/index.md"));
        assert!(w.contains("not staged"));
    }
    #[test]
    fn audit_not_ok_with_untracked_warning_names_file() {
        let a = scope_audit("?? new.ts");
        assert!(!a.ok);
        let w = a.warning.unwrap();
        assert!(w.contains("new.ts"));
        assert!(w.contains("untracked"));
    }
    #[test]
    fn audit_warning_covers_both_unstaged_and_untracked() {
        let a = scope_audit(" M a.ts\n?? b.ts");
        assert!(!a.ok);
        let w = a.warning.unwrap();
        assert!(w.contains("a.ts"));
        assert!(w.contains("b.ts"));
    }
    #[test]
    fn audit_warning_matches_ts_wording() {
        assert_eq!(
            scope_audit(" M a.ts\n?? b.ts").warning.unwrap(),
            "scope check: 1 changed but not staged (a.ts); 1 untracked (b.ts) \u{2014} confirm these don't belong in this PR before committing"
        );
    }
}
