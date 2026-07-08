"""mission-preflight CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mission_preflight.doctor import diagnose_receipt, resolve_receipt
from mission_preflight.plan import build_plan
from mission_preflight.report import write_report
from mission_preflight.run_module import execute_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mission-preflight",
        description="Plan, run, doctor, and report on BVLOS / multi-drone mission preflight.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan", help="Build preflight plan from mission YAML")
    plan_p.add_argument("--mission", type=Path, required=True, help="Path to mission.yaml")
    plan_p.add_argument("--rules", type=Path, default=None, help="Optional rules.yaml")
    plan_p.add_argument("--json", action="store_true", dest="as_json")
    plan_p.set_defaults(handler=_cmd_plan)

    run_p = sub.add_parser("run", help="Ingest mission scenario into receipt bundle")
    run_p.add_argument("--input", type=Path, required=True, help="Scenario directory")
    run_p.add_argument("--out", type=Path, default=Path("out"), help="Output root")
    run_p.add_argument("--label", type=str, default=None, help="Run label suffix")
    run_p.add_argument("--rules", type=Path, default=None)
    run_p.add_argument("--json", action="store_true", dest="as_json")
    run_p.set_defaults(handler=_cmd_run)

    doc_p = sub.add_parser("doctor", help="Diagnose a receipt bundle")
    doc_p.add_argument("receipt", help="Receipt dir or run id under --out")
    doc_p.add_argument("--out", type=Path, default=Path("out"))
    doc_p.add_argument("--json", action="store_true", dest="as_json")
    doc_p.set_defaults(handler=_cmd_doctor)

    rep_p = sub.add_parser("report", help="Write Markdown report from doctor output")
    rep_p.add_argument("receipt", help="Receipt dir or run id")
    rep_p.add_argument("--out", type=Path, default=Path("out"))
    rep_p.add_argument("--output", type=Path, default=None)
    rep_p.set_defaults(handler=_cmd_report)

    demo_p = sub.add_parser("demo", help="Run bundled mock scenarios (60s demo)")
    demo_p.add_argument("--out", type=Path, default=Path("out/demo"))
    demo_p.set_defaults(handler=_cmd_demo)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_plan(args: argparse.Namespace) -> int:
    plan = build_plan(args.mission, args.rules)
    if args.as_json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"Mission: {plan['mission_id']}")
        print(f"Operation: {plan['operation']}")
        print(f"Waiver: {plan['waiver_profile']}")
        print(f"Drones: {plan['drone_count']}")
        if plan["risks"]:
            print("Risks:")
            for risk in plan["risks"]:
                print(f"  - {risk}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    result = execute_run(args.input, args.out, label=args.label, rules_path=args.rules)
    rdir = Path(result["receipt_dir"])
    diagnose_receipt(rdir)
    write_report(rdir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"run_id: {result['run_id']}")
        print(f"receipt: {result['receipt_dir']}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    rdir = resolve_receipt(args.receipt, args.out)
    result = diagnose_receipt(rdir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"overall: {result['overall_status']}")
        print(f"launch: {result['launch_recommendation']}")
        for check in result["checks"]:
            print(f"  [{check['status']}] {check['signal']}: {check['message']}")
    return 2 if result["overall_status"] == "blocked" else 0


def _cmd_report(args: argparse.Namespace) -> int:
    rdir = resolve_receipt(args.receipt, args.out)
    path = write_report(rdir, args.output)
    print(path)
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    examples = Path(__file__).resolve().parent.parent / "examples"
    scenarios = (
        "dfr-rapid-launch",
        "multi-drone-inspection",
        "bvlos-waiver-block",
    )
    for name in scenarios:
        inp = examples / name
        run_result = execute_run(inp, args.out, label=name)
        rdir = Path(run_result["receipt_dir"])
        doc = diagnose_receipt(rdir)
        write_report(rdir)
        print(f"{name}: {doc['overall_status']} ({doc['launch_recommendation']}) → {rdir}")
    print(f"\nDemo complete. Receipts under {args.out}/receipts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
