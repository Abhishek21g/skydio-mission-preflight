"""Ingest mission scenario into receipt bundle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mission_preflight.plan import build_plan, load_mission, load_rules
from mission_preflight.store import make_run_id, receipt_dir, write_json


def execute_run(
    input_dir: Path,
    out_root: Path,
    *,
    label: str | None = None,
    rules_path: Path | None = None,
) -> dict[str, Any]:
    input_dir = input_dir.expanduser().resolve()
    mission_path = input_dir / "mission.yaml"
    if not mission_path.exists():
        raise FileNotFoundError(f"Expected mission.yaml in {input_dir}")

    mission = load_mission(mission_path)
    rules_file = rules_path or (input_dir / "rules.yaml")
    rules = load_rules(rules_file if rules_file.exists() else None)
    plan = build_plan(mission_path, rules_file if rules_file.exists() else None)

    run_id = make_run_id(label or mission.get("mission_id", input_dir.name))
    rdir = receipt_dir(out_root, run_id)

    ingested: dict[str, Any] = {
        "run_id": run_id,
        "input_dir": str(input_dir),
        "mission": mission,
        "rules": rules,
        "drone_count": len(mission.get("drones", [])),
        "operation": mission.get("operation"),
        "waiver_profile": mission.get("waiver_profile"),
    }

    write_json(rdir / "plan.json", plan)
    write_json(rdir / "ingested.json", ingested)
    write_json(
        rdir / "summary.json",
        {
            "run_id": run_id,
            "mission_id": mission.get("mission_id"),
            "operation": mission.get("operation"),
            "waiver_profile": mission.get("waiver_profile"),
            "drone_count": len(mission.get("drones", [])),
            "input_dir": str(input_dir),
        },
    )
    write_json(
        rdir / "manifest.json",
        {
            "run_id": run_id,
            "artifacts": ["plan.json", "ingested.json", "summary.json"],
            "tool": "skydio-mission-preflight",
            "version": "0.1.0",
        },
    )

    return {"run_id": run_id, "receipt_dir": str(rdir)}
