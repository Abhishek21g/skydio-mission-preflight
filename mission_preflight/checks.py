"""Preflight doctor checks — inspired by Skydio public BVLOS / ops guidance."""

from __future__ import annotations

from typing import Any

from mission_preflight.models import CheckResult


def _parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.strip().split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            break
    return tuple(parts) if parts else (0,)


def check_shift_preflight(mission: dict[str, Any], rules: dict[str, Any]) -> CheckResult:
    if not rules.get("require_shift_preflight", True):
        return CheckResult("shift_preflight", "pass", "Shift preflight not required by rules")
    if mission.get("shift_preflight_completed"):
        return CheckResult("shift_preflight", "pass", "Shift-start preflight completed")
    return CheckResult(
        "shift_preflight",
        "fail",
        "Shift-start preflight not completed — required before BVLOS launch",
        {"recommendation": "Run full fleet inspection at shift start per Part 91.103"},
    )


def check_rapid_preflight(drones: list[dict[str, Any]], rules: dict[str, Any]) -> CheckResult:
    if not rules.get("require_rapid_preflight_per_drone", True):
        return CheckResult("rapid_preflight", "pass", "Rapid preflight not required by rules")
    missing = [d.get("drone_id", "?") for d in drones if not d.get("rapid_preflight_done")]
    if not missing:
        return CheckResult("rapid_preflight", "pass", "All launching drones passed rapid preflight")
    return CheckResult(
        "rapid_preflight",
        "fail",
        f"Rapid preflight incomplete for: {', '.join(missing)}",
        {"drones": missing},
    )


def check_battery_health(drones: list[dict[str, Any]], rules: dict[str, Any]) -> CheckResult:
    min_soc = int(rules.get("min_battery_soc_percent", 80))
    max_cycles = int(rules.get("max_battery_cycles", 300))
    low_soc = []
    high_cycles = []
    for drone in drones:
        did = drone.get("drone_id", "?")
        soc = drone.get("battery_soc_percent")
        cycles = drone.get("battery_cycles")
        if soc is not None and soc < min_soc:
            low_soc.append(f"{did} ({soc}%)")
        if cycles is not None and cycles >= max_cycles:
            high_cycles.append(f"{did} ({cycles} cycles)")
    if low_soc:
        return CheckResult(
            "battery_health",
            "fail",
            f"Battery SOC below {min_soc}%: {', '.join(low_soc)}",
            {"low_soc": low_soc},
        )
    if high_cycles:
        return CheckResult(
            "battery_health",
            "warn",
            f"Battery cycle count at or above {max_cycles}: {', '.join(high_cycles)}",
            {"high_cycles": high_cycles},
        )
    return CheckResult("battery_health", "pass", "All drone batteries within limits")


def check_software_freshness(drones: list[dict[str, Any]]) -> CheckResult:
    stale = []
    for drone in drones:
        current = str(drone.get("software_version", "0.0.0"))
        minimum = str(drone.get("min_software_version", "0.0.0"))
        if _parse_version(current) < _parse_version(minimum):
            stale.append(
                f"{drone.get('drone_id', '?')} ({current} < {minimum})"
            )
    if stale:
        return CheckResult(
            "software_freshness",
            "fail",
            f"Software update required: {', '.join(stale)}",
            {"stale_drones": stale},
        )
    return CheckResult("software_freshness", "pass", "Fleet software meets minimum versions")


def check_adsb_bvlos(
    mission: dict[str, Any], drones: list[dict[str, Any]], rules: dict[str, Any]
) -> CheckResult:
    waiver = str(mission.get("waiver_profile", "")).lower()
    if "bvlos" not in waiver and not mission.get("requires_adsb", False):
        return CheckResult("adsb_bvlos", "pass", "ADS-B not required for this operation profile")
    if not rules.get("require_adsb_for_bvlos", True):
        return CheckResult("adsb_bvlos", "pass", "ADS-B check disabled in rules")
    missing = [d.get("drone_id", "?") for d in drones if not d.get("adsb_in")]
    if missing:
        return CheckResult(
            "adsb_bvlos",
            "fail",
            f"ADS-B In required for BVLOS — missing on: {', '.join(missing)}",
            {"drones": missing},
        )
    return CheckResult("adsb_bvlos", "pass", "ADS-B In present on all launching drones")


def check_waiver_altitude(
    mission: dict[str, Any], drones: list[dict[str, Any]]
) -> CheckResult:
    cap = mission.get("max_altitude_ft")
    if cap is None:
        return CheckResult("waiver_altitude", "pass", "No altitude cap in mission manifest")
    violations = []
    for drone in drones:
        planned = drone.get("planned_max_altitude_ft")
        if planned is not None and planned > cap:
            violations.append(
                f"{drone.get('drone_id', '?')} ({planned}ft > {cap}ft waiver cap)"
            )
    if violations:
        return CheckResult(
            "waiver_altitude",
            "fail",
            f"Planned altitude exceeds waiver: {', '.join(violations)}",
            {"violations": violations, "waiver_cap_ft": cap},
        )
    return CheckResult(
        "waiver_altitude",
        "pass",
        f"All planned altitudes within {cap}ft waiver cap",
        {"waiver_cap_ft": cap},
    )


def check_weather(mission: dict[str, Any], rules: dict[str, Any]) -> CheckResult:
    weather = mission.get("weather") or {}
    wind = weather.get("wind_mph")
    precip = weather.get("precip", False)
    max_wind = int(rules.get("max_wind_mph", 25))
    if precip:
        return CheckResult(
            "weather_window",
            "fail",
            "Active precipitation — launch not recommended",
            {"precip": True},
        )
    if wind is not None and wind > max_wind:
        return CheckResult(
            "weather_window",
            "warn",
            f"Wind {wind} mph exceeds recommended {max_wind} mph",
            {"wind_mph": wind, "max_wind_mph": max_wind},
        )
    return CheckResult("weather_window", "pass", "Weather within operational window")


def check_deconfliction(
    mission: dict[str, Any], drones: list[dict[str, Any]], rules: dict[str, Any]
) -> CheckResult:
    if mission.get("deconfliction_enabled", False):
        return CheckResult(
            "multi_drone_deconfliction",
            "pass",
            "Fleet deconfliction enabled for concurrent operations",
        )

    by_fence: dict[str, list[str]] = {}
    for drone in drones:
        fence = drone.get("geofence_id") or "default"
        by_fence.setdefault(fence, []).append(drone.get("drone_id", "?"))

    overlaps = {k: v for k, v in by_fence.items() if len(v) > 1}
    max_concurrent = int(rules.get("max_concurrent_per_site_without_deconfliction", 1))

    for site in mission.get("sites", []):
        concurrent = int(site.get("concurrent_missions", 1))
        if concurrent > max_concurrent:
            return CheckResult(
                "multi_drone_deconfliction",
                "fail",
                (
                    f"Site {site.get('site_id', '?')} has {concurrent} concurrent missions "
                    f"without deconfliction (max {max_concurrent})"
                ),
                {"site_id": site.get("site_id"), "concurrent_missions": concurrent},
            )

    if overlaps:
        return CheckResult(
            "multi_drone_deconfliction",
            "warn",
            (
                "Multiple drones share geofence without deconfliction flag: "
                + ", ".join(f"{k}=[{', '.join(v)}]" for k, v in overlaps.items())
            ),
            {"overlapping_geofences": overlaps},
        )

    return CheckResult(
        "multi_drone_deconfliction",
        "pass",
        "No concurrent geofence overlap detected",
    )


def run_all_checks(mission: dict[str, Any], rules: dict[str, Any]) -> list[CheckResult]:
    drones = mission.get("drones", [])
    return [
        check_shift_preflight(mission, rules),
        check_rapid_preflight(drones, rules),
        check_battery_health(drones, rules),
        check_software_freshness(drones),
        check_adsb_bvlos(mission, drones, rules),
        check_waiver_altitude(mission, drones),
        check_weather(mission, rules),
        check_deconfliction(mission, drones, rules),
    ]
