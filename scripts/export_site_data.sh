#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=site/data
rm -rf out/site-export
mission-preflight demo --out out/site-export
mkdir -p "$OUT"
python3 << 'PY'
import json
from pathlib import Path

export = Path("out/site-export/receipts")
runs = []
for rdir in sorted(export.iterdir()):
    if not rdir.is_dir():
        continue
    doctor = json.loads((rdir / "doctor.json").read_text())
    summary = json.loads((rdir / "summary.json").read_text())
    plan = json.loads((rdir / "plan.json").read_text()) if (rdir / "plan.json").exists() else {}
    runs.append({
        "doctor": doctor,
        "summary": summary,
        "plan": plan,
        "receipt_dir": f"out/site-export/receipts/{rdir.name}",
    })
Path("site/data/demo.json").write_text(json.dumps({"runs": runs}, indent=2) + "\n")
print(f"Wrote site/data/demo.json ({len(runs)} runs)")
PY
