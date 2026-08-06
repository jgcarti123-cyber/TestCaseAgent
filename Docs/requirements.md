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

## 4. Requirement traceability data — 🟡 LIVE DATA PULLED FOR NIO-F001, GRANULARITY GAP FOUND (2026-08-06)

- **Finding**: all 2,704 rows across all 22 existing feature files have an empty Requirement ID column — zero local traceability data exists, not a subset. Confirmed by direct count, not assumed.
- **Source of truth**: Jira (team-confirmed). **Atlassian MCP connector is now set up and connected** (`jiratatamotors.atlassian.net`) — live-queried for Intrusion Alert on 2026-08-06, superseding the "no connector" status below.
- **Confirmed live**: Jira is on **Xray** (Test/Test Execution/Test Set issue types). Test cases are NOT tracked via a plain "Requirement ID" text field or via the local `NIO-F0001_INT_REQ_NNN` scheme — a JQL text search for `"NIO-F0001"` across the entire instance returned zero hits. Real traceability exists via Xray's **Parent-Child** issue link from the Feature issue down to individual Test issues — i.e. at **feature granularity, not individual-requirement-line granularity**.
- **Intrusion Alert in Jira**: Feature `NIF-117` ("Intrusion Alert", project NIF, child of `NIF-45` "Vehicle Alert"), status "Released to Internal Validation" — linked to 40 Test issues (`NIV-1582`–`NIV-1621`, project NIV, all status Open) and 27 closed Validation Bug issues via "Blocks" links. Full data in `Traceability/requirement_traceability.json` under `features.NIO-F001`.
- **Built artifacts**: `Scripts/jira_traceability_sync.py` (CSV/API paths, still unrun against this instance — superseded for this feature by the direct MCP pull above), `Docs/traceability.md` (full design, now needs a follow-up note on the granularity gap).
- **Decision (2026-08-06)**: feature-level Jira check + semantic similarity against real Jira Test summaries — chosen over requesting per-requirement-line linkage from admins (blocked on org timeline) or accepting feature-level-only with no finer check. No admin dependency; usable today. See `traceability.md` → Granularity gap for the full reasoning.
- **Still needed to actually close this out**: the semantic-similarity piece itself isn't built yet (see `architecture.md` Coverage & Dedupe Checker stage); `Scripts/jira_traceability_sync.py`'s CSV/API paths still assume the old `REQ_NNN`-per-requirement shape and need updating to match the real `features` structure; unconfirmed for the other 21 features (only Intrusion Alert has been live-queried so far).
- **Scope**: going forward only, matches the item 2 decision — historical 2,704 rows are not being retroactively backfilled with Jira links as part of this pipeline.

## 5. Field/bug history feed — 🟡 PARTIAL DATA FOR INTRUSION ALERT (2026-08-06)

The same live Jira MCP pull for item 4 incidentally answered this too — 27 closed Validation Bug issues linked to `NIF-117`, now sitting in `Traceability/requirement_traceability.json` under `features.NIO-F001.linked_bug_issues`. Not yet used systematically (no automated "turn closed bugs into edge-case candidates" step exists in the pipeline), but real data, not a placeholder. Standout examples worth generating test cases from: `NIV-6819` (alert timestamp shows UST while phone shows IST — a real timezone bug), `NIV-9610` (EV/PV cross-variant alert suppression), `NIV-6850` (duplicate/continuous alert firing — a debounce failure).

**Still pending**: this for the other 21 features, and a designed step in the pipeline that actually consumes `linked_bug_issues` to propose edge cases (currently just data sitting in the JSON, not wired into Test Case Generator).

## 6. Test bench capability list — ⬜ PENDING

What can the physical LabCar/Vehicle/Bench rigs actually simulate/inject? No point generating a test case for a fault condition the lab can't produce.

## 7. Compliance/safety mapping — ⬜ PENDING

UNECE R155/ASIL classification for Intrusion Alert, if one exists, so test case severity/priority can reflect it.

## 8. A golden eval set — ⬜ PENDING

10–15 hand-reviewed, expert-approved test cases (can draw from the 2,704 existing rows) held out specifically to regression-test the pipeline whenever a prompt or document changes.
