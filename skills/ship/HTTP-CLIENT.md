# HTTP client decision

**Decision (Barbosa, 2026-11-08):** `ureq` 3 + `serde_json`, direct REST calls, for GitHub and Azure DevOps.

## Candidates

Versions and maintenance status checked on crates.io on 2026-11-08.

| Candidate | Version | Maintained | Verdict |
|---|---|---|---|
| `octocrab` (GitHub) | 0.54.9 | yes | Rejected: pulls in tokio + reqwest |
| `azure_devops_rust_api` (Azure DevOps) | 0.39.1 | yes | Rejected: pulls in tokio + reqwest |
| `ureq` | 3.5.1 | yes | **Chosen** |

## Why `ureq` and direct REST

- It is blocking, so there is no async runtime in a CLI that makes a handful of sequential calls.
- TLS is rustls (`ring`) with the OS trust store, so there is no OpenSSL and no system library; release builds stay static on `x86_64-unknown-linux-musl` and build on `aarch64-apple-darwin`.
- It keeps the binary small and startup fast (NFR9). The musl release binary is about 4 MB.
- The TS scripts call only about 8 endpoints, so a typed SDK buys little and costs a large dependency tree.

## How it is used

- `src/github.rs` holds the GitHub calls. Story 3.2 adds `src/azure.rs` beside it.
- The agent is built with `http_status_as_error(false)` (the caller reads the status and the error body) and `max_redirects(0)`: a credential is never forwarded to another host.
- The token goes only into an `Authorization: Bearer` header. It is never put in a URL, output, log or file, and error text is built from the response status, message and `errors[]` details, never the token.
- `SHIP_GITHUB_API_URL` replaces the base URL (default `https://api.github.com`). It is a test seam only: GitHub Enterprise is not supported yet (`gh auth token` is not asked for a host, and owner/repo parsing needs a `github` host, so a github.com token would go to the wrong server). The token is refused over cleartext: the base must be `https://`, or `http://` on `127.0.0.1`, `::1` or `localhost`.

## Trust store

ureq's default rustls roots (bundled `webpki-roots`) ignore the OS trust store, so a TLS-inspecting network with corporate root CAs (as on this host, `/usr/local/share/ca-certificates`) would fail every call. The crate enables ureq's `platform-verifier` feature and sets `RootCerts::PlatformVerifier`, so certificates are checked against the OS store. It adds `rustls-platform-verifier`, `rustls-native-certs` and `openssl-probe` (a small crate that locates CA bundle paths; it does not link OpenSSL). Still no tokio and no OpenSSL in `cargo tree`. Size delta of the musl release binary: 4,068,392 to 4,105,256 bytes (+36,864, about 0.9%).

## Dependencies

Only `ureq` and `serde_json` were added to the crate (alongside `clap` and `regex`). No async runtime, no OpenSSL.

## Azure DevOps (Story 3.2)

`src/azure.rs` holds the Azure calls; the agent, the https-or-loopback guard and path encoding are shared with GitHub in `src/http.rs`.

| Call | Request |
|---|---|
| Work-item read | `GET {org}/_apis/wit/workitems/{id}?api-version=7.1` (200 = exists, 404 = missing, anything else fails the run) |
| PR create | `POST {org}/{project}/_apis/git/repositories/{repo}/pullrequests?api-version=7.1` with `sourceRefName`, `targetRefName`, `title`, `description`, `isDraft`, `workItemRefs`, `labels` |
| Work-item create (Story 3.3) | `POST {org}/{project}/_apis/wit/workitems/${type}?api-version=7.1`, `Content-Type: application/json-patch+json`, body `[{"op":"add","path":"/fields/System.Title","value":<title>}]` plus an `/fields/System.AssignedTo` op when the assignee is non-empty. The `$type` segment is percent-encoded (`User Story` becomes `%24User%20Story`); the printed id is the response's `id`. |
| Identity lookup (Story 3.4) | `GET https://vssps.dev.azure.com/{org}/_apis/identities?searchFilter=General&filterValue=<encodeURIComponent(upn)>&api-version=7.1`; the identity is `value[0].id` |
| Completion option (Story 3.5) | `PATCH {org}/{project}/_apis/git/repositories/{repo}/pullrequests/{id}?api-version=7.1`, `Content-Type: application/json`, body `{"completionOptions":{"transitionWorkItems":<bool>}}` (the create call drops `completionOptions`) |
| Work-item state (Story 3.5) | `PATCH {org}/{project}/_apis/wit/workitems/{id}?api-version=7.1`, `Content-Type: application/json-patch+json`, body `[{"op":"add","path":"/fields/System.State","value":<state>}]` |

`{org}` is `https://dev.azure.com/<org>`; project and repo are percent-encoded in the path. The identities API lives on a different origin, `https://vssps.dev.azure.com/{org}` (org = the org segment of the org URL).

**Reviewers (Story 3.4).** Each `--reviewer` (optional) and `--required-reviewer` UPN is resolved after work-item handling and before the PR create, optional first. A GUID passes through with no lookup. The lookup starts on the credential the client is on and moves to the next after a 401/403/203/3xx, printing `>> identity lookup got HTTP <status>; retrying with the next credential`. A name that cannot be resolved prints `>> WARNING: could not resolve reviewer '<upn>' (<why>); skipping` and `reviewer_skipped=<upn>` (printed at that point, before `platform=azure`) and never blocks the PR. Each UPN is looked up once, and one resolved identity appears once in `reviewers` and in the `reviewer_added=` lines (first UPN spelling, `required=true` if either list named it, so a UPN plus its GUID, or the same person in both flags, is not sent twice). An empty `id` counts as `no matching identity`.

`SHIP_ADO_DEFAULT_REVIEWER`: trimmed; used only when neither `--reviewer` nor `--required-reviewer` is given; ignored with `--no-reviewer`; always added as an optional reviewer, with `>> NOTE: no reviewer given; using SHIP_ADO_DEFAULT_REVIEWER (<value>)`. Resolved reviewers go into the create body as `reviewers: [{id, isRequired}]` (omitted when none resolved); `reviewer_added=<upn> required=<bool>` lines follow `tag_added=`.

**Transitions (Story 3.5).** After `work_items=`, every Azure PR gets the completion PATCH: `true` by default, an explicit `false` with `--no-complete-transition`. `complete_transitions_work_items=` prints the response's `completionOptions.transitionWorkItems` (`unset` when it is absent, null or not a boolean, or when the PATCH fails, which also prints a WARNING). Then, with a non-empty `--transition <state>`, each linked item gets the state PATCH and prints `work_item=<id> state=<state>`; a rejected one warns and the loop goes on. Both steps are best-effort (exit 0 once the PR exists), use the same credential fallback as every other call, and come before `tag_added=`. GitHub ignores both flags.

**Auth order (NFR5).** The `az` token (`git::try_ado_token`) is sent as `Authorization: Bearer`. A PAT (`AZURE_DEVOPS_EXT_PAT`, else `AZURE_DEVOPS_PAT`) is sent as `Authorization: Basic base64(":" + pat)`. With neither, the run exits 1 before any request. A 401 or 403 moves to the next credential once, prints `>> bearer auth failed (401/403); falling back to pat`, and later calls stay on it. With no credential left, the rejection is `ship-pr failed: HTTP <status>: <message>`, except on the post-create PATCHes (Story 3.5), which warn and let the run finish.

**The 203 rule.** Azure DevOps answers a bad PAT with `203` (an HTML sign-in page) or a redirect to one. A 203 or any 3xx is therefore treated like a 401/403: it triggers the fallback, or fails the run when no credential is left. Redirects are never followed, so a credential cannot reach another host.

**Test seam.** `SHIP_ADO_API_URL` replaces the `https://dev.azure.com` origin of API calls and also the `https://vssps.dev.azure.com` origin of identity lookups (same https-or-loopback guard as `SHIP_GITHUB_API_URL`). The printed `pr_url` still uses the real org URL.

## musl note

`ring` compiles C. On `x86_64-unknown-linux-musl`, cc-rs looks for `musl-gcc`, so the musl leg of `.github/workflows/ship-release.yml` installs `musl-tools`. The macOS leg needs nothing extra.
