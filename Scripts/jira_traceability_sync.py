#!/usr/bin/env python3
"""Jira <-> local requirement traceability sync.

Produces Traceability/requirement_traceability.json - the artifact the
Coverage Checker pipeline stage reads to know which requirement IDs
already have a Jira-tracked test case, independent of Existing_TestCases/
(which has zero Requirement ID coverage across all 2,704 rows - see
Docs/requirements.md item 4 and Docs/traceability.md for why this script
exists at all).

Two ways to populate the artifact, both producing the identical output
schema so the Coverage Checker doesn't care which path was used:

  1) From a manual Jira CSV export (works today, no API access needed).
     In Jira: run your saved search / JQL, then Export > CSV, including
     at minimum the "Issue key" and "Summary" columns, plus whichever
     column holds the requirement linkage - either a custom
     "Requirement ID" field matching the NIO-F0001_INT_REQ_NNN pattern,
     or Jira's default "Linked Issues" export column. See
     Docs/traceability.md for exactly what to ask your Jira admin for.

       python jira_traceability_sync.py --from-csv path/to/export.csv

  2) From the Jira REST API directly, once access is set up. Requires
     JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN as environment
     variables - never pass these as CLI arguments (they'd land in
     shell history) and never hardcode them in this file.

       export JIRA_BASE_URL="https://yourteam.atlassian.net"
       export JIRA_EMAIL="you@company.com"
       export JIRA_API_TOKEN="..."
       python jira_traceability_sync.py --from-api --project NIO

     NOTE: this path is written against the documented Jira REST API v3
     shape but has not been run against a live instance in this
     project yet (no Jira access was available while building it).
     Dry-run against a test project before trusting it in the pipeline.

Output schema (Traceability/requirement_traceability.json):
{
  "generated_at": "<ISO 8601 timestamp>",
  "source": "csv" | "api",
  "source_detail": "<file path or Jira project key>",
  "requirements": {
    "<requirement_id>": {
      "jira_keys": ["PROJ-123", ...],
      "test_case_count": <int>
    },
    ...
  }
}
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REQUIREMENT_ID_PATTERN = re.compile(r"[A-Z]{2,6}-F\d{3,4}_[A-Z]{2,6}_REQ_\d{1,4}")

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "Traceability" / "requirement_traceability.json"


def _extract_requirement_ids(text):
    """Pull every requirement-ID-shaped token out of a free-text field.

    Handles both a dedicated "Requirement ID" column (may contain a
    semicolon-separated list, matching the local schema's convention)
    and requirement IDs embedded inside a Jira "Linked Issues" export
    cell (e.g. "is tested by NIO-F0001_INT_REQ_004").
    """
    if not text:
        return []
    return sorted(set(REQUIREMENT_ID_PATTERN.findall(text)))


def build_from_csv(csv_path, req_id_columns=("Requirement ID", "Linked Issues", "Custom field (Requirement ID)")):
    """Parse a manually-exported Jira CSV into the traceability structure.

    req_id_columns: tried in order; first column present in the CSV
    header that contains at least one requirement-ID-shaped token wins
    per row. Adjust this tuple (or pass --req-id-column) once your
    team's actual export column name is confirmed - see
    Docs/traceability.md.
    """
    requirements = defaultdict(lambda: {"jira_keys": set(), "test_case_count": 0})
    rows_seen = 0
    rows_with_requirement = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no header row - can't identify columns")

        key_col = next((c for c in reader.fieldnames if c.strip().lower() in ("issue key", "key")), None)
        if key_col is None:
            raise ValueError(
                f"No 'Issue key' / 'Key' column found in {csv_path}. "
                f"Columns present: {reader.fieldnames}"
            )

        for row in reader:
            rows_seen += 1
            issue_key = (row.get(key_col) or "").strip()
            if not issue_key:
                continue

            found_ids = []
            for col in req_id_columns:
                if col in row and row[col]:
                    found_ids = _extract_requirement_ids(row[col])
                    if found_ids:
                        break

            if found_ids:
                rows_with_requirement += 1
            for rid in found_ids:
                requirements[rid]["jira_keys"].add(issue_key)

    for rid, data in requirements.items():
        data["test_case_count"] = len(data["jira_keys"])
        data["jira_keys"] = sorted(data["jira_keys"])

    print(
        f"Parsed {rows_seen} rows from {csv_path}: "
        f"{rows_with_requirement} had a recognizable requirement ID, "
        f"covering {len(requirements)} distinct requirements.",
        file=sys.stderr,
    )
    return dict(requirements), str(csv_path)


def build_from_api(project_key, jql_extra=None):
    """Query Jira's REST API v3 directly for issues + their requirement links.

    UNVERIFIED against a live Jira instance (see module docstring).
    Written against the documented v3 search + issuelinks shape;
    confirm field names against your actual instance before relying
    on this in the pipeline - in particular, if you're on Xray or
    Zephyr, requirement linkage may live in a plugin-specific field
    rather than plain Jira issuelinks, and this function does not
    handle that case yet.
    """
    try:
        import requests
    except ImportError:
        raise SystemExit(
            "The --from-api path needs the 'requests' package: pip install requests"
        )

    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not all([base_url, email, token]):
        raise SystemExit(
            "Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN as environment "
            "variables before using --from-api. Never pass these as CLI args."
        )

    jql = f"project = {project_key}"
    if jql_extra:
        jql += f" AND {jql_extra}"

    requirements = defaultdict(lambda: {"jira_keys": set(), "test_case_count": 0})
    start_at = 0
    page_size = 100

    while True:
        resp = requests.get(
            f"{base_url.rstrip('/')}/rest/api/3/search",
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": "summary,issuelinks",
            },
            auth=(email, token),
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        for issue in payload.get("issues", []):
            key = issue["key"]
            summary = issue.get("fields", {}).get("summary", "") or ""
            found_ids = _extract_requirement_ids(summary)

            for link in issue.get("fields", {}).get("issuelinks", []):
                linked = link.get("outwardIssue") or link.get("inwardIssue")
                if linked:
                    linked_summary = linked.get("fields", {}).get("summary", "") or ""
                    found_ids += _extract_requirement_ids(linked_summary)
                    found_ids += _extract_requirement_ids(linked.get("key", ""))

            for rid in set(found_ids):
                requirements[rid]["jira_keys"].add(key)

        total = payload.get("total", 0)
        start_at += page_size
        if start_at >= total:
            break

    for rid, data in requirements.items():
        data["test_case_count"] = len(data["jira_keys"])
        data["jira_keys"] = sorted(data["jira_keys"])

    return dict(requirements), project_key


def write_output(requirements, source, source_detail):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "source_detail": source_detail,
        "requirements": requirements,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(f"Wrote {len(requirements)} requirement entries to {OUTPUT_PATH}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-csv", metavar="PATH", help="Path to a manually-exported Jira CSV")
    group.add_argument("--from-api", action="store_true", help="Query the Jira REST API (needs env vars, see docstring)")
    parser.add_argument("--project", help="Jira project key, required with --from-api")
    parser.add_argument("--req-id-column", help="Override which CSV column to read requirement IDs from")
    args = parser.parse_args()

    if args.from_csv:
        cols = (args.req_id_column,) if args.req_id_column else None
        kwargs = {"req_id_columns": cols} if cols else {}
        requirements, detail = build_from_csv(args.from_csv, **kwargs)
        write_output(requirements, "csv", detail)
    else:
        if not args.project:
            parser.error("--from-api requires --project")
        requirements, detail = build_from_api(args.project)
        write_output(requirements, "api", detail)


if __name__ == "__main__":
    main()
