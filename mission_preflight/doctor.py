"""Doctor: evaluate mission readiness from ingested state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mission_preflight.checks import run_all_checks
from mission_preflight.models import overall_status
from mission_preflight.store import read_json, receipt_dir, write_json


def diagnose_receipt(receipt_path: Path) -> dict[str, Any]:
    receipt_path = receipt_path.expanduser().resolve()
    rdir = receipt_path if receipt_path.is_dir() else receipt_path.parent

    ingested = read_json(rdir / "ingested.json")
    mission = ingested.get("mission", {})
    rules = ingested.get("rules", {})
    plan = read_json(rdir / "plan.json") if (rdir / "plan.json").exists() else {}

    checks = run_all_checks(mission, rules)
    statuses = [c.status for c in checks]
    result = {
        "run_id": ingested.get("run_id", rdir.name),
        "receipt_dir": str(rdir),
        "mission_id": mission.get("mission_id", plan.get("mission_id", rdir.name)),
        "overall_status": overall_status(statuses),
        "launch_recommendation": _launch_recommendation(statuses),
        "checks": [c.to_dict() for c in checks],
    }
    write_json(rdir / "doctor.json", result)
    return result


def _launch_recommendation(statuses: list[str]) -> str:
    overall = overall_status(statuses)
    if overall == "blocked":
        return "hold"
    if overall == "caution":
        return "review"
    return "go"


def resolve_receipt(path: str | Path, out_root: Path | None = None) -> Path:
    path = Path(path).expanduser()
    if path.is_dir() and (path / "ingested.json").exists():
        return path
    if out_root:
        candidate = receipt_dir(out_root, path.name)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No receipt at {path}")
