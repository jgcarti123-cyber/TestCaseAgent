# Requirement Traceability — Test Case Generation Pipeline

Decided 2026-08-06. See `requirements.md` item 4 for status, `Scripts/jira_traceability_sync.py` for the tooling this describes.

## The finding that shaped this

Before designing anything, the local data was checked: **all 2,704 rows across all 22 existing feature test suites in `Existing_TestCases/` have an empty Requirement ID column.** Not partial — zero, everywhere, across every feature. Whatever traceability exists for this team has never been captured in these Excel files.

Team confirmed: the real system is **Jira**, with API access achievable. So this file exists to make that source usable by the pipeline, not to build a traceability system from scratch locally.

## What this changes for the pipeline

The Coverage & Dedupe Checker stage previously had only `Existing_TestCases/` (2,704 rows, zero requirement links) as its "already covered" reference. That's not enough — a requirement could already have a Jira-tracked test case that never made it into these Excel exports. Without checking Jira, the pipeline could confidently generate a "new" test case for a requirement that's already fully covered elsewhere, and have no way to know.

`requirement_traceability.json` (produced by the sync script, read by the Coverage Checker) closes that gap — for a given requirement ID, it answers "does Jira already show test coverage for this, independent of what's in our local Excel files?"

## Access status (as of 2026-08-06)

**Update, later same day**: the Atlassian MCP connector was set up and connected (`jiratatamotors.atlassian.net`) and used to live-query Jira for Intrusion Alert — see the finding below and `Traceability/requirement_traceability.json`. The "no connector" state described in the rest of this section no longer applies; kept below for history since the CSV/API paths are still valid fallbacks.

**Granularity finding (important, changes the design below)**: Jira is on Xray. There is no field or literal text anywhere in the instance matching the local `NIO-F0001_INT_REQ_NNN` requirement-ID scheme — confirmed via a JQL text search for `"NIO-F0001"` across all projects (zero hits). Real traceability exists via Xray's **Parent-Child** issue link from a **Feature**-type issue (e.g. `NIF-117` "Intrusion Alert") down to individual **Test**-type issues — i.e. one level of granularity coarser than assumed below. The Coverage Checker design (and `jira_traceability_sync.py`'s `_extract_requirement_ids` regex) should be revisited: it currently expects to find `REQ_NNN`-shaped tokens in Jira text/links, which don't exist. A feature-level check ("does Jira show *any* test coverage for this feature") is achievable today; a requirement-line-level check is not, without a team decision to add that linkage in Jira.

~~**No Jira MCP connector is set up in this environment.**~~ (superseded, see above) It isn't in the list of connectors available-but-needing-authorization either — Jira integration doesn't exist here yet. Two consequences:

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

## Information to gather from your Jira admin — RESOLVED (2026-08-06) for Intrusion Alert

- ~~Project key(s) that hold Intrusion Alert (and other feature) work~~ → **Confirmed**: Feature issues in `NIF` (N.IO Feature), Test issues in `NIV` (N.IO Validation). `NIO-F001` = Jira `NIF-117`, child of `NIF-45` "Vehicle Alert".
- ~~Whether test cases are tracked as plain Jira issues, or via Xray/Zephyr~~ → **Confirmed**: Xray. Test-type issues, not plain issues.
- ~~The exact field or link type that connects a requirement to its test case(s)~~ → **Confirmed**: Xray **Parent-Child** link, Feature → Test, at **feature granularity only** — see the granularity gap below.
- **Still open**: whether historical Jira data can be backfilled with `NIO-F0001_INT_REQ_NNN`-format IDs. Unlikely to matter now — see the decision below, which doesn't depend on this.

Still unconfirmed for the other 21 connected-car features — the above was only checked for Intrusion Alert. Re-run the same live-MCP query per feature as the pipeline expands.

## Granularity gap — decision (2026-08-06)

Jira has no per-requirement-line linkage — a JQL text search for `"NIO-F0001"` across the entire instance returned zero hits, confirming the `NIO-F0001_INT_REQ_NNN` scheme used in `Requirement_Docs/` doesn't exist anywhere in Jira. Traceability tops out at **feature level**: "does this feature have Jira-tracked test coverage at all," not "is this specific requirement line covered."

Three options were on the table: (a) request per-requirement-line linkage from Jira admins — most accurate, but blocked on org buy-in and timeline; (b) accept feature-level as the ceiling with no finer check; (c) feature-level check **plus** semantic similarity against the real Jira Test issue summaries as a scenario-level dedup proxy. **Chosen: (c)** — no admin dependency, usable immediately, and the 40 real Test summaries pulled for Intrusion Alert are exactly the corpus this needs.

This directly extends the embedding-similarity upgrade already flagged as a future item in `definition_of_done.md` Tier 1 gate #6 (originally scoped to local dedup against `Existing_TestCases/` only) — once built, it should check a generated test case's summary against **both** `Existing_TestCases/` rows **and** `requirement_traceability.json`'s `features.*.linked_test_issues` summaries. Not yet built; see `architecture.md`'s Coverage & Dedupe Checker stage for where this hooks in.

**Live signal already worth acting on, found by reading (not the crude keyword-overlap script — see chat history for why that approach produced false positives)**: `NIV-1586` ("no alert on authorized entry") reads as conceptually close to our `Test_91` (negative case). `NIV-1595` plus the door-handle cluster (`NIV-1602`–`1606`, `1619`–`1621`) reads as conceptually close to `Test_90` (happy path). Worth a human confirming before assuming duplication — a proper semantic check would be the reliable way to confirm at scale.

## Scope decision

**Going forward only** — matches the item 2 schema decision. New/AI-generated test cases are checked against `requirement_traceability.json`; the 2,704 historical rows are not retroactively backfilled with Jira links as part of this pipeline (a separate, much larger project if the team wants it later).

## Output schema (actual, as written by the live MCP pull)

```json
{
  "generated_at": "<ISO 8601 timestamp>",
  "source": "csv | api | jira-mcp-live",
  "source_detail": "<file path, Jira project key, or MCP connection detail>",
  "requirements": {},
  "features": {
    "<local_feature_id, e.g. NIO-F001>": {
      "feature_name": "...",
      "jira_feature_key": "NIF-117",
      "jira_feature_status": "...",
      "jira_parent_key": "NIF-45",
      "jira_project": "NIF",
      "test_project": "NIV",
      "test_case_count": 40,
      "linked_test_issues": [{"key": "NIV-1582", "issuetype": "Test", "status": "Open", "summary": "..."}],
      "bug_count": 27,
      "linked_bug_issues": [{"key": "NIV-10594", "issuetype": "Validation Bug", "status": "Close", "summary": "..."}],
      "other_links": [{"key": "...", "type": "Relates", "issuetype": "Story", "status": "...", "summary": "..."}]
    }
  }
}
```

`requirements` (per-`REQ_NNN`) is kept in the schema but intentionally left empty — no fabricated Test→REQ_NNN mapping. `features` is the real, populated structure given the granularity finding above. The `Scripts/jira_traceability_sync.py` CSV/API paths still assume the old `requirements`-only shape (built before the granularity gap was known) — needs a matching update once the semantic-similarity piece is built, since it should probably produce this same `features` shape rather than the original `REQ_NNN` regex extraction, which doesn't match reality for Xray-based instances.

The Coverage Checker reads this alongside `Existing_TestCases/` and (once built) the semantic-similarity check — a feature with no Jira coverage and no local rows is a genuine gap worth generating for; a feature that already has both dense Jira coverage and a semantically-similar summary is a likely duplicate worth flagging before generation, not after.
