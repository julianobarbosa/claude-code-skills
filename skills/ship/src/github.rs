//! GitHub REST calls for `ship pr`: token lookup, create PR, labels, reviewers.
//! Blocking `ureq`, JSON via `serde_json`. The token only ever goes into an
//! `Authorization` header on the configured API host; redirects are never followed.

use serde_json::{Value, json};
use std::process::{Command, Stdio};
use crate::http;

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

/// The verb of a call; only `Post` carries a body.
#[derive(Debug, Clone, Copy)]
enum Method {
    Get,
    Post,
    Delete,
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
        http::check_base("SHIP_GITHUB_API_URL", &base)?;
        Ok(Client {
            agent: http::agent(),
            base: base.trim_end_matches('/').to_string(),
            token,
            owner: owner.to_string(),
            repo: repo.to_string(),
        })
    }

    fn repo_url(&self, tail: &str) -> String {
        format!("{}/repos/{}/{}/{tail}", self.base, http::enc(&self.owner), http::enc(&self.repo))
    }

    fn post(&self, url: &str, payload: &Value) -> Result<Value, String> {
        self.send(Method::Post, url, Some(payload))
    }

    /// One request; `Ok(parsed body)` on 2xx, else `Err("HTTP <status>: <message>")`.
    /// `payload` only goes out on a `Post`. Error text is built from the response status,
    /// message and `errors[]` details, never the token.
    fn send(&self, method: Method, url: &str, payload: Option<&Value>) -> Result<Value, String> {
        let auth = format!("Bearer {}", self.token);
        let ua = concat!("ship/", env!("CARGO_PKG_VERSION"));
        let bodyless = |b: ureq::RequestBuilder<ureq::typestate::WithoutBody>| {
            b.header("Authorization", &auth)
                .header("Accept", "application/vnd.github+json")
                .header("X-GitHub-Api-Version", API_VERSION)
                .header("User-Agent", ua)
                .call()
        };
        let result = match method {
            Method::Get => bodyless(self.agent.get(url)),
            Method::Delete => bodyless(self.agent.delete(url)),
            Method::Post => self
                .agent
                .post(url)
                .header("Authorization", &auth)
                .header("Accept", "application/vnd.github+json")
                .header("X-GitHub-Api-Version", API_VERSION)
                .header("User-Agent", ua)
                .content_type("application/json")
                .send(payload.map_or_else(String::new, Value::to_string).as_bytes()),
        };
        let mut resp = result.map_err(|e| format!("request failed: {e}"))?;
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

    /// Remove label `name` from PR/issue `number`; a label the PR does not carry (404) is an error.
    pub fn remove_label(&self, number: u64, name: &str) -> Result<(), String> {
        let url = self.repo_url(&format!("issues/{number}/labels/{}", http::enc(name)));
        self.send(Method::Delete, &url, None).map(|_| ())
    }

    /// The label names on PR/issue `number`: the first page only, as the TS.
    pub fn list_labels(&self, number: u64) -> Result<Vec<String>, String> {
        let v = self.send(Method::Get, &self.repo_url(&format!("issues/{number}/labels")), None)?;
        let arr = v.as_array().ok_or_else(|| "unexpected response listing the labels".to_string())?;
        Ok(arr
            .iter()
            .filter_map(|l| l.get("name").and_then(Value::as_str))
            .map(str::to_string)
            .collect())
    }

    pub fn request_reviewers(&self, number: u64, reviewers: &[String]) -> Result<(), String> {
        self.post(
            &self.repo_url(&format!("pulls/{number}/requested_reviewers")),
            &json!({ "reviewers": reviewers }),
        )
        .map(|_| ())
    }
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
}
