# Requirement Traceability — Test Case Generation Pipeline

Decided 2026-08-06. See `requirements.md` item 4 for status, `Scripts/jira_traceability_sync.py` for the tooling this describes.

## The finding that shaped this

Before designing anything, the local data was checked: **all 2,704 rows across all 22 existing feature test suites in `Existing_TestCases/` have an empty Requirement ID column.** Not partial — zero, everywhere, across every feature. Whatever traceability exists for this team has never been captured in these Excel files.

Team confirmed: the real system is **Jira**, with API access achievable. So this file exists to make that source usable by the pipeline, not to build a traceability system from scratch locally.

## What this changes for the pipeline

The Coverage & Dedupe Checker stage previously had only `Existing_TestCases/` (2,704 rows, zero requirement links) as its "already covered" reference. That's not enough — a requirement could already have a Jira-tracked test case that never made it into these Excel exports. Without checking Jira, the pipeline could confidently generate a "new" test case for a requirement that's already fully covered elsewhere, and have no way to know.

`requirement_traceability.json` (produced by the sync script, read by the Coverage Checker) closes that gap — for a given requirement ID, it answers "does Jira already show test coverage for this, independent of what's in our local Excel files?"

## Access status (as of 2026-08-06)

**No Jira MCP connector is set up in this environment.** It isn't in the list of connectors available-but-needing-authorization either — Jira integration doesn't exist here yet. Two consequences:

1. I can't query Jira directly from a Claude session right now. If you want that (recommended long-term), set up a Jira connector via `claude mcp` or connector settings in an interactive session — not something I can do on your behalf, and I won't ask you for an API token in chat to work around it.
2. Until that's set up, use the CSV path below. It needs no credentials shared with me at all.

## Path 1 — Manual CSV export (works today)

1. In Jira, run a JQL search covering the requirements/test-case issues you want traced. If test cases are tracked via a plugin (Xray, Zephyr Scale/Squad), search within that plugin's issue types.
2. Export the results as CSV, including at minimum:
   - **Issue key** (or "Key")
   - A column containing the requirement ID linkage — either a custom "Requirement ID" field (if your team's Jira has one matching the `NIO-F0001_INT_REQ_NNN` format), or Jira's default **Linked Issues** export column.
3. Run:
   ```
   python Scripts/jira_traceability_sync.py --from-csv path/to/export.csv
   ```
4. This writes `Traceability/requirement_traceability.json` (gitignored — this is your team's project data, stays local like `Signal_Catalogs/` and `Existing_TestCases/`).

**Tested against a synthetic sample CSV during this build** (4 rows, 3 recognizable requirement IDs) — parsing logic is verified. Not yet run against a real Jira export, since none was available.

## Path 2 — Live API sync (once Jira access is set up)

```
export JIRA_BASE_URL="https://yourteam.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="..."
python Scripts/jira_traceability_sync.py --from-api --project NIO
```

**Written against the documented Jira REST API v3 shape, not yet run against a live instance** — no Jira access was available while building this. Before trusting it in the pipeline: dry-run against a real (ideally test) project and confirm the output looks right. One known gap: if requirement linkage lives in an Xray/Zephyr-specific field rather than plain Jira `issuelinks`, the current script won't see it — that needs a small extension once you confirm which plugin (if any) is in use.

## Information to gather from your Jira admin before either path is fully reliable

- Project key(s) that hold Intrusion Alert (and other feature) work
- Whether test cases are tracked as plain Jira issues, or via Xray/Zephyr/another plugin
- The exact field or link type that connects a requirement to its test case(s) — custom field, issue link type ("Tests"/"is tested by"), or something plugin-specific
- Whether historical Jira data can be backfilled with the `NIO-F0001_INT_REQ_NNN`-format IDs used in `Requirement_Docs/`, or whether Jira uses its own different requirement ID scheme that needs a mapping table

## Scope decision

**Going forward only** — matches the item 2 schema decision. New/AI-generated test cases are checked against `requirement_traceability.json`; the 2,704 historical rows are not retroactively backfilled with Jira links as part of this pipeline (a separate, much larger project if the team wants it later).

## Output schema

```json
{
  "generated_at": "<ISO 8601 timestamp>",
  "source": "csv | api",
  "source_detail": "<file path or Jira project key>",
  "requirements": {
    "<requirement_id>": {
      "jira_keys": ["NIO-201", "NIO-202"],
      "test_case_count": 2
    }
  }
}
```

The Coverage Checker reads this alongside `Existing_TestCases/` — a requirement absent from *both* is a genuine coverage gap worth generating a test case for; present in either is not.
