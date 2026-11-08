#!/bin/sh
# Install the prebuilt `ship` binary. No bun, node, npm or Rust needed.
#
#   sh install.sh                      latest ship-v* GitHub Release
#   SHIP_VERSION=0.1.0 sh install.sh   a specific release
#   SHIP_ASSET_DIR=./artifacts sh install.sh
#                                      use already-downloaded assets (a folder holding
#                                      ship-<target> and ship-<target>.sha256, directly
#                                      or one level down) instead of a release
#
# Environment:
#   SHIP_INSTALL_DIR  destination directory (default: ~/.local/bin)
#   SHIP_REPO         GitHub owner/repo (default: julianobarbosa/claude-code-skills)
#   SHIP_VERSION      release version without the "ship-v" prefix
#   SHIP_ASSET_DIR    local directory of assets (skips the download)
set -eu

REPO=${SHIP_REPO:-julianobarbosa/claude-code-skills}
DEST=${SHIP_INSTALL_DIR:-$HOME/.local/bin}

die() { echo "ship install: $*" >&2; exit 1; }

case "$(uname -s)/$(uname -m)" in
  Linux/x86_64)  TARGET=x86_64-unknown-linux-musl ;;
  Darwin/arm64)  TARGET=aarch64-apple-darwin ;;
  *) die "unsupported host $(uname -s)/$(uname -m); supported: Linux x86_64 (incl. WSL2), macOS arm64" ;;
esac
ASSET=ship-$TARGET

if command -v sha256sum >/dev/null 2>&1; then
  hash_of() { sha256sum "$1" | cut -d' ' -f1; }
elif command -v shasum >/dev/null 2>&1; then
  hash_of() { shasum -a 256 "$1" | cut -d' ' -f1; }
else
  die "need sha256sum or shasum to verify the download"
fi

WORK=$(mktemp -d) || die "cannot create a temp directory"
trap 'rm -rf "$WORK"' EXIT
trap 'exit 130' INT TERM

if [ -n "${SHIP_ASSET_DIR:-}" ]; then
  for d in "$SHIP_ASSET_DIR" "$SHIP_ASSET_DIR"/*/; do
    if [ -f "$d/$ASSET" ] && [ -f "$d/$ASSET.sha256" ]; then
      cp "$d/$ASSET" "$d/$ASSET.sha256" "$WORK/"
      break
    fi
  done
  [ -f "$WORK/$ASSET" ] || die "no $ASSET and $ASSET.sha256 under $SHIP_ASSET_DIR"
else
  command -v curl >/dev/null 2>&1 || die "curl is required"
  VERSION=${SHIP_VERSION:-}
  VERSION=${VERSION#ship-}
  VERSION=${VERSION#v}
  if [ -z "$VERSION" ]; then
    RELEASES=$(curl -fsSL "https://api.github.com/repos/$REPO/releases?per_page=100") \
      || die "cannot list releases of $REPO"
    VERSION=$(printf '%s\n' "$RELEASES" \
      | sed -n 's/.*"tag_name": *"ship-v\([^"]*\)".*/\1/p' | head -n 1)
    [ -n "$VERSION" ] || die "no ship-v* release found in $REPO"
  fi
  BASE="https://github.com/$REPO/releases/download/ship-v$VERSION"
  echo "downloading ship $VERSION ($TARGET)"
  curl -fsSL -o "$WORK/$ASSET" "$BASE/$ASSET" || die "download failed: $BASE/$ASSET"
  curl -fsSL -o "$WORK/$ASSET.sha256" "$BASE/$ASSET.sha256" || die "download failed: $BASE/$ASSET.sha256"
fi

EXPECTED=$(cut -d' ' -f1 "$WORK/$ASSET.sha256")
ACTUAL=$(hash_of "$WORK/$ASSET")
if [ -z "$EXPECTED" ] || [ "$EXPECTED" != "$ACTUAL" ]; then
  die "checksum mismatch for $ASSET (expected ${EXPECTED:-none}, got $ACTUAL); nothing installed"
fi

mkdir -p "$DEST" || die "cannot create $DEST"
chmod +x "$WORK/$ASSET"
mv "$WORK/$ASSET" "$DEST/.ship.$$" || die "cannot write to $DEST"
mv "$DEST/.ship.$$" "$DEST/ship"
INSTALLED=$("$DEST/ship" --version) || die "installed $DEST/ship does not run"
echo "installed $DEST/ship: $INSTALLED"

case ":$PATH:" in
  *":$DEST:"*) ;;
  *) echo "note: $DEST is not on PATH; add it to your shell profile" ;;
esac
