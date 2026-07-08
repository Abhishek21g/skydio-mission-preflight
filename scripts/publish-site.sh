#!/usr/bin/env bash
# Sync site/ to enaguthi.com via Abhishek21g.github.io public/ on main.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${SITE_REPO:-$HOME/Documents/Abhishek21g.github.io}"
TARGET="public/skydio-mission-preflight"

if [[ ! -d "$DEST/.git" ]]; then
  echo "error: portfolio repo not found at $DEST" >&2
  exit 1
fi

echo "==> Refresh demo data"
"$ROOT/scripts/export_site_data.sh"

echo "==> Sync to $DEST/$TARGET/"
cd "$DEST"
PREV_BRANCH="$(git branch --show-current 2>/dev/null || echo main)"
trap 'git checkout "$PREV_BRANCH" 2>/dev/null || true' EXIT

git checkout main
git pull origin main --no-rebase

mkdir -p "$TARGET"
rsync -av --delete "$ROOT/site/" "$DEST/$TARGET/site/"
cat > "$DEST/$TARGET/index.html" <<'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="refresh" content="0; url=./site/" />
    <title>Mission Preflight Workbench</title>
    <link rel="canonical" href="./site/" />
    <script>window.location.replace("./site/");</script>
  </head>
  <body>
    <p>Redirecting to <a href="./site/">Mission Preflight Workbench</a>.</p>
  </body>
</html>
HTML

git add "$TARGET/"
if git diff --cached --quiet; then
  echo "No site changes to publish."
  exit 0
fi

git commit -m "Add Skydio Mission Preflight Workbench demo to public/skydio-mission-preflight"
git pull origin main --no-rebase
git push origin main

trap - EXIT

echo "Published to main — deploys to https://enaguthi.com/skydio-mission-preflight/site/"
echo "Monitor: https://github.com/Abhishek21g/Abhishek21g.github.io/actions"
