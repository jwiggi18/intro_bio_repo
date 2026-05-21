#!/usr/bin/env bash
# build.sh — BIOL 1113 Canvas build script
#
# Usage:
#   bash build/build.sh              # build all week* folders
#   bash build/build.sh week01/      # build one week
#   bash build/build.sh week01/overview.html  # build one file
#
# Output: build/biol1113/ (gitignored — do not edit files there)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TARGET="${1:-}"

echo "=== BIOL 1113 Build ==="
echo "Root: $REPO_ROOT"
echo ""

# Require Python 3
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is required."
  exit 1
fi

python3 build/inline_css.py $TARGET

echo ""
echo "Canvas-ready HTML is in build/biol1113/"
echo "Upload via: python3 scripts/upload_to_canvas.py"
