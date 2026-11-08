//! GitHub REST calls for `ship pr`: token lookup, create PR, labels, reviewers.
//! Blocking `ureq`, JSON via `serde_json`. The token only ever goes into an
//! `Authorization` header on the configured API host; redirects are never followed.

use serde_json::{Value, json};
use std::process::{Command, Stdio};
use std::time::Duration;

const DEFAULT_API: &str = "https://api.github.com";
const API_VERSION: &str = "2022-11-28";

/// Run `gh` with an argument array; trimmed stdout, empty on any failure.
fn gh(args: &[&str]) -> String {
    Command::new("gh")
        .args(args)
        .stdin(Stdio::null())
        .stderr(Stdio::null())
        .output()
        .ok()
        .filter(|o| o.status.success())
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

/// Token for a repo, preferring the account that owns it: `GH_TOKEN`, then
/// `GITHUB_TOKEN`, then `gh auth token -u <owner>`, then the active `gh` account.
/// Empty when none is found.
pub fn token(owner: &str) -> String {
    for var in ["GH_TOKEN", "GITHUB_TOKEN"] {
        if let Ok(v) = std::env::var(var)
            && !v.is_empty()
        {
            return v;
        }
    }
    if !owner.is_empty() {
        let owned = gh(&["auth", "token", "-u", owner]);
        if !owned.is_empty() {
            return owned;
        }
    }
    gh(&["auth", "token"])
}

/// A created pull request.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Created {
    pub html_url: String,
    pub number: u64,
}

/// JSON body for `POST /repos/{o}/{r}/pulls`; `body` is omitted when empty.
pub fn create_payload(title: &str, head: &str, base: &str, draft: bool, body: &str) -> Value {
    let mut v = json!({ "title": title, "head": head, "base": base, "draft": draft });
    if !body.is_empty() {
        v["body"] = Value::String(body.to_string());
    }
    v
}

pub struct Client {
    agent: ureq::Agent,
    base: String,
    token: String,
    owner: String,
    repo: String,
}

impl Client {
    /// Errors when the base URL would send the token in cleartext: only `https://`, or
    /// `http://` on a loopback host (the test seam), is accepted.
    pub fn new(token: String, owner: &str, repo: &str) -> Result<Self, String> {
        let base = std::env::var("SHIP_GITHUB_API_URL")
            .ok()
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| DEFAULT_API.to_string());
        check_base(&base)?;
        let agent: ureq::Agent = ureq::Agent::config_builder()
            .http_status_as_error(false)
            .max_redirects(0)
            .timeout_global(Some(Duration::from_secs(60)))
            .tls_config(
                ureq::tls::TlsConfig::builder()
                    .root_certs(ureq::tls::RootCerts::PlatformVerifier)
                    .build(),
            )
            .build()
            .into();
        Ok(Client {
            agent,
            base: base.trim_end_matches('/').to_string(),
            token,
            owner: owner.to_string(),
            repo: repo.to_string(),
        })
    }

    fn repo_url(&self, tail: &str) -> String {
        format!("{}/repos/{}/{}/{tail}", self.base, enc(&self.owner), enc(&self.repo))
    }

    /// POST `payload`; `Ok(parsed body)` on 2xx, else `Err("HTTP <status>: <message>")`.
    /// Error text is built from the response status, message and `errors[]` details, never the token.
    fn post(&self, url: &str, payload: &Value) -> Result<Value, String> {
        let body = payload.to_string();
        let mut resp = self
            .agent
            .post(url)
            .header("Authorization", format!("Bearer {}", self.token))
            .header("Accept", "application/vnd.github+json")
            .header("X-GitHub-Api-Version", API_VERSION)
            .header("User-Agent", concat!("ship/", env!("CARGO_PKG_VERSION")))
            .content_type("application/json")
            .send(body.as_bytes())
            .map_err(|e| format!("request failed: {e}"))?;
        let status = resp.status().as_u16();
        let text = resp.body_mut().read_to_string().unwrap_or_default();
        let parsed: Value = serde_json::from_str(&text).unwrap_or(Value::Null);
        if (200..300).contains(&status) {
            return Ok(parsed);
        }
        let msg = parsed.get("message").and_then(Value::as_str).map(str::to_string);
        let mut out = format!("HTTP {status}");
        if let Some(m) = msg {
            out.push_str(": ");
            out.push_str(&m);
        }
        if let Some(errs) = parsed.get("errors").and_then(Value::as_array) {
            let detail: Vec<String> = errs
                .iter()
                .map(|e| e.as_str().map(str::to_string).or_else(|| e.get("message").and_then(Value::as_str).map(str::to_string)).unwrap_or_else(|| e.to_string()))
                .collect();
            if !detail.is_empty() {
                out.push_str(&format!(" ({})", detail.join("; ")));
            }
        }
        Err(out)
    }

    pub fn create_pr(&self, payload: &Value) -> Result<Created, String> {
        let v = self.post(&self.repo_url("pulls"), payload)?;
        let html_url = v.get("html_url").and_then(Value::as_str);
        let number = v.get("number").and_then(Value::as_u64);
        match (html_url, number) {
            (Some(u), Some(n)) => Ok(Created { html_url: u.to_string(), number: n }),
            _ => Err("unexpected response creating the pull request".to_string()),
        }
    }

    /// A PR is an issue on GitHub, so labels go through the issues API; a label that
    /// does not exist on the repo is created by GitHub.
    pub fn add_labels(&self, number: u64, labels: &[String]) -> Result<(), String> {
        self.post(&self.repo_url(&format!("issues/{number}/labels")), &json!({ "labels": labels }))
            .map(|_| ())
    }

    pub fn request_reviewers(&self, number: u64, reviewers: &[String]) -> Result<(), String> {
        self.post(
            &self.repo_url(&format!("pulls/{number}/requested_reviewers")),
            &json!({ "reviewers": reviewers }),
        )
        .map(|_| ())
    }
}

/// Refuse a base URL that would put the token on the wire unencrypted.
fn check_base(base: &str) -> Result<(), String> {
    if base.starts_with("https://") {
        return Ok(());
    }
    if let Some(rest) = base.strip_prefix("http://") {
        let authority = rest.split(['/', '?', '#']).next().unwrap_or("");
        let host_port = authority.rsplit('@').next().unwrap_or("");
        let host = if let Some(v6) = host_port.strip_prefix('[') {
            v6.split(']').next().unwrap_or("")
        } else {
            host_port.split(':').next().unwrap_or("")
        };
        if matches!(host, "127.0.0.1" | "::1" | "localhost") {
            return Ok(());
        }
    }
    Err(format!(
        "refusing SHIP_GITHUB_API_URL '{base}': the token is only sent over https:// (or http:// to localhost)"
    ))
}

/// Percent-encode one URL path segment (owner and repo come from a remote URL).
fn enc(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for b in s.bytes() {
        if b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b'~') {
            out.push(b as char);
        } else {
            out.push_str(&format!("%{b:02X}"));
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn payload_omits_empty_body_and_keeps_literals() {
        let p = create_payload("a & b", "feat/x", "main", true, "");
        assert_eq!(p, json!({"title": "a & b", "head": "feat/x", "base": "main", "draft": true}));
        let p = create_payload("t", "h", "b", false, "line1\n& more");
        assert_eq!(p["body"], "line1\n& more");
        assert_eq!(p["draft"], false);
    }

    #[test]
    fn base_url_must_be_https_or_loopback() {
        for ok in ["https://api.github.com", "http://127.0.0.1:8080", "http://localhost", "http://[::1]:9/x"] {
            assert!(check_base(ok).is_ok(), "{ok}");
        }
        for bad in ["http://example.com", "http://127.0.0.1@evil.com", "ftp://x", "api.github.com", "http://localhost.evil.com"] {
            assert!(check_base(bad).is_err(), "{bad}");
        }
    }

    #[test]
    fn path_segments_are_encoded() {
        assert_eq!(enc("my repo"), "my%20repo");
        assert_eq!(enc(".dotfiles"), ".dotfiles");
    }
}
