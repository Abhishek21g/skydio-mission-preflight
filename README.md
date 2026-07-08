# Skydio Mission Preflight Workbench

**Operational preflight receipts for BVLOS and multi-drone fleet launches.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Live demo](https://img.shields.io/badge/demo-live-2da44e)](https://enaguthi.com/skydio-mission-preflight/site/)

### [→ Live demo](https://enaguthi.com/skydio-mission-preflight/site/) · [GitHub](https://github.com/Abhishek21g/skydio-mission-preflight)

---

## What it answers

| Question | Command |
|----------|---------|
| Is this **mission stack** cleared to launch? | `doctor` |
| Did we miss **shift vs rapid** preflight steps? | `doctor` → shift / rapid checks |
| Are **waiver limits** (altitude, ADS-B) satisfied? | `doctor` → waiver / ADS-B checks |
| Can **4 concurrent inspections** deconflict? | `doctor` → multi-drone deconfliction |

Independent of any upstream PR — this targets **fleet operator readiness**, not git tooling.

---

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 60-second bundled demo (no hardware, no API keys)
mission-preflight demo --out out/demo

# Single scenario
mission-preflight run --input examples/dfr-rapid-launch --out out
mission-preflight doctor <run_id> --out out --json
mission-preflight report <run_id> --out out
```

---

## CLI

```
plan   — build manifest + risk list from mission.yaml
run    — ingest scenario → out/receipts/<run-id>/
doctor — 8-signal readiness gate (pass / warn / fail)
report — Markdown receipt for ops handoff
demo   — three bundled scenarios (cleared / caution / blocked)
```

All commands support `--json` where applicable.

---

## Bundled scenarios

| Scenario | Expected | Story |
|----------|----------|-------|
| `dfr-rapid-launch` | **cleared** | DFR call-for-service — shift + rapid preflight done |
| `multi-drone-inspection` | **caution** | 4 drones, shared geofence without deconfliction flag |
| `bvlos-waiver-block` | **blocked** | Planned altitude exceeds 200ft Part 91 waiver |

---

## Receipt layout

```
out/receipts/<run-id>/
  manifest.json
  plan.json
  ingested.json
  summary.json
  doctor.json
  report.md
```

---

## Development

```bash
pytest tests/ -q
ruff check mission_preflight/ tests/
mission-preflight demo --out out/demo
./scripts/export_site_data.sh
```

---

## Disclaimer

Independent demo inspired by Skydio's **public** BVLOS / operational-readiness guidance. Not affiliated with or endorsed by Skydio.

Built by [Abhishek Enaguthi](https://enaguthi.com/) · BS/MS CS & AI, Oregon State University
