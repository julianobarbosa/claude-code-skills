//! Azure DevOps REST calls for `ship pr`: credentials, the work-item read and the PR create.
//! Blocking `ureq`, JSON via `serde_json`. A credential only ever goes into an
//! `Authorization` header on the configured API host; redirects are never followed.

use crate::{git, http};
use serde_json::{Value, json};

const DEFAULT_ORIGIN: &str = "https://dev.azure.com";
const IDENTITY_ORIGIN: &str = "https://vssps.dev.azure.com";
const API_VERSION: &str = "7.1";

/// One way to authenticate, in the order they are tried.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Cred {
    /// The `az` OAuth token, sent as `Bearer`.
    Bearer(String),
    /// A personal access token, sent as `Basic base64(":" + pat)`.
    Pat(String),
}

impl Cred {
    /// The name the TS prints in its fallback line.
    pub fn kind(&self) -> &'static str {
        match self {
            Cred::Bearer(_) => "bearer",
            Cred::Pat(_) => "pat",
        }
    }

    fn header(&self) -> String {
        match self {
            Cred::Bearer(t) => format!("Bearer {t}"),
            Cred::Pat(p) => format!("Basic {}", base64(format!(":{p}").as_bytes())),
        }
    }
}

/// Credentials in the order to try them: the `az` token first (minted from whoever is
/// logged in now, so it cannot go stale), then `AZURE_DEVOPS_EXT_PAT`, else `AZURE_DEVOPS_PAT`.
pub fn credentials() -> Vec<Cred> {
    let mut creds = Vec::new();
    let token = git::try_ado_token();
    if !token.is_empty() {
        creds.push(Cred::Bearer(token));
    }
    let pat = ["AZURE_DEVOPS_EXT_PAT", "AZURE_DEVOPS_PAT"]
        .iter()
        .find_map(|v| std::env::var(v).ok().filter(|s| !s.is_empty()));
    if let Some(p) = pat {
        creds.push(Cred::Pat(p));
    }
    creds
}

/// A reviewer resolved to an identity id, with whether the review is required.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Reviewer {
    pub id: String,
    pub is_required: bool,
}

/// JSON body for the pull-request create call. `description`, `isDraft`, `labels` and
/// `reviewers` are left out when empty/false; `workItemRefs` is always present (empty when
/// nothing is linked).
#[allow(clippy::too_many_arguments)]
pub fn create_payload(
    source: &str,
    target: &str,
    title: &str,
    body: &str,
    draft: bool,
    work_items: &[u64],
    tags: &[String],
    reviewers: &[Reviewer],
) -> Value {
    let mut v = json!({
        "sourceRefName": format!("refs/heads/{source}"),
        "targetRefName": format!("refs/heads/{target}"),
        "title": title,
        "workItemRefs": work_items.iter().map(|id| json!({ "id": id.to_string() })).collect::<Vec<_>>(),
    });
    if !body.is_empty() {
        v["description"] = Value::String(body.to_string());
    }
    if draft {
        v["isDraft"] = Value::Bool(true);
    }
    if !tags.is_empty() {
        v["labels"] = tags.iter().map(|t| json!({ "name": t })).collect();
    }
    if !reviewers.is_empty() {
        v["reviewers"] = reviewers
            .iter()
            .map(|r| json!({ "id": r.id, "isRequired": r.is_required }))
            .collect();
    }
    v
}

/// Whether `s` is a bare identity GUID (`8-4-4-4-12` hex digits, any case).
fn is_guid(s: &str) -> bool {
    let groups: Vec<&str> = s.split('-').collect();
    groups.len() == 5
        && groups
            .iter()
            .zip([8, 4, 4, 4, 12])
            .all(|(g, n)| g.len() == n && g.bytes().all(|b| b.is_ascii_hexdigit()))
}

/// JSON-patch document for a work-item create: the title, plus the assignee when non-empty.
pub fn work_item_patch(title: &str, assignee: &str) -> Value {
    let mut ops = vec![json!({ "op": "add", "path": "/fields/System.Title", "value": title })];
    if !assignee.is_empty() {
        ops.push(json!({ "op": "add", "path": "/fields/System.AssignedTo", "value": assignee }));
    }
    Value::Array(ops)
}

pub struct Client {
    agent: ureq::Agent,
    /// Origin + org used for API calls (the test seam replaces `https://dev.azure.com`).
    api_org: String,
    /// Origin + org of the identities API (`https://vssps.dev.azure.com/<org>`, or the seam).
    identity_org: String,
    project: String,
    repo: String,
    creds: Vec<Cred>,
    /// Index of the credential in use; only ever moves forward.
    idx: usize,
}

impl Client {
    /// Errors when `SHIP_ADO_API_URL` would send a credential in cleartext: only
    /// `https://`, or `http://` on a loopback host (the test seam), is accepted.
    pub fn new(creds: Vec<Cred>, org_url: &str, project: &str, repo: &str) -> Result<Self, String> {
        if creds.is_empty() {
            return Err("no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)".to_string());
        }
        let seam = std::env::var("SHIP_ADO_API_URL").ok().filter(|s| !s.is_empty());
        if let Some(s) = &seam {
            http::check_base("SHIP_ADO_API_URL", s)?;
        }
        Ok(Client {
            agent: http::agent(),
            api_org: api_org(org_url, seam.as_deref()),
            identity_org: identity_org(org_url, seam.as_deref()),
            project: project.to_string(),
            repo: repo.to_string(),
            creds,
            idx: 0,
        })
    }

    /// Whether work item `id` exists: `Ok(true)` on 200, `Ok(false)` on 404, an error for
    /// anything else (including a credential every source of which was rejected).
    pub fn work_item_exists(&mut self, id: u64) -> Result<bool, String> {
        let url = format!("{}/_apis/wit/workitems/{id}?api-version={API_VERSION}", self.api_org);
        let (status, v) = self.send(&url, None, "")?;
        match status {
            200..=299 => Ok(v.get("id").is_some()),
            404 => Ok(false),
            _ => Err(api_error(status, &v)),
        }
    }

    /// Create the PR; the id the API returned.
    pub fn create_pr(&mut self, payload: &Value) -> Result<u64, String> {
        let url = format!(
            "{}/{}/_apis/git/repositories/{}/pullrequests?api-version={API_VERSION}",
            self.api_org,
            http::enc(&self.project),
            http::enc(&self.repo)
        );
        let (status, v) = self.send(&url, Some(payload), "application/json")?;
        if !(200..300).contains(&status) {
            return Err(api_error(status, &v));
        }
        v.get("pullRequestId")
            .and_then(Value::as_u64)
            .ok_or_else(|| "unexpected response creating the pull request".to_string())
    }

    /// Resolve a reviewer UPN to an identity id. A GUID passes through unchanged. Otherwise
    /// the vssps identities API is asked, starting on the credential in use and moving to the
    /// next after a 401/403/203/3xx. `Err` is the reason, for the "could not resolve" warning.
    pub fn resolve_identity(&self, upn: &str) -> Result<String, String> {
        if is_guid(upn) {
            return Ok(upn.to_string());
        }
        let url = format!(
            "{}/_apis/identities?searchFilter=General&filterValue={}&api-version={API_VERSION}",
            self.identity_org,
            http::encode_uri_component(upn)
        );
        let mut i = self.idx;
        let (status, v) = loop {
            let (status, v) = self.once(&self.creds[i].header(), &url, None, "")?;
            if !is_auth_failure(status) || i + 1 >= self.creds.len() {
                break (status, v);
            }
            eprintln!(">> identity lookup got HTTP {status}; retrying with the next credential");
            i += 1;
        };
        if !(200..300).contains(&status) || status == 203 {
            return Err(format!("HTTP {status}"));
        }
        v.get("value")
            .and_then(|a| a.get(0))
            .and_then(|e| e.get("id"))
            .and_then(Value::as_str)
            .filter(|id| !id.is_empty())
            .map(str::to_string)
            .ok_or_else(|| "no matching identity".to_string())
    }

    /// Create a work item of `wi_type` titled `title`, assigned to `assignee` unless it is
    /// empty; the `id` the API returned.
    pub fn create_work_item(&mut self, wi_type: &str, title: &str, assignee: &str) -> Result<u64, String> {
        let url = format!(
            "{}/{}/_apis/wit/workitems/{}?api-version={API_VERSION}",
            self.api_org,
            http::enc(&self.project),
            http::enc(&format!("${wi_type}"))
        );
        let doc = work_item_patch(title, assignee);
        let (status, v) = self.send(&url, Some(&doc), "application/json-patch+json")?;
        if !(200..300).contains(&status) {
            return Err(api_error(status, &v));
        }
        v.get("id")
            .and_then(Value::as_u64)
            .ok_or_else(|| "unexpected response creating the work item".to_string())
    }

    /// GET (no payload) or POST one request on the current credential. A 401/403, a 203
    /// (ADO's answer to a bad PAT is a sign-in page) or a redirect moves to the next
    /// credential once and prints the TS fallback line; later calls stay on it. With no
    /// credential left, the rejection comes back as an error.
    fn send(&mut self, url: &str, payload: Option<&Value>, content_type: &str) -> Result<(u16, Value), String> {
        loop {
            let (status, v) = self.once(&self.creds[self.idx].header(), url, payload, content_type)?;
            if !is_auth_failure(status) {
                return Ok((status, v));
            }
            if self.idx + 1 >= self.creds.len() {
                return Err(auth_error(status, &v));
            }
            eprintln!(
                ">> {} auth failed (401/403); falling back to {}",
                self.creds[self.idx].kind(),
                self.creds[self.idx + 1].kind()
            );
            self.idx += 1;
        }
    }

    fn once(&self, auth: &str, url: &str, payload: Option<&Value>, content_type: &str) -> Result<(u16, Value), String> {
        let ua = concat!("ship/", env!("CARGO_PKG_VERSION"));
        let result = match payload {
            None => self
                .agent
                .get(url)
                .header("Authorization", auth)
                .header("Accept", "application/json")
                .header("User-Agent", ua)
                .call(),
            Some(p) => self
                .agent
                .post(url)
                .header("Authorization", auth)
                .header("Accept", "application/json")
                .header("User-Agent", ua)
                .content_type(content_type)
                .send(p.to_string().as_bytes()),
        };
        let mut resp = match result {
            Ok(r) => r,
            // With redirects disabled ureq reports a 3xx as this error; ADO redirects a
            // rejected credential to a sign-in page, so it counts as an auth failure.
            Err(ureq::Error::TooManyRedirects) => return Ok((302, Value::Null)),
            Err(e) => return Err(format!("request failed: {e}")),
        };
        let status = resp.status().as_u16();
        let text = resp.body_mut().read_to_string().unwrap_or_default();
        Ok((status, serde_json::from_str(&text).unwrap_or(Value::Null)))
    }
}

fn is_auth_failure(status: u16) -> bool {
    matches!(status, 401 | 403 | 203) || (300..400).contains(&status)
}

/// `HTTP <status>: <message>` from the response; never contains a credential.
fn api_error(status: u16, v: &Value) -> String {
    match v.get("message").and_then(Value::as_str) {
        Some(m) => format!("HTTP {status}: {m}"),
        None => format!("HTTP {status}"),
    }
}

fn auth_error(status: u16, v: &Value) -> String {
    if matches!(status, 203) || (300..400).contains(&status) {
        format!("HTTP {status}: Azure DevOps answered with a sign-in page (credential rejected)")
    } else {
        api_error(status, v)
    }
}

/// The API origin + org: `org_url` with `https://dev.azure.com` swapped for the test seam.
fn api_org(org_url: &str, seam: Option<&str>) -> String {
    match (seam, org_url.strip_prefix(DEFAULT_ORIGIN)) {
        (Some(s), Some(rest)) => format!("{}{rest}", s.trim_end_matches('/')),
        _ => org_url.trim_end_matches('/').to_string(),
    }
}

/// The identities API origin + org: the org segment of `org_url` under `vssps.dev.azure.com`,
/// or under the test seam.
fn identity_org(org_url: &str, seam: Option<&str>) -> String {
    let org = org_url.strip_prefix(DEFAULT_ORIGIN).unwrap_or("").trim_matches('/');
    let origin = seam.map_or(IDENTITY_ORIGIN, |s| s.trim_end_matches('/'));
    format!("{origin}/{org}")
}

/// Standard base64 with padding (for the PAT `Basic` header); no crate needed.
fn base64(data: &[u8]) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for c in data.chunks(3) {
        let n = (u32::from(c[0]) << 16) | (u32::from(*c.get(1).unwrap_or(&0)) << 8) | u32::from(*c.get(2).unwrap_or(&0));
        out.push(T[(n >> 18) as usize & 63] as char);
        out.push(T[(n >> 12) as usize & 63] as char);
        out.push(if c.len() > 1 { T[(n >> 6) as usize & 63] as char } else { '=' });
        out.push(if c.len() > 2 { T[n as usize & 63] as char } else { '=' });
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn base64_matches_known_vectors() {
        assert_eq!(base64(b""), "");
        assert_eq!(base64(b"f"), "Zg==");
        assert_eq!(base64(b"fo"), "Zm8=");
        assert_eq!(base64(b"foo"), "Zm9v");
        assert_eq!(base64(b":pat"), "OnBhdA==");
    }

    #[test]
    fn headers_use_the_ts_schemes() {
        assert_eq!(Cred::Bearer("t".into()).header(), "Bearer t");
        assert_eq!(Cred::Pat("pat".into()).header(), "Basic OnBhdA==");
    }

    #[test]
    fn payload_omits_empty_fields_and_keeps_literals() {
        let p = create_payload("feat/x", "main", "a & b", "", false, &[], &[], &[]);
        assert_eq!(
            p,
            json!({"sourceRefName": "refs/heads/feat/x", "targetRefName": "refs/heads/main",
                   "title": "a & b", "workItemRefs": []})
        );
        let rv = [
            Reviewer { id: "i1".into(), is_required: false },
            Reviewer { id: "i2".into(), is_required: true },
        ];
        let p = create_payload("s", "t", "x", "body\n& more", true, &[42, 7], &["a".into(), "b".into()], &rv);
        assert_eq!(p["reviewers"], json!([{"id": "i1", "isRequired": false}, {"id": "i2", "isRequired": true}]));
        assert_eq!(p["description"], "body\n& more");
        assert_eq!(p["isDraft"], true);
        assert_eq!(p["workItemRefs"], json!([{"id": "42"}, {"id": "7"}]));
        assert_eq!(p["labels"], json!([{"name": "a"}, {"name": "b"}]));
    }

    #[test]
    fn guid_detection() {
        assert!(is_guid("1f0e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b"));
        assert!(is_guid("1F0E2D3C-4B5A-6978-8A9B-0C1D2E3F4A5B"));
        for bad in [
            "",
            "a@b.c",
            "1f0e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5",
            "1f0e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5bb",
            "zf0e2d3c-4b5a-6978-8a9b-0c1d2e3f4a5b",
        ] {
            assert!(!is_guid(bad), "{bad}");
        }
    }

    #[test]
    fn identity_origin_follows_the_seam() {
        assert_eq!(identity_org("https://dev.azure.com/acme", None), "https://vssps.dev.azure.com/acme");
        assert_eq!(
            identity_org("https://dev.azure.com/acme", Some("http://127.0.0.1:9/")),
            "http://127.0.0.1:9/acme"
        );
    }

    #[test]
    fn work_item_patch_assigns_only_when_non_empty() {
        let p = work_item_patch("t & u", "a@b");
        assert_eq!(
            p,
            json!([
                {"op": "add", "path": "/fields/System.Title", "value": "t & u"},
                {"op": "add", "path": "/fields/System.AssignedTo", "value": "a@b"}
            ])
        );
        assert_eq!(work_item_patch("t", "").as_array().unwrap().len(), 1);
    }

    #[test]
    fn seam_replaces_only_the_default_origin() {
        assert_eq!(api_org("https://dev.azure.com/acme", None), "https://dev.azure.com/acme");
        assert_eq!(
            api_org("https://dev.azure.com/acme", Some("http://127.0.0.1:9/")),
            "http://127.0.0.1:9/acme"
        );
    }

    #[test]
    fn auth_failures_include_203_and_redirects() {
        for s in [401, 403, 203, 302, 301] {
            assert!(is_auth_failure(s), "{s}");
        }
        for s in [200, 201, 404, 500] {
            assert!(!is_auth_failure(s), "{s}");
        }
    }
}
