"""CLI integration tests."""

from pathlib import Path

import pytest

from mission_preflight.cli import main


EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_plan_json(tmp_path):
    mission = EXAMPLES / "dfr-rapid-launch" / "mission.yaml"
    code = main(["plan", "--mission", str(mission), "--json"])
    assert code == 0


def test_run_and_doctor_dfr(tmp_path):
    out = tmp_path / "out"
    code = main(["run", "--input", str(EXAMPLES / "dfr-rapid-launch"), "--out", str(out)])
    assert code == 0
    receipts = list((out / "receipts").iterdir())
    assert len(receipts) == 1
    run_id = receipts[0].name
    code = main(["doctor", run_id, "--out", str(out), "--json"])
    assert code == 0


def test_doctor_blocked_waiver(tmp_path):
    out = tmp_path / "out"
    main(["run", "--input", str(EXAMPLES / "bvlos-waiver-block"), "--out", str(out)])
    run_id = next((out / "receipts").iterdir()).name
    code = main(["doctor", run_id, "--out", str(out)])
    assert code == 2


def test_report_writes_markdown(tmp_path):
    out = tmp_path / "out"
    main(["run", "--input", str(EXAMPLES / "dfr-rapid-launch"), "--out", str(out)])
    run_id = next((out / "receipts").iterdir()).name
    code = main(["report", run_id, "--out", str(out)])
    assert code == 0
    report = out / "receipts" / run_id / "report.md"
    assert report.exists()
    assert "Mission preflight report" in report.read_text()


def test_demo_command(tmp_path):
    out = tmp_path / "demo"
    code = main(["demo", "--out", str(out)])
    assert code == 0
    assert len(list((out / "receipts").iterdir())) == 3
