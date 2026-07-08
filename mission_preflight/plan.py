"""Build preflight plan manifests from mission YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES = {
    "min_battery_soc_percent": 80,
    "max_battery_cycles": 300,
    "max_wind_mph": 25,
    "require_adsb_for_bvlos": True,
    "require_shift_preflight": True,
    "require_rapid_preflight_per_drone": True,
    "max_concurrent_per_site_without_deconfliction": 1,
}


def load_mission(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Mission file must be a mapping: {path}")
    return data


def load_rules(path: Path | None) -> dict[str, Any]:
    if path is None:
        return dict(DEFAULT_RULES)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rules = dict(DEFAULT_RULES)
    rules.update(data)
    return rules


def build_plan(mission_path: Path, rules_path: Path | None = None) -> dict[str, Any]:
    mission = load_mission(mission_path)
    rules = load_rules(rules_path)
    drones = mission.get("drones", [])
    sites = mission.get("sites", [])

    risks: list[str] = []
    if mission.get("operation") == "multi_drone_inspection":
        risks.append("Concurrent missions — verify site deconfliction is enabled")
    if "bvlos" in str(mission.get("waiver_profile", "")).lower():
        risks.append("BVLOS waiver — ADS-B In and altitude caps apply")
    if len(drones) > 1 and not mission.get("deconfliction_enabled", False):
        risks.append("Multiple drones without fleet deconfliction flag")

    return {
        "mission_id": mission.get("mission_id", mission_path.stem),
        "operation": mission.get("operation", "unknown"),
        "waiver_profile": mission.get("waiver_profile", "none"),
        "max_altitude_ft": mission.get("max_altitude_ft"),
        "airspace_class": mission.get("airspace_class"),
        "drone_count": len(drones),
        "site_count": len(sites),
        "rules": rules,
        "risks": risks,
        "source_mission": str(mission_path.resolve()),
    }
