#!/usr/bin/env bash
# Publish site to enaguthi.com (Abhishek21g.github.io)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${SITE_DEST:-$HOME/Documents/Abhishek21g.github.io/skydio-mission-preflight/site}"

cd "$ROOT"
./scripts/export_site_data.sh
mkdir -p "$DEST"
rsync -av --delete site/ "$DEST/"
echo "Published to $DEST"
echo "Live: https://enaguthi.com/skydio-mission-preflight/site/"
