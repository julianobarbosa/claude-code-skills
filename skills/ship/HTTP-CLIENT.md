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

## musl note

`ring` compiles C. On `x86_64-unknown-linux-musl`, cc-rs looks for `musl-gcc`, so the musl leg of `.github/workflows/ship-release.yml` installs `musl-tools`. The macOS leg needs nothing extra.
