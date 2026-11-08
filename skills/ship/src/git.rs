//! Git subprocess helpers. Always an argument array, never a shell.

use crate::Platform;
use std::io;
use std::process::{Command, Stdio};

/// Run `git` with `args`; stdout is returned untrimmed. stderr is inherited,
/// like the TS `execFileSync` default. A non-zero exit is an error.
fn run_raw(args: &[&str]) -> io::Result<String> {
    let out = Command::new("git")
        .args(args)
        .stdin(Stdio::null())
        .stderr(Stdio::inherit())
        .output()
        .map_err(|e| io::Error::new(e.kind(), format!("failed to run git: {e}")))?;
    if !out.status.success() {
        return Err(io::Error::other(format!(
            "Command failed: git {} ({})",
            args.join(" "),
            out.status
        )));
    }
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

/// Like [`run_raw`] but with stdout trimmed, as the TS `sh()` does.
fn run(args: &[&str]) -> io::Result<String> {
    run_raw(args).map(|s| s.trim().to_string())
}

/// Current checked-out branch name. Errors outside a repo.
pub fn current_branch() -> io::Result<String> {
    run(&["rev-parse", "--abbrev-ref", "HEAD"])
}

/// Fetch URL of a remote; empty string when the remote (or git itself) fails.
pub fn remote_url(remote: &str) -> String {
    run(&["remote", "get-url", remote]).unwrap_or_default()
}

/// `git log --oneline @{u}..`: one line per local commit not on the upstream.
/// Empty when there is no upstream (or git fails); git's own stderr still shows.
pub fn log_ahead_of_upstream() -> String {
    run(&["log", "--oneline", "@{u}.."]).unwrap_or_default()
}

/// `git status --porcelain`, deliberately untrimmed: trimming would eat the
/// leading space of a first ` M path` line and misread it as staged (the TS
/// `sh()` bug). Only trailing newlines are dropped. Empty when git fails.
/// `--untracked-files=normal` is explicit so a `status.showUntrackedFiles=no`
/// config cannot hide new files from the scope guard; on default config the
/// output is identical to plain `git status --porcelain`.
pub fn status_porcelain() -> String {
    run_raw(&["status", "--porcelain", "--untracked-files=normal"])
        .map(|s| s.trim_end_matches('\n').to_string())
        .unwrap_or_default()
}

/// Azure DevOps API resource id: the same constant for every org, not a secret.
const ADO_RESOURCE: &str = "499b84ac-1321-427f-aa17-267ca6975798";

/// Mint a short-lived Azure DevOps token from the logged-in `az` CLI. Empty when
/// `az` is missing, logged out or prints nothing, like the TS `tryAdoToken`.
/// `az`'s stderr is inherited, as in the TS `sh()`.
pub fn try_ado_token() -> String {
    Command::new("az")
        .args([
            "account", "get-access-token",
            "--resource", ADO_RESOURCE,
            "--query", "accessToken", "-o", "tsv",
        ])
        .stdin(Stdio::null())
        .stderr(Stdio::inherit())
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

/// Push URL of a remote (`git remote get-url --push`); empty when it fails, e.g.
/// when `remote` is itself a URL rather than a configured name.
fn push_url(remote: &str) -> String {
    run(&["remote", "get-url", "--push", remote]).unwrap_or_default()
}

/// Config key for the Bearer header. For an http(s) URL it is scoped to that
/// URL's origin (`http.<scheme>://<host>/.extraHeader`, git's URL-matched config),
/// so the token is not sent on redirects to other hosts or to other HTTP services
/// git talks to during the push. Other URLs (ssh, file, path) send no HTTP request
/// carrying it, so they keep the plain `http.extraHeader`.
pub fn extra_header_key(url: &str) -> String {
    for scheme in ["https://", "http://"] {
        if let Some(rest) = url.strip_prefix(scheme) {
            let authority = rest.split('/').next().unwrap_or("");
            let host = authority.rsplit('@').next().unwrap_or(authority);
            if !host.is_empty() {
                return format!("http.{scheme}{host}/.extraHeader");
            }
        }
    }
    "http.extraHeader".into()
}

/// The `GIT_CONFIG_*` environment that authenticates one git call with a Bearer
/// token: `credential.helper` emptied (a stale stored credential would otherwise
/// still answer git's 401 challenge) and the header set under `header_key`.
/// `GIT_TERMINAL_PROMPT=0` makes a rejected token fail instead of prompting for a
/// password, so the plain-push fallback can run. The token is kept out of argv,
/// `ps` args and disk; it is visible to the same user's process environment and
/// to hooks git runs. `existing_count` is the caller's own `GIT_CONFIG_COUNT`, so
/// its entries are kept and ours appended.
pub fn bearer_env(token: &str, header_key: &str, existing_count: usize) -> Vec<(String, String)> {
    let n = existing_count;
    vec![
        ("GIT_TERMINAL_PROMPT".into(), "0".into()),
        ("GIT_CONFIG_COUNT".into(), (n + 2).to_string()),
        (format!("GIT_CONFIG_KEY_{n}"), "credential.helper".into()),
        (format!("GIT_CONFIG_VALUE_{n}"), String::new()),
        (format!("GIT_CONFIG_KEY_{}", n + 1), header_key.into()),
        (format!("GIT_CONFIG_VALUE_{}", n + 1), format!("Authorization: Bearer {token}")),
    ]
}

/// Run `git args` with inherited stdio (push progress streams) and extra env.
/// True on a zero exit; a spawn failure counts as failure.
fn run_inherit(args: &[&str], envs: &[(String, String)]) -> bool {
    Command::new("git")
        .args(args)
        .envs(envs.iter().map(|(k, v)| (k, v)))
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// argv for the push, identical for the Bearer and plain attempts: no `-c`, no
/// force flag, no `+refspec`. Auth travels in the environment, not here. `--`
/// keeps a remote or ref that starts with `-` from being read as an option.
pub fn push_args(remote: &str, refs: &[&str]) -> Vec<String> {
    ["push", "-u", "--", remote]
        .into_iter()
        .chain(refs.iter().copied())
        .map(String::from)
        .collect()
}

/// How a push got through.
#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum PushMode {
    OauthBearer,
    Normal,
}

impl PushMode {
    pub fn as_str(self) -> &'static str {
        match self {
            PushMode::OauthBearer => "oauth-bearer",
            PushMode::Normal => "normal",
        }
    }
}

/// `git push -u` of `refs` to `remote` with the shared auth order: on Azure an
/// `az` Bearer push first, then the plain push (stored credential) as the one
/// fallback; GitHub and unknown go straight to the plain push. Never forces.
/// `None` when the final push fails. Reused by `snapshot --push`.
pub fn push_with_auth(kind: Platform, remote: &str, refs: &[&str]) -> Option<PushMode> {
    let args = push_args(remote, refs);
    let args: Vec<&str> = args.iter().map(String::as_str).collect();
    let args = args.as_slice();

    if kind == Platform::Azure {
        let token = try_ado_token();
        if !token.is_empty() {
            let base = std::env::var("GIT_CONFIG_COUNT")
                .ok()
                .and_then(|v| v.trim().parse::<usize>().ok())
                .unwrap_or(0);
            let url = Some(push_url(remote)).filter(|u| !u.is_empty()).unwrap_or_else(|| remote.to_string());
            if run_inherit(args, &bearer_env(&token, &extra_header_key(&url), base)) {
                return Some(PushMode::OauthBearer);
            }
        }
        eprintln!(
            "{}",
            if token.is_empty() {
                ">> could not mint an az token (is 'az login' done?); trying the stored git credential"
            } else {
                ">> OAuth Bearer push failed; trying the stored git credential"
            }
        );
    }

    run_inherit(args, &[]).then_some(PushMode::Normal)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bearer_env_sets_both_pairs_and_keeps_token_out_of_keys() {
        let env = bearer_env("SECRET", "http.extraHeader", 0);
        let get = |k: &str| env.iter().find(|(key, _)| key == k).map(|(_, v)| v.as_str());
        assert_eq!(get("GIT_TERMINAL_PROMPT"), Some("0"));
        assert_eq!(get("GIT_CONFIG_COUNT"), Some("2"));
        assert_eq!(get("GIT_CONFIG_KEY_0"), Some("credential.helper"));
        assert_eq!(get("GIT_CONFIG_VALUE_0"), Some(""));
        assert_eq!(get("GIT_CONFIG_KEY_1"), Some("http.extraHeader"));
        assert_eq!(get("GIT_CONFIG_VALUE_1"), Some("Authorization: Bearer SECRET"));
        assert!(env.iter().all(|(k, _)| !k.contains("SECRET")));
    }

    #[test]
    fn push_args_carry_no_config_override_and_no_force() {
        let args = push_args("origin", &["feat/x"]);
        assert_eq!(args, ["push", "-u", "--", "origin", "feat/x"]);
        assert!(args.iter().all(|a| a != "-c" && !a.contains("Bearer") && !a.starts_with('+') && !a.contains("force")));
    }

    #[test]
    fn header_key_is_scoped_to_the_origin_of_http_urls() {
        assert_eq!(
            extra_header_key("https://dev.azure.com/org/proj/_git/repo"),
            "http.https://dev.azure.com/.extraHeader" // check-no-identity-allow: config key, not an org
        );
        assert_eq!(
            extra_header_key("https://org@dev.azure.com:8443/org/proj/_git/repo"),
            "http.https://dev.azure.com:8443/.extraHeader"
        );
        assert_eq!(extra_header_key("http://host/x.git"), "http.http://host/.extraHeader");
    }

    #[test]
    fn header_key_is_unscoped_for_non_http_remotes() {
        assert_eq!(extra_header_key("/tmp/some/bare"), "http.extraHeader");
        assert_eq!(extra_header_key("git@ssh.dev.azure.com:v3/org/proj/repo"), "http.extraHeader");
        assert_eq!(extra_header_key(""), "http.extraHeader");
    }

    #[test]
    fn bearer_env_appends_after_existing_entries() {
        let env = bearer_env("T", "http.extraHeader", 3);
        assert!(env.contains(&("GIT_CONFIG_COUNT".into(), "5".into())));
        assert!(env.contains(&("GIT_CONFIG_KEY_3".into(), "credential.helper".into())));
        assert!(env.contains(&("GIT_CONFIG_KEY_4".into(), "http.extraHeader".into())));
    }
}
