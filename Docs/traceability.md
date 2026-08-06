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

**Granularity finding — CORRECTED (later same day, 2026-08-06)**: the "no per-requirement linkage" conclusion below was wrong. It was based on a full-instance JQL text search for `"NIO-F0001"` returning zero hits — that search is unreliable; Jira's cross-project text index apparently doesn't reliably cover the `description` field. Direct reads of individual Test issues show requirement IDs ARE present, in the Test issue's free-text `description` field (not a dedicated custom field) — e.g. `NIV-1582`'s description is `"FFW_02_RA_FUN_0001, FFW_02_RA_GEN_0003, FFW_02_RA_FUN_0006, NIO-F0001_INT_REQ_001, NIO-F0001_INT_REQ_002, FFW_02_RA_GEN_0001"`. The separator between "NIO" and "F00NN" is inconsistent in the source data — sometimes a real hyphen, sometimes a stray U+0002 control character, sometimes no separator at all — so a naive text search misses most of them. Real traceability exists at **two levels**: Xray's **Parent-Child** link (Feature → Test issues, e.g. `NIF-117` "Intrusion Alert" → 40 Tests) for feature-level coverage, AND the requirement IDs embedded in each Test issue's `description` for per-requirement coverage. Coverage is coarse, though: Intrusion Alert's 40 Test issues collectively reference only 2 requirement IDs (`REQ_001`, `REQ_002`), not the fuller set (up to `REQ_014`) used in `Requirement_Docs/` — Jira's tagging is a subset of the local requirement-doc granularity, not a 1:1 mirror. `jira_traceability_sync.py`'s `_extract_requirement_ids` regex needs updating to parse the `description` field (with the separator-normalization above) rather than only `issuelinks`/CSV columns. Real per-requirement data for Intrusion Alert (NIO-F001) and Time Fencing Alert (NIO-F003) is now in `Traceability/requirement_traceability.json`'s `requirements` key.

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

## Granularity gap — decision (2026-08-06, revised later same day)

**Revised**: Jira *does* have per-requirement-line linkage, via the requirement IDs embedded in each Test issue's `description` field (see the corrected finding above) — the original "zero hits" search that drove this section's original conclusion was a false negative, not a true absence. The gap is narrower than first thought but still real: Jira's tagging is *coarse* relative to `Requirement_Docs/`. For Intrusion Alert, all 40 Test issues collectively cite only `NIO-F0001_INT_REQ_001` and `_002`, while `Generated_TestCases/` and `Requirement_Docs/` reference up to `_014`. So a requirement-line check against Jira today can confirm coverage for `_001`/`_002` but says nothing about `_004`, `_005`, `_009`, `_011`, `_014` etc. — Jira not mentioning them isn't evidence they're uncovered, just evidence Jira's tagging didn't capture that level of detail.

Three options were on the table: (a) request finer/more complete per-requirement-line linkage from Jira admins — most accurate, but blocked on org buy-in and timeline; (b) accept Jira's existing (coarse) per-requirement tagging as the ceiling with no finer check; (c) Jira per-requirement check **plus** semantic similarity against the real Jira Test issue summaries as a scenario-level dedup proxy, to catch coverage Jira's coarse tagging misses. **Chosen: (c)** — no admin dependency, usable immediately, and the real Test summaries pulled for both Intrusion Alert and Time Fencing Alert are exactly the corpus this needs.

This directly extends the embedding-similarity upgrade already flagged as a future item in `definition_of_done.md` Tier 1 gate #6 (originally scoped to local dedup against `Existing_TestCases/` only) — once built, it should check a generated test case's summary against **both** `Existing_TestCases/` rows **and** `requirement_traceability.json`'s `features.*.linked_test_issues` summaries. Not yet built; see `architecture.md`'s Coverage & Dedupe Checker stage for where this hooks in.

**Live signal already worth acting on, found by reading (not the crude keyword-overlap script — see chat history for why that approach produced false positives)**: `NIV-1586` ("no alert on authorized entry") reads as conceptually close to our `Test_91` (negative case). `NIV-1595` plus the door-handle cluster (`NIV-1602`–`1606`, `1619`–`1621`) reads as conceptually close to `Test_90` (happy path). Worth a human confirming before assuming duplication — a proper semantic check would be the reliable way to confirm at scale.

## Bug detail enrichment — severity, associated project, due date, comments (2026-08-06)

Direct team ask: for bugs linked to a feature, surface severity, associated project, a summary of comments, and fix due date — this is visible on the NIV board in Jira's UI, and is now pulled programmatically too.

**Field mapping, verified against live field metadata (`getJiraIssueTypeMetaWithFields` on the "Validation Bug" issue type in NIV) before writing anything — not assumed:**

| What the team asked for | Actual Jira field | Notes |
|---|---|---|
| Severity | `customfield_10854` ("Severity"), values `A`/`B`/`C` | A genuinely separate field from Priority — don't conflate the two. **Populated on only 3 of the 27 bugs linked to Intrusion Alert** — a real data-consistency gap in how the team files bugs, not a fetch failure. Treat a missing severity as unknown, not as implicitly low. |
| Associated project | `customfield_10721` ("Associated Project"), e.g. `N.IO T.OS`, `N.IO Hypercube`, `N.IO MAP2`, `Cyber Security` | Distinct from the Jira *project* (always `NIV` for these bugs) — this is which TML sub-team/system area owns the bug. Populated on all 27. |
| Fix due date | `duedate` (standard system field) | Populated on all 27. |
| Summary of comments | `comment` field (standard, full thread via `fields: ["comment"]`) | 25 of 27 bugs have at least one comment; fetched in full (author, timestamp, body). |

All 27 bugs for Intrusion Alert are enriched with these fields in `Traceability/requirement_traceability.json` under `features.NIO-F001.linked_bug_issues[]`. Comment bodies contain real personnel names/mentions — that data stays in the gitignored `Traceability/` artifact only, same as everything else pulled from Jira; this document intentionally doesn't quote any of it.

**Still pending**: the same enrichment for the other 26 bugs across the remaining 21 features once their traceability data is pulled.

## Execution status (Pass/Fail) — a genuinely separate system (2026-08-06)

Team also asked for per-build execution status (Passing/Failing), and for failing tests, the associated bug detail above. **This does not come from the same place.**

Confirmed two ways, not assumed: (1) a direct attempt to read it via the generic Atlassian/Jira MCP toolset found nothing — Test Execution issues exist (e.g. `NIV-14027`) but expose no pass/fail data through standard Jira fields; (2) research into Xray Cloud's actual architecture confirms why — Xray has its own separate GraphQL API (`https://xray.cloud.getxray.app/api/v2/graphql`), with its own credentials (a Client ID/Secret pair from Xray's own Global Settings → API Keys page, **not** the Jira OAuth already connected for everything else in this file).

**Architectural nuance worth understanding before using this data**: pass/fail is not a fixed property of a Test issue like `NIV-1582`. It's a property of that test's *run* inside a specific **Test Execution** (one per build). The same test can pass in build N and fail in build N+1 — this is exactly the regression-testing reality behind the item 2/3 dedup-exemption decision (`definition_of_done.md` gate #6): the same basic test genuinely needs re-running, and re-recording a result, every build.

**Built**: `Scripts/xray_execution_status_sync.py`. Grounded in real, working source code (the `cloud-client.ts` implementation from an open-source Xray MCP server — auth flow, endpoint, and GraphQL query shapes copied from tested code, not paraphrased from documentation that turned out to be behind a login wall). **Not yet run** — no Xray credentials were available while building it. Two things the script itself flags as unverified and to confirm on first real run: whether Xray's GraphQL accepts a Jira key directly as `issueId` or needs Xray's internal numeric ID, and what JQL actually scopes `getTestExecutions()` to one feature (naming/tagging convention for this team's Test Executions is unknown).

**Scope decision (2026-08-06)**: informational only for now — this data does not gate Coverage Checker or Reviewer logic, given the source is brand new and unverified against a real run. Revisit once `xray_execution_status_sync.py` has actually been run and the output's been sanity-checked.

**Deferred (2026-08-06)**: blocked on Xray admin access — the logged-in account (confirmed intentional, not a mistake) hit "You do not have access to Jira settings or Atlassian admin, contact your Jira admin to grant you access" when trying to reach Xray's Global Settings → API Keys page, which is where a Client ID/Secret gets generated. Team decision: don't pursue this further right now. `xray_execution_status_sync.py` stays built and ready — running it is just an admin-access problem to solve later, not a code problem. No further agent action needed on this until access is resolved.

## Expansion to 18 more features (2026-08-06)

Went from 2 features (Intrusion Alert, Time Fencing Alert — both with full per-test detail and requirement-line extraction) to 20, by mapping 18 more local `Existing_TestCases/` files to their Jira Feature issue by name and pulling **feature-level only** data (Test count + feature-level bug count via count-mode JQL) — not the same depth as the first two, since 18 features turned out to hold 272 Test issues collectively, and going per-test for all of them wasn't a reasonable scope for one pass.

**Key scheme note**: these 18 have no confirmed local `NIO-FXXX` ID (unlike `NIO-F001`/`NIO-F003`, which came from `Requirement_Docs/`), so `features.*` for these is keyed by the `Existing_TestCases/` filename instead — don't confuse this with a real requirement-doc-derived feature ID.

**Not guessed, left out**: `Auto Ecall` / `E-Call Manual` (Jira has two similarly-worded features under one parent — `NIF-215` "ECall (Manual)", `NIF-216` "Manual(Hard button press)/Auto eCall" — genuinely ambiguous which maps to which local file) and `RESS` / `B-Call SoftSwitch` (no matching Jira Feature found anywhere in the NIF project by keyword search). All four need a team member's confirmation of actual Jira terminology, not more searching.

## Scope decision

**Going forward only** — matches the item 2 schema decision. New/AI-generated test cases are checked against `requirement_traceability.json`; the 2,704 historical rows are not retroactively backfilled with Jira links as part of this pipeline (a separate, much larger project if the team wants it later).

## Output schema (actual, as written by the live MCP pull)

```json
{
  "generated_at": "<ISO 8601 timestamp>",
  "source": "csv | api | jira-mcp-live",
  "source_detail": "<file path, Jira project key, or MCP connection detail>",
  "requirements": {
    "NIO-F0001_INT_REQ_001": {"jira_keys": ["NIV-1582", "..."], "test_case_count": 40}
  },
  "features": {
    "<local_feature_id, e.g. NIO-F001>": {
      "feature_name": "...",
      "jira_feature_key": "NIF-117",
      "jira_feature_status": "...",
      "jira_parent_key": "NIF-45",
      "jira_project": "NIF",
      "test_project": "NIV",
      "test_case_count": 40,
      "linked_test_issues": [{
        "key": "NIV-1582", "issuetype": "Test", "status": "Open", "summary": "...",
        "executions": [{"execution_key": "...", "status": "PASS|FAIL|...", "comment": "..."}]
      }],
      "bug_count": 27,
      "linked_bug_issues": [{
        "key": "NIV-10594", "issuetype": "Validation Bug", "status": "Close", "summary": "...",
        "priority": "Highest", "severity": "A", "associated_project": "N.IO T.OS",
        "due_date": "2025-10-13", "fix_versions": [], "comment_count": 0, "comments": []
      }],
      "other_links": [{"key": "...", "type": "Relates", "issuetype": "Story", "status": "...", "summary": "..."}],
      "bug_field_source": "...", "execution_status_source": "..."
    }
  }
}
```

`requirements` (per-`REQ_NNN`) is real and populated for Intrusion Alert and Time Fencing Alert — see the correction above; kept in the schema for features where it's not yet been pulled (empty object, not fabricated). `features.*.linked_bug_issues[]` carries the severity/associated-project/due-date/comments enrichment (see below); `linked_test_issues[].executions` carries Xray pass/fail data once `xray_execution_status_sync.py` has actually been run (not yet, for any feature). The `Scripts/jira_traceability_sync.py` CSV/API paths still assume the old `requirements`-only shape (built before the granularity gap was known) — needs a matching update once the semantic-similarity piece is built, since it should probably produce this same `features` shape rather than the original `REQ_NNN` regex extraction, which doesn't match reality for Xray-based instances.

The Coverage Checker reads this alongside `Existing_TestCases/` and (once built) the semantic-similarity check — a feature with no Jira coverage and no local rows is a genuine gap worth generating for; a feature that already has both dense Jira coverage and a semantically-similar summary is a likely duplicate worth flagging before generation, not after.
