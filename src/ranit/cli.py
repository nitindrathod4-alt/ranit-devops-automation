"""Command-line interface for RANIT."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from ranit import __version__
from ranit.inspector import inspect_project
from ranit.scanner import scan_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranit",
        description="RANIT — a safety-first DevOps automation CLI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local tools and show their availability.")

    analyze = subparsers.add_parser("analyze", help="Read project files and identify its stack.")
    analyze.add_argument("path", type=Path, help="Path to a local project directory.")
    analyze.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    scan = subparsers.add_parser("scan", help="Run a read-only heuristic security scan.")
    scan.add_argument("path", type=Path, help="Path to a local project directory.")
    scan.add_argument("--json", action="store_true", help="Print machine-readable JSON")

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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "init":
        return _init()
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
                print(f"  [{finding['severity']}] {finding['file']}:{finding['line']} — {finding['rule']}")
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
