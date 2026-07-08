"""Doctor integration tests."""

from pathlib import Path

from mission_preflight.doctor import diagnose_receipt
from mission_preflight.run_module import execute_run

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_dfr_cleared(tmp_path):
    result = execute_run(EXAMPLES / "dfr-rapid-launch", tmp_path)
    doc = diagnose_receipt(Path(result["receipt_dir"]))
    assert doc["overall_status"] == "cleared"
    assert doc["launch_recommendation"] == "go"


def test_multi_drone_caution(tmp_path):
    result = execute_run(EXAMPLES / "multi-drone-inspection", tmp_path)
    doc = diagnose_receipt(Path(result["receipt_dir"]))
    assert doc["overall_status"] == "caution"
    assert doc["launch_recommendation"] == "review"


def test_waiver_blocked(tmp_path):
    result = execute_run(EXAMPLES / "bvlos-waiver-block", tmp_path)
    doc = diagnose_receipt(Path(result["receipt_dir"]))
    assert doc["overall_status"] == "blocked"
    signals = {c["signal"]: c["status"] for c in doc["checks"]}
    assert signals["waiver_altitude"] == "fail"
