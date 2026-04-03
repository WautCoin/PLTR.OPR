#!/usr/bin/env python3
"""PLTR.OPR - Operation Reporting CLI Tool"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STORAGE_FILE = Path(os.environ.get("OPR_STORAGE", "opr_data.json"))

STATUSES = ["open", "in_progress", "resolved", "closed"]


def _load() -> dict:
    if STORAGE_FILE.exists():
        with STORAGE_FILE.open() as f:
            return json.load(f)
    return {"reports": [], "next_id": 1}


def _save(data: dict) -> None:
    with STORAGE_FILE.open("w") as f:
        json.dump(data, f, indent=2)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find(data: dict, report_id: int) -> Optional[dict]:
    for report in data["reports"]:
        if report["id"] == report_id:
            return report
    return None


def cmd_create(args: argparse.Namespace) -> int:
    data = _load()
    report = {
        "id": data["next_id"],
        "title": args.title,
        "description": args.description or "",
        "status": "open",
        "severity": args.severity,
        "created_at": _now(),
        "updated_at": _now(),
    }
    data["reports"].append(report)
    data["next_id"] += 1
    _save(data)
    print(f"Created OPR-{report['id']}: {report['title']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    data = _load()
    reports = data["reports"]
    if args.status:
        reports = [r for r in reports if r["status"] == args.status]
    if not reports:
        print("No reports found.")
        return 0
    fmt = "{:<8} {:<12} {:<10} {:<30} {}"
    print(fmt.format("ID", "STATUS", "SEVERITY", "TITLE", "CREATED"))
    print("-" * 80)
    for r in reports:
        print(fmt.format(
            f"OPR-{r['id']}",
            r["status"],
            r.get("severity", "medium"),
            r["title"][:30],
            r["created_at"],
        ))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    data = _load()
    report = _find(data, args.id)
    if report is None:
        print(f"Error: OPR-{args.id} not found.", file=sys.stderr)
        return 1
    print(f"ID:          OPR-{report['id']}")
    print(f"Title:       {report['title']}")
    print(f"Status:      {report['status']}")
    print(f"Severity:    {report.get('severity', 'medium')}")
    print(f"Created:     {report['created_at']}")
    print(f"Updated:     {report['updated_at']}")
    if report.get("description"):
        print(f"Description:\n  {report['description']}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    data = _load()
    report = _find(data, args.id)
    if report is None:
        print(f"Error: OPR-{args.id} not found.", file=sys.stderr)
        return 1
    if args.title:
        report["title"] = args.title
    if args.description is not None:
        report["description"] = args.description
    if args.status:
        if args.status not in STATUSES:
            print(f"Error: status must be one of {STATUSES}", file=sys.stderr)
            return 1
        report["status"] = args.status
    if args.severity:
        report["severity"] = args.severity
    report["updated_at"] = _now()
    _save(data)
    print(f"Updated OPR-{report['id']}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    data = _load()
    report = _find(data, args.id)
    if report is None:
        print(f"Error: OPR-{args.id} not found.", file=sys.stderr)
        return 1
    data["reports"] = [r for r in data["reports"] if r["id"] != args.id]
    _save(data)
    print(f"Deleted OPR-{args.id}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:  # noqa: ARG001
    data = _load()
    reports = data["reports"]
    total = len(reports)
    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for r in reports:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_severity[r.get("severity", "medium")] = (
            by_severity.get(r.get("severity", "medium"), 0) + 1
        )
    print(f"Total reports: {total}")
    print("\nBy status:")
    for status in STATUSES:
        count = by_status.get(status, 0)
        print(f"  {status:<12} {count}")
    print("\nBy severity:")
    for severity in sorted(by_severity):
        print(f"  {severity:<12} {by_severity[severity]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opr",
        description="PLTR.OPR - Operation Reporting Tool",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new operation report")
    p_create.add_argument("title", help="Report title")
    p_create.add_argument("-d", "--description", help="Report description")
    p_create.add_argument(
        "-s", "--severity",
        default="medium",
        choices=["low", "medium", "high", "critical"],
        help="Severity level (default: medium)",
    )
    p_create.set_defaults(func=cmd_create)

    # list
    p_list = subparsers.add_parser("list", help="List operation reports")
    p_list.add_argument(
        "--status",
        choices=STATUSES,
        help="Filter by status",
    )
    p_list.set_defaults(func=cmd_list)

    # show
    p_show = subparsers.add_parser("show", help="Show report details")
    p_show.add_argument("id", type=int, help="Report ID")
    p_show.set_defaults(func=cmd_show)

    # update
    p_update = subparsers.add_parser("update", help="Update a report")
    p_update.add_argument("id", type=int, help="Report ID")
    p_update.add_argument("-t", "--title", help="New title")
    p_update.add_argument("-d", "--description", help="New description")
    p_update.add_argument("--status", choices=STATUSES, help="New status")
    p_update.add_argument(
        "--severity",
        choices=["low", "medium", "high", "critical"],
        help="New severity",
    )
    p_update.set_defaults(func=cmd_update)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a report")
    p_delete.add_argument("id", type=int, help="Report ID")
    p_delete.set_defaults(func=cmd_delete)

    # summary
    p_summary = subparsers.add_parser("summary", help="Show summary statistics")
    p_summary.set_defaults(func=cmd_summary)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
