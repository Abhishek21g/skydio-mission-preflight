"""Tests for preflight checks."""

import pytest

from mission_preflight.checks import (
    check_adsb_bvlos,
    check_battery_health,
    check_deconfliction,
    check_rapid_preflight,
    check_shift_preflight,
    check_software_freshness,
    check_waiver_altitude,
    check_weather,
    run_all_checks,
)

RULES = {
    "min_battery_soc_percent": 80,
    "max_battery_cycles": 300,
    "max_wind_mph": 25,
    "require_adsb_for_bvlos": True,
    "require_shift_preflight": True,
    "require_rapid_preflight_per_drone": True,
    "max_concurrent_per_site_without_deconfliction": 1,
}


def test_shift_preflight_pass():
    mission = {"shift_preflight_completed": True}
    assert check_shift_preflight(mission, RULES).status == "pass"


def test_shift_preflight_fail():
    mission = {"shift_preflight_completed": False}
    assert check_shift_preflight(mission, RULES).status == "fail"


def test_rapid_preflight_fail():
    drones = [{"drone_id": "a", "rapid_preflight_done": False}]
    assert check_rapid_preflight(drones, RULES).status == "fail"


def test_battery_low_soc_fail():
    drones = [{"drone_id": "a", "battery_soc_percent": 50, "battery_cycles": 10}]
    assert check_battery_health(drones, RULES).status == "fail"


def test_battery_high_cycles_warn():
    drones = [{"drone_id": "a", "battery_soc_percent": 90, "battery_cycles": 310}]
    assert check_battery_health(drones, RULES).status == "warn"


def test_software_stale_fail():
    drones = [
        {
            "drone_id": "a",
            "software_version": "2.3.0",
            "min_software_version": "2.4.0",
        }
    ]
    assert check_software_freshness(drones).status == "fail"


def test_adsb_missing_fail():
    mission = {"waiver_profile": "part91-200ft-bvlos"}
    drones = [{"drone_id": "a", "adsb_in": False}]
    assert check_adsb_bvlos(mission, drones, RULES).status == "fail"


def test_waiver_altitude_violation():
    mission = {"max_altitude_ft": 200}
    drones = [{"drone_id": "a", "planned_max_altitude_ft": 350}]
    assert check_waiver_altitude(mission, drones).status == "fail"


def test_weather_precip_fail():
    mission = {"weather": {"wind_mph": 5, "precip": True}}
    assert check_weather(mission, RULES).status == "fail"


def test_deconfliction_overlap_warn():
    mission = {"deconfliction_enabled": False, "sites": []}
    drones = [
        {"drone_id": "a", "geofence_id": "pad-1"},
        {"drone_id": "b", "geofence_id": "pad-1"},
    ]
    assert check_deconfliction(mission, drones, RULES).status == "warn"


def test_deconfliction_concurrent_site_fail():
    mission = {
        "deconfliction_enabled": False,
        "sites": [{"site_id": "s1", "concurrent_missions": 4}],
    }
    drones = [{"drone_id": "a", "geofence_id": "pad-1"}]
    assert check_deconfliction(mission, drones, RULES).status == "fail"


def test_run_all_checks_count():
    mission = {
        "shift_preflight_completed": True,
        "waiver_profile": "part91-200ft-bvlos",
        "max_altitude_ft": 200,
        "weather": {"wind_mph": 5, "precip": False},
        "sites": [{"site_id": "s", "concurrent_missions": 1}],
        "drones": [
            {
                "drone_id": "a",
                "battery_soc_percent": 90,
                "battery_cycles": 10,
                "software_version": "2.4.1",
                "min_software_version": "2.4.0",
                "adsb_in": True,
                "rapid_preflight_done": True,
                "planned_max_altitude_ft": 150,
                "geofence_id": "pad",
            }
        ],
    }
    assert len(run_all_checks(mission, RULES)) == 8
