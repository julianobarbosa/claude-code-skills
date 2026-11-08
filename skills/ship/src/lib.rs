//! Shared helpers for the `ship` binary. Pure functions live here so they can be
//! tested without git; subprocess work is in [`git`], command output in [`detect`].

pub mod detect;
pub mod git;

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
}
