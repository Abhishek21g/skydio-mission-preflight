"""Plan builder tests."""

from pathlib import Path

from mission_preflight.plan import build_plan

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_build_plan_dfr():
    plan = build_plan(EXAMPLES / "dfr-rapid-launch" / "mission.yaml")
    assert plan["mission_id"] == "lvmpd-dfr-rapid-001"
    assert plan["drone_count"] == 1


def test_build_plan_multi_drone_risks():
    plan = build_plan(EXAMPLES / "multi-drone-inspection" / "mission.yaml")
    assert plan["drone_count"] == 4
    assert any("deconfliction" in r.lower() for r in plan["risks"])
