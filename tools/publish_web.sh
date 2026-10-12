#!/bin/bash
# Builds the Web export and publishes it to the gh-pages branch (GitHub Pages).
# Usage: tools/publish_web.sh [path-to-godot]
set -euo pipefail
GODOT="${1:-godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf export/web && mkdir -p export/web
"$GODOT" --headless --path . --export-release "Web" export/web/index.html
touch export/web/.nojekyll
TMP="$(mktemp -d)"
cp -r export/web/. "$TMP"
cd "$TMP"
git init -q -b gh-pages
git add -A
git commit -q -m "Web build $(date -u +%Y-%m-%dT%H:%MZ)"
git push -f "$(git -C "$ROOT" remote get-url origin)" gh-pages
rm -rf "$TMP"
echo "Published. Pages URL: https://$(git -C "$ROOT" remote get-url origin | sed -E 's#.*github.com[:/]([^/]+)/([^/.]+).*#\1.github.io/\2#')/"
