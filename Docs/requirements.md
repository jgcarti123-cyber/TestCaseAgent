# Requirements — Test Case Generation Pipeline

Living checklist of what the pipeline needs beyond the raw feature documents. Update status as items get resolved. See `architecture.md` for how these feed the 8-stage pipeline, `guardrails.md` for the accuracy rules these requirements exist to support.

## 1. Authoritative signal ground truth — ✅ DONE (2026-08-06)

Real `.dbc` file + Master Signal Catalog, not PDF-parsed tables.

- **Source files**: `Signal_Catalogs/TML_IVN_Communication_Matrix_CM_CANFD_V1.1.5_TM.dbc` (436 messages, 3,623 signals), `Signal_Catalogs/Master_Signal_Catalog_V4.4_20.8.25.xlsx` (VSS↔CAN cross-reference, 3,684 rows).
- **Built artifact**: `Signal_Catalogs/unified_signal_index.json` — cross-validated index, every entry flagged `bit_position_match: true/false`. This is what Signal Resolution queries; never re-derive from the raw PDFs.
- **Known gaps**: 345 residual catalog-vs-DBC discrepancies unresolved (see task #6), `DoorStateDrvr` naming ambiguity between message 748/946 unresolved (task #7), 1,375 DBC signals have no VSS mapping and therefore no entry in `unified_signal_index.json` at all (confirmed by direct count: 2,544 of 3,593 DBC signal names indexed, 70.8% coverage). **This gap has a real consequence, not just a documentation footnote** — see `guardrails.md` #2 and `Docs/definition_of_done.md` Tier 1 gate #2 for the two-source (index + raw DBC) verification rule it produced.

## 2. Machine-readable test case schema — ✅ DONE (2026-08-06)

- **Built artifact**: `Schema/test_case_schema.json` — formal JSON Schema, derived empirically from 2,704 rows across the 22 existing feature files, not guessed.
- **Key decisions** (see git/chat history for full reasoning):
  - `Environment` enum enforced (`LabCar`/`Vehicle`/`Bench`) for new rows only — 22 historical files keep their 6 inconsistent spellings, not retroactively fixed.
  - The two identically-named "Test Type" columns (execution method vs. validation scope) kept as-is, documented rather than renamed.
  - `Test Set Category` (Happy Path / Negative / Edge Case taxonomy) is now **required** for all new/AI-generated rows — it was empty in all 2,704 historical rows.
  - `CAN Signals Referenced` / `VSS Signals Referenced` columns adopted as the new standard schema for all future test cases, not just this pipeline.
- Validated against all 3 generated test cases with zero schema errors.

## 3. A "definition of done" rubric — ✅ DONE (2026-08-06)

- **Built artifact**: `Docs/definition_of_done.md` — two-tier rubric (Tier 1 hard gates, auto-checkable; Tier 2 quality checks, route to human on failure) plus a human-sign-off policy and status lifecycle (DRAFT → RELEASED / NEEDS_REVIEW / REJECTED).
- **Key decisions**: dedup via exact-field match now, embeddings noted as a future upgrade; Tier 2 failures route to human review rather than auto-reject; mandatory human sign-off for Edge Case categories + low-confidence tags only (Happy Path/Negative Case can auto-release); `SIGNAL NOT FOUND` hard-blocks release, no visible-flag exception.
- **Validated against the 3 existing test cases** — see the worked example table in `definition_of_done.md`. In the process, caught and corrected a false "fabricated signal" call on `Test_91` (the signal was real; the derived index was just incomplete) — this produced the two-source signal-verification rule now in Tier 1 gate #2 and a new entry in `guardrails.md` #2.
- **Refined 2026-08-06 (direct team feedback)**: dedup gate #6 was blanket — any resemblance to existing coverage blocked release. Corrected to be category-scoped: `Happy Path`/`Negative Case` matches are expected regression coverage and never block; only `Edge Case - *`/`User-Journey` matches block. See `guardrails.md` #6.

## 4. Requirement traceability data — 🟡 LIVE DATA PULLED FOR NIO-F001, GRANULARITY GAP FOUND (2026-08-06)

- **Finding**: all 2,704 rows across all 22 existing feature files have an empty Requirement ID column — zero local traceability data exists, not a subset. Confirmed by direct count, not assumed.
- **Source of truth**: Jira (team-confirmed). **Atlassian MCP connector is now set up and connected** (`jiratatamotors.atlassian.net`) — live-queried for Intrusion Alert on 2026-08-06, superseding the "no connector" status below.
- **Confirmed live**: Jira is on **Xray** (Test/Test Execution/Test Set issue types). Test cases ARE tagged with requirement IDs matching the local `NIO-F00NN_INT_REQ_NNN` scheme, but as free text inside each Test issue's `description` field (not a dedicated custom field) — e.g. `NIV-1582`'s description includes `NIO-F0001_INT_REQ_001, NIO-F0001_INT_REQ_002`. **Correction (later same day)**: an earlier pass here concluded this linkage didn't exist at all, based on a full-instance JQL text search for `"NIO-F0001"` returning zero hits — that search was a false negative (Jira's cross-project text index doesn't reliably cover `description`, and the separator between "NIO" and "F00NN" is inconsistent in the source data: real hyphen, a stray control character, or nothing). Direct reads of individual Test issues are the reliable path. Coverage is coarse, though — Intrusion Alert's 40 Test issues collectively cite only `REQ_001`/`REQ_002`, not the fuller set (up to `REQ_014`) in `Requirement_Docs/`. Xray's **Parent-Child** link (Feature → Test issues) additionally gives feature-level coverage.
- **Intrusion Alert in Jira**: Feature `NIF-117` ("Intrusion Alert", project NIF, child of `NIF-45` "Vehicle Alert"), status "Released to Internal Validation" — linked to 40 Test issues (`NIV-1582`–`NIV-1621`, project NIV, all status Open), tagged with `NIO-F0001_INT_REQ_001`/`_002`, and 27 closed Validation Bug issues via feature-level "Blocks" links (individual-Test-level bug links not yet checked for this feature). Full data in `Traceability/requirement_traceability.json` under `features.NIO-F001` and `requirements.*`.
- **Time Fencing Alert in Jira**: Feature `NIF-148` ("Time Fencing Alert (user defined)", project NIF, child of `NIF-45`), status "Under Development" — linked to 29 Test issues (`NIV-1512`–`NIV-1540`), tagged with `NIO-F0003_INT_REQ_001`/`_002`. 3 dependent bugs, all Closed: `NIV-10429`/`NIV-10619` (Highest priority, feature-linked, both "time fence alert not received after vehicle cranked during fenced duration" — same defect recurring across PAT rounds, see also unlinked `NIV-11793`, a third recurrence) and `NIV-13233` (linked to 25 of the 29 individual Test issues, not the Feature — "not able to set time fence alert [KPIT BENCH]"). A Test Execution issue exists (`NIV-14027`) but has no linked Tests and no accessible pass/fail data via this toolset. Full data under `features.NIO-F003`.
- **Built artifacts**: `Scripts/jira_traceability_sync.py` (CSV/API paths, still unrun against this instance, and its `_extract_requirement_ids` regex needs updating to parse the `description` field with separator normalization — currently only handles `issuelinks`/CSV columns), `Docs/traceability.md` (full design, now corrected).
- **Decision (2026-08-06)**: Jira per-requirement check (now confirmed real, but coarse) + semantic similarity against real Jira Test summaries to catch coverage Jira's coarse tagging misses — chosen over requesting finer/complete linkage from admins (blocked on org timeline) or accepting Jira's tagging as the ceiling with no finer check. See `traceability.md` → Granularity gap for the full reasoning.
- **Still needed to actually close this out**: the semantic-similarity piece itself isn't built yet (see `architecture.md` Coverage & Dedupe Checker stage); `Scripts/jira_traceability_sync.py` needs the description-parsing update above; individual-Test-level bug links unchecked for Intrusion Alert; unconfirmed for the other 20 features (2 of 22 now live-queried).
- **Scope**: going forward only, matches the item 2 decision — historical 2,704 rows are not being retroactively backfilled with Jira links as part of this pipeline.

## 5. Field/bug history feed — 🟡 ENRICHED FOR INTRUSION ALERT, INFORMATIONAL ONLY (2026-08-06)

The live Jira MCP pull for item 4 incidentally answered the base version of this — 27 closed Validation Bug issues linked to `NIF-117`. **Enriched same day, direct team ask**: each of the 27 now also carries `priority`, `severity` (Jira custom field `customfield_10854`, values A/B/C), `associated_project` (custom field `customfield_10721` — a TML sub-team/system area like "N.IO T.OS"/"N.IO Hypercube", distinct from the Jira project NIV which is constant across all of them), `due_date`, `fix_versions`, and full `comments` threads — all verified against live field metadata (`getJiraIssueTypeMetaWithFields`) before writing, not assumed field names. Sits in `Traceability/requirement_traceability.json` under `features.NIO-F001.linked_bug_issues`.

**Real data-quality finding, not a fetch failure**: `severity` is populated on only 3 of 27 bugs — most bugs in this project never had the field set despite it existing on the issue type. Don't treat a missing severity as "low severity"; it's an unknown, and the pipeline should say so rather than infer.

**Execution status (Passing/Failing) — separate system, script built, not yet run.** Team also asked for per-build Pass/Fail status. This does NOT live in standard Jira fields — confirmed both by a direct failed attempt to read it via the generic Jira MCP toolset, and by design: Xray Cloud has its own separate GraphQL API (`xray.cloud.getxray.app/api/v2`) with its own credentials (Client ID/Secret from Xray's own Global Settings, not the Jira OAuth already connected). Architecturally, pass/fail is a property of a **Test Execution** (a specific build run), not a fixed property of a Test issue — the same test can pass in one build and fail the next. `Scripts/xray_execution_status_sync.py` is built against real, verified Xray client source code (not paraphrased docs — the auth endpoint, GraphQL endpoint, and query shapes are copied from a working open-source Xray MCP server's implementation), but has not been run against this instance — no Xray credentials were available while building it. Decision: informational only for now, does not gate pipeline logic (team decision, 2026-08-06).

**Still pending**: this enrichment for the other 21 features; a designed pipeline step that actually consumes `linked_bug_issues` to propose edge cases (currently just data sitting in the JSON, not wired into Test Case Generator); running `xray_execution_status_sync.py` for the first time and confirming its two unverified assumptions (whether Xray's GraphQL accepts a Jira key directly as `issueId`, and the right JQL to scope Test Executions to one feature) — see the script's own docstring for the exact open questions. Standout bug examples worth generating test cases from: `NIV-6819` (alert timestamp shows UST while phone shows IST — a real timezone bug), `NIV-9610` (EV/PV cross-variant alert suppression), `NIV-6850` (duplicate/continuous alert firing — a debounce failure).

## 6. Test bench capability list — ⬜ PENDING

What can the physical LabCar/Vehicle/Bench rigs actually simulate/inject? No point generating a test case for a fault condition the lab can't produce.

## 7. Compliance/safety mapping — ⬜ PENDING

UNECE R155/ASIL classification for Intrusion Alert, if one exists, so test case severity/priority can reflect it.

## 8. A golden eval set — ⬜ PENDING

10–15 hand-reviewed, expert-approved test cases (can draw from the 2,704 existing rows) held out specifically to regression-test the pipeline whenever a prompt or document changes.
