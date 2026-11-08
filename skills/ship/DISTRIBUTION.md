# Distribution of the `ship` binary

**Decision (Barbosa, 2026-11-08): GitHub Releases.**

## What

- Pushing a `ship-v<version>` tag runs `.github/workflows/ship-release.yml`, which builds `ship` for
  `x86_64-unknown-linux-musl` and `aarch64-apple-darwin`, smoke-tests each binary on its own runner,
  and attaches `ship-<target>` plus `ship-<target>.sha256` to a GitHub Release.
- The version has one source: `version` in `skills/ship/Cargo.toml`. The workflow refuses a tag that does
  not equal `ship-v<Cargo version>`, so `ship --version` (`ship <version>`) always matches the release.
- Pull requests and manual runs build and test the same way but only upload workflow artifacts; they never
  create a tag or release.
- `.github/workflows/ship-rust.yml` runs `cargo test` and `cargo clippy --all-targets -- -D warnings` on PRs
  touching `skills/ship/**`.

## Targets

| Target | Why |
|--------|-----|
| `x86_64-unknown-linux-musl` | Static binary: runs on any WSL2 distro with no libc dependency. |
| `aarch64-apple-darwin` | macOS arm64. Built on a GitHub-hosted `macos-14` runner; it cannot be built on the Linux/WSL2 workstation. |

## Install

```sh
sh skills/ship/install.sh                       # latest ship-v* release
SHIP_VERSION=0.1.0 sh skills/ship/install.sh    # pin a version
SHIP_INSTALL_DIR=/usr/local/bin sh skills/ship/install.sh
```

The script picks the asset for the host, verifies its SHA-256 against the `.sha256` file and aborts with
`checksum mismatch` before installing anything if they differ. It needs only POSIX `sh`, `curl` and
`sha256sum`/`shasum`; no bun, npm, npx, Python or Rust. `SHIP_ASSET_DIR=<dir>` installs from
already-downloaded assets (used to test against workflow artifacts).

Notes:

- The `.sha256` guards against corrupted downloads, not a tampered release: it is served from the same
  origin as the binary.
- To test against a PR's workflow artifacts: `gh run download <run-id> -D artifacts`, then
  `SHIP_ASSET_DIR=artifacts sh skills/ship/install.sh`.
- Linux aarch64 and Intel macOS are not targets; use the bun scripts there until Story 5.2.

## Why GitHub Releases

- Committed per-platform builds put binaries in git history forever and can drift from the source.
- `cargo install` needs a Rust toolchain on every machine, which is the install burden this port removes.
- Releases keep binaries out of git, tie each one to a tag and checksum, and are fetched with plain `curl`.
- Trade-off: the repo is public, so released binaries are public.

## Releasing

Bump `version` in `skills/ship/Cargo.toml`, merge, then push the tag `ship-v<version>`. The first release
(`ship-v0.1.0`) is cut on an explicit go-ahead.
