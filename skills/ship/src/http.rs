//! Pieces shared by the GitHub and Azure DevOps clients: the `ureq` agent, the
//! cleartext-token guard for the test-seam base URLs, and path-segment encoding.

use std::time::Duration;

/// Blocking agent: the caller reads the status and error body itself, redirects are never
/// followed (a credential must not reach another host), certificates are checked against
/// the OS trust store.
pub fn agent() -> ureq::Agent {
    ureq::Agent::config_builder()
        .http_status_as_error(false)
        .max_redirects(0)
        .timeout_global(Some(Duration::from_secs(60)))
        .tls_config(
            ureq::tls::TlsConfig::builder()
                .root_certs(ureq::tls::RootCerts::PlatformVerifier)
                .build(),
        )
        .build()
        .into()
}

/// Refuse a base URL (read from env var `var`) that would put a credential on the wire
/// unencrypted: only `https://`, or `http://` on a loopback host (the test seam).
pub fn check_base(var: &str, base: &str) -> Result<(), String> {
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
        "refusing {var} '{base}': the token is only sent over https:// (or http:// to localhost)"
    ))
}

/// Percent-encode one URL path segment (owner, repo and project come from a remote URL).
pub fn enc(s: &str) -> String {
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

/// JavaScript `encodeURIComponent`: leaves `A-Za-z0-9 - _ . ! ~ * ' ( )` as is. Used for
/// the printed `pr_url`, which must match the TS byte for byte.
pub fn encode_uri_component(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for b in s.bytes() {
        if b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b'!' | b'~' | b'*' | b'\'' | b'(' | b')') {
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
    fn uri_component_matches_javascript() {
        assert_eq!(encode_uri_component("My Project (x)!"), "My%20Project%20(x)!");
        assert_eq!(encode_uri_component("a/b&c"), "a%2Fb%26c");
        assert_eq!(encode_uri_component("é"), "%C3%A9");
    }

    #[test]
    fn base_url_must_be_https_or_loopback() {
        for ok in ["https://api.github.com", "http://127.0.0.1:8080", "http://localhost", "http://[::1]:9/x"] {
            assert!(check_base("V", ok).is_ok(), "{ok}");
        }
        for bad in ["http://example.com", "http://127.0.0.1@evil.com", "ftp://x", "api.github.com", "http://localhost.evil.com"] {
            assert!(check_base("V", bad).is_err(), "{bad}");
        }
        assert!(check_base("SHIP_X", "http://e.com").unwrap_err().contains("SHIP_X"));
    }

    #[test]
    fn path_segments_are_encoded() {
        assert_eq!(enc("my repo"), "my%20repo");
        assert_eq!(enc(".dotfiles"), ".dotfiles");
        assert_eq!(enc("a/b&c"), "a%2Fb%26c");
    }
}
