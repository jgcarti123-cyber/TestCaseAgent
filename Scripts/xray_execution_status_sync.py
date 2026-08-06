#!/usr/bin/env python3
"""Xray Cloud execution status sync (Pass/Fail per build).

Extends Traceability/requirement_traceability.json with, per Test issue,
which Test Execution(s) it ran in and its status (PASS/FAIL/EXECUTING/
TODO/ABORTED) in each. Answers the team's ask: "for a given build, which
tests are failing, and what bugs are attached to those failures."

IMPORTANT ARCHITECTURAL NOTE: pass/fail is NOT a static property of a
Test issue (e.g. NIV-1582). It's a property of that Test's *run* inside
a specific Test Execution - the same Test can pass in one build and fail
in the next. This script is organized around Test Executions, not Tests,
for that reason. If you only want "the latest build's" status, filter to
the most recent Test Execution by `created` date after fetching.

WHY A SEPARATE SCRIPT FROM jira_traceability_sync.py: Xray Cloud has its
own GraphQL API (https://xray.cloud.getxray.app/api/v2/graphql),
completely separate from Jira's REST API. It needs its own credentials -
a Client ID + Client Secret pair, generated from Xray's own UI at
https://xray.cloud.getxray.app/api-keys - NOT the Jira API token or
OAuth session used elsewhere in this project. This is confirmed against
the real Xray Cloud client source (github.com/jithinjosejacob/
xray-mcp-server, src/xray/cloud-client.ts) - auth endpoint, GraphQL
endpoint, and query shapes below are copied from working code, not
paraphrased from documentation.

WHAT IS NOT YET VERIFIED (no Xray credentials were available while
writing this - confirm on first real run, see NOTES below):
  - Whether `getTestExecution(issueId: ...)` / `getTest(issueId: ...)`
    accept a human-readable Jira key (e.g. "NIV-1582") directly, or
    require Xray's internal numeric issueId. Xray's public docs describe
    both being accepted in most Cloud GraphQL resolvers, but this has
    not been confirmed against this specific instance.
  - The exact JQL needed to scope getTestExecutions() to Intrusion Alert
    specifically - this project's Test Executions naming/tagging
    convention is unknown. Start broad (project = NIV AND type =
    "Test Execution") and narrow once you see real results.
  - Rate limits observed vs. documented (300 req/5min Standard, 1000
    req/5min Enterprise, per third-party research - not confirmed
    against this org's actual Xray license tier).

Usage:
    export XRAY_CLIENT_ID="..."
    export XRAY_CLIENT_SECRET="..."
    python xray_execution_status_sync.py --project NIV --feature NIO-F001

Output: merges into Traceability/requirement_traceability.json under
features.<feature>.linked_test_issues[].executions - does not overwrite
the bug/requirement data already there (see jira_traceability_sync.py
and the direct MCP pulls that populated the rest of this file).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

XRAY_BASE_URL = "https://xray.cloud.getxray.app/api/v2"
TRACEABILITY_PATH = Path(__file__).resolve().parent.parent / "Traceability" / "requirement_traceability.json"


def _get_client():
    try:
        import requests
    except ImportError:
        raise SystemExit("Needs the 'requests' package: pip install requests")
    return requests


def authenticate(requests_mod, client_id, client_secret):
    """POST /authenticate -> raw bearer token string, ~15min expiry.

    Verified shape from github.com/jithinjosejacob/xray-mcp-server
    src/xray/cloud-client.ts - response body IS the token (not wrapped
    in a JSON object with a "token" key).
    """
    resp = requests_mod.post(
        f"{XRAY_BASE_URL}/authenticate",
        json={"client_id": client_id, "client_secret": client_secret},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()
    if not isinstance(token, str):
        raise SystemExit(f"Unexpected /authenticate response shape: {token!r} - Xray may have changed its API")
    return token


def graphql(requests_mod, token, query, variables=None):
    resp = requests_mod.post(
        f"{XRAY_BASE_URL}/graphql",
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise SystemExit(f"Xray GraphQL error: {payload['errors']}")
    return payload["data"]


GET_TEST_EXECUTIONS_QUERY = """
query GetTestExecutions($jql: String!, $limit: Int) {
  getTestExecutions(jql: $jql, limit: $limit) {
    total
    results {
      issueId
      jira(fields: ["key", "summary", "created"])
    }
  }
}
"""

GET_TEST_EXECUTION_DETAIL_QUERY = """
query GetTestExecution($issueId: String!) {
  getTestExecution(issueId: $issueId) {
    issueId
    jira(fields: ["key", "summary", "status"])
    testRuns(limit: 100) {
      total
      results {
        test {
          issueId
          jira(fields: ["key"])
        }
        status {
          name
        }
        comment
      }
    }
  }
}
"""


def fetch_execution_status(requests_mod, token, project_key, jql_extra=None):
    """Fetch every Test Execution in a project, and every Test's status within each.

    Returns {test_key: [{execution_key, execution_summary, execution_created, status, comment}, ...]}
    """
    jql = f'project = {project_key} AND type = "Test Execution"'
    if jql_extra:
        jql += f" AND {jql_extra}"

    executions = graphql(requests_mod, token, GET_TEST_EXECUTIONS_QUERY, {"jql": jql, "limit": 100})
    exec_list = executions["getTestExecutions"]["results"]
    print(f"Found {len(exec_list)} Test Execution(s) matching: {jql}", file=sys.stderr)

    per_test = {}
    for exe in exec_list:
        exe_key = exe["jira"]["key"]
        exe_summary = exe["jira"].get("summary", "")
        exe_created = exe["jira"].get("created")

        detail = graphql(requests_mod, token, GET_TEST_EXECUTION_DETAIL_QUERY, {"issueId": exe["issueId"]})
        runs = detail["getTestExecution"]["testRuns"]["results"]

        for run in runs:
            test_key = run["test"]["jira"]["key"]
            per_test.setdefault(test_key, []).append({
                "execution_key": exe_key,
                "execution_summary": exe_summary,
                "execution_created": exe_created,
                "status": run["status"]["name"] if run.get("status") else None,
                "comment": run.get("comment"),
            })

    return per_test


def merge_into_traceability(per_test, feature_id):
    if not TRACEABILITY_PATH.exists():
        raise SystemExit(f"{TRACEABILITY_PATH} doesn't exist yet - run jira_traceability_sync.py or the live MCP pull first")

    with open(TRACEABILITY_PATH) as f:
        trace = json.load(f)

    feature = trace.get("features", {}).get(feature_id)
    if not feature:
        raise SystemExit(f"features.{feature_id} not found in {TRACEABILITY_PATH} - fetch its Jira/traceability data first")

    matched = 0
    for test_issue in feature.get("linked_test_issues", []):
        key = test_issue["key"]
        if key in per_test:
            test_issue["executions"] = per_test[key]
            matched += 1

    feature["execution_status_source"] = f"Xray Cloud GraphQL API, {datetime.now(timezone.utc).isoformat()}"

    with open(TRACEABILITY_PATH, "w") as f:
        json.dump(trace, f, indent=2, sort_keys=False)

    print(f"Matched execution data for {matched}/{len(feature.get('linked_test_issues', []))} Test issues in {feature_id}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Xray/Jira project key holding Test Executions (e.g. NIV)")
    parser.add_argument("--feature", required=True, help="Feature ID to merge results into, e.g. NIO-F001")
    parser.add_argument("--jql-extra", help='Extra JQL to narrow which Test Executions to fetch, e.g. \'summary ~ "Intrusion"\'')
    args = parser.parse_args()

    client_id = os.environ.get("XRAY_CLIENT_ID")
    client_secret = os.environ.get("XRAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Set XRAY_CLIENT_ID and XRAY_CLIENT_SECRET as environment variables first "
            "(generate at https://xray.cloud.getxray.app/api-keys). Never pass these as CLI args."
        )

    requests_mod = _get_client()
    token = authenticate(requests_mod, client_id, client_secret)
    per_test = fetch_execution_status(requests_mod, token, args.project, args.jql_extra)
    merge_into_traceability(per_test, args.feature)


if __name__ == "__main__":
    main()
