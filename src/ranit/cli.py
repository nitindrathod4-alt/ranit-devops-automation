
"""Command-line interface for RANIT."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from ranit import __version__
from ranit.ai_analyzer import analyze_with_ai
from ranit.diagnose import MAX_LOG_BYTES, diagnose_log
from ranit.docker_health import check_docker_health
from ranit.health import check_project_health
from ranit.inspector import inspect_project
from ranit.logs import analyze_log
from ranit.scanner import scan_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranit",
        description="RANIT - a safety-first DevOps automation CLI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("doctor", help="Check local tools and show their availability.")

    analyze = subparsers.add_parser("analyze", help="Read project files and identify its stack.")
    analyze.add_argument("path", type=Path)
    analyze.add_argument("--json", action="store_true")

    scan = subparsers.add_parser("scan", help="Run a read-only heuristic security scan.")
    scan.add_argument("path", type=Path)
    scan.add_argument("--json", action="store_true")

    diagnose = subparsers.add_parser("diagnose", help="Suggest causes from a local log file.")
    diagnose.add_argument("log_file", type=Path)
    diagnose.add_argument("--json", action="store_true")
    diagnose.add_argument(
        "--ai",
        action="store_true",
        help="Analyze the log using the local Ollama AI model.",
    )

    logs = subparsers.add_parser("logs", help="Summarize severity and patterns in a log file.")
    logs.add_argument("log_file", type=Path)
    logs.add_argument("--json", action="store_true")

    health = subparsers.add_parser("health", help="Run read-only project health checks.")
    health.add_argument("path", type=Path)
    health.add_argument("--json", action="store_true")

    docker_health = subparsers.add_parser(
        "docker-health",
        help="Read Docker container status and health without changing containers.",
    )
    docker_health.add_argument("--json", action="store_true")

    subparsers.add_parser("init", help="Show the safe first-run setup checklist.")
    return parser


def _doctor() -> int:
    print("RANIT environment check")
    print("=======================")
    for command in ("python", "git", "docker", "terraform", "kubectl", "aws"):
        resolved = shutil.which(command)
        status = f"available: {resolved}" if resolved else "not found (optional for now)"
        print(f"{command:12} {status}")
    print("\nNo cloud resources were created or changed.")
    return 0


def _init() -> int:
    print("RANIT setup checklist")
    print("=====================")
    print("1. Use a project you own or are authorized to inspect.")
    print("2. Run: ranit analyze <project-folder>")
    print("3. Keep secrets out of source code and Git history.")
    print("4. AWS provisioning is not enabled in this initial release.")
    print("5. Never run unknown project scripts with administrator privileges.")
    return 0


def _render_report(report: dict[str, Any]) -> None:
    print(f"Project: {report['project_path']}")
    print(f"Exists:  {report['exists']}")
    print(f"Files scanned: {report['files_scanned']}")
    print("\nDetected markers:")
    for marker in report["markers"] or ["No common build/deployment markers found"]:
        print(f"  - {marker}")
    print("\nTop-level entries:")
    for entry in report["top_level_entries"] or ["(none)"]:
        print(f"  - {entry}")
    print("\nSafety note: this command only reads metadata; no code was executed.")


def _diagnose(args: argparse.Namespace) -> int:
    try:
        report = diagnose_log(args.log_file)

        if args.ai and report["exists"]:
            size = args.log_file.stat().st_size
            if size > MAX_LOG_BYTES:
                raise ValueError(
                    f"Log file is larger than the {MAX_LOG_BYTES}-byte safety limit."
                )

            log_text = args.log_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
            report["ai_analysis"] = analyze_with_ai(log_text)

    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Log: {report['log_path']}")
        print(f"Exists: {report['exists']}")
        print(f"Bytes read: {report['bytes_read']}")
        print("\nPossible diagnoses:")

        for item in report["diagnoses"]:
            print(f"  - {item['category']}")
            print(f"    Severity: {item.get('severity', 'Unknown')}")
            print(f"    Possible cause: {item['possible_cause']}")
            print(f"    Suggested checks: {item['suggested_checks']}")

        if not report["diagnoses"]:
            print("  No known patterns matched. Review the log manually.")

        summary = report.get("summary", {})
        print("\nSummary:")
        print(
            f"  Errors detected: "
            f"{summary.get('errors_detected', len(report['diagnoses']))}"
        )
        print(
            f"  Highest severity: "
            f"{summary.get('highest_severity', 'Unknown')}"
        )

        if args.ai and report.get("ai_analysis"):
            print("\nAI Analysis:")
            print(report["ai_analysis"])
            print("\nNote: Local rule-based and Ollama AI analysis completed.")
        else:
            print(f"\nNote: {report['note']}")

    return 0 if report["exists"] else 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()

    if args.command == "init":
        return _init()

    if args.command == "docker-health":
        report = check_docker_health()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("RANIT Docker Container Health Check")
            print("===================================")
            print(f"Docker CLI available: {report['available']}")

            if report["error"]:
                print(f"Error: {report['error']}")

            if report["containers"]:
                for container in report["containers"]:
                    print(f"\nName:   {container['name']}")
                    print(f"Image:  {container['image']}")
                    print(f"State:  {container['state']}")
                    print(f"Status: {container['status']}")
                    print(f"Health: {container['health']}")
            elif not report["error"]:
                print("No containers found.")

            print(f"\nNote: {report['note']}")

        return 0 if report["available"] and report["error"] is None else 1

    if args.command == "diagnose":
        return _diagnose(args)

    if args.command == "logs":
        try:
            report = analyze_log(args.log_file)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Log: {report['log_path']}")
            print(f"Exists: {report['exists']}")
            print(f"Bytes read: {report['bytes_read']}")
            print(f"Total lines: {report['total_lines']}")
            print("\nSeverity counts:")
            for severity, count in report["severity_counts"].items():
                print(f"  {severity}: {count}")
            print("\nPattern matches:")
            for item in report["matches"]:
                print(f"  Line {item['line']}: [{item['severity']}] {item['category']}")
            if not report["matches"]:
                print("  No known error patterns matched.")
            print(f"\nNote: {report['note']}")

        return 0 if report["exists"] else 2

    if args.command == "health":
        try:
            report = check_project_health(args.path)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Project: {report['project_path']}")
            print(f"Exists:  {report['exists']}")
            print(f"Status:  {report['status']}")
            print(f"Files scanned: {report.get('files_scanned', 0)}")
            print("\nDetected markers:")
            for marker in report.get("markers", []):
                print(f"  - {marker}")
            print("\nTool checks:")
            for check in report.get("checks", []):
                location = f" ({check['path']})" if check["path"] else ""
                print(f"  [{check['status'].upper()}] {check['tool']}{location}")
            print("\nIssues:")
            for issue in report.get("issues", []) or ["No issues detected by these checks."]:
                print(f"  - {issue}")
            print(f"\nNote: {report['note']}")

        return 0 if report.get("exists") and report.get("status") == "OK" else (
            2 if not report.get("exists") else 1
        )

    if args.command == "scan":
        try:
            report = scan_project(args.path)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Project: {report['project_path']}")
            print(f"Files scanned: {report['files_scanned']}")
            print(f"Dependency files: {len(report['dependency_files'])}")
            print(f"Deployment files: {len(report['deployment_files'])}")
            print("\nFindings:")
            for finding in report["findings"]:
                print(
                    f"  [{finding['severity']}] "
                    f"{finding['file']}:{finding['line']} - {finding['rule']}"
                )
            if not report["findings"]:
                print("  No matching heuristic patterns found.")
            print(f"\nNote: {report.get('note', 'No project files were changed.')}")

        return 0 if report["exists"] else 2

    if args.command == "analyze":
        try:
            report = inspect_project(args.path)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            _render_report(report)

        return 0 if report["exists"] else 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
