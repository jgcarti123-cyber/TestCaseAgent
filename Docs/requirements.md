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

## 4. Requirement traceability data — 🟡 TOOLING BUILT, NOT YET CLOSED (2026-08-06)

- **Finding**: all 2,704 rows across all 22 existing feature files have an empty Requirement ID column — zero local traceability data exists, not a subset. Confirmed by direct count, not assumed.
- **Source of truth**: Jira (team-confirmed), API access achievable. **No Jira MCP connector is set up in this environment yet** — nothing was queried live.
- **Built artifacts**: `Scripts/jira_traceability_sync.py` (CSV-export path tested against a synthetic sample; live-API path written against the documented Jira REST API v3 shape but not run against a real instance), `Docs/traceability.md` (full design, what to gather from the Jira admin, output schema).
- **Still needed to actually close this out**: a real Jira CSV export (or live API access) to run the sync against; confirmation of whether test cases are tracked via plain Jira issues or a plugin (Xray/Zephyr) — the current API path doesn't handle plugin-specific fields yet.
- **Scope**: going forward only, matches the item 2 decision — historical 2,704 rows are not being retroactively backfilled with Jira links as part of this pipeline.

## 5. Field/bug history feed — ⬜ PENDING

Bug tracker or known-issues export for Intrusion Alert (and eventually other features). This is where genuinely novel edge cases come from — cross-referencing documents harder has diminishing returns.

## 6. Test bench capability list — ⬜ PENDING

What can the physical LabCar/Vehicle/Bench rigs actually simulate/inject? No point generating a test case for a fault condition the lab can't produce.

## 7. Compliance/safety mapping — ⬜ PENDING

UNECE R155/ASIL classification for Intrusion Alert, if one exists, so test case severity/priority can reflect it.

## 8. A golden eval set — ⬜ PENDING

10–15 hand-reviewed, expert-approved test cases (can draw from the 2,704 existing rows) held out specifically to regression-test the pipeline whenever a prompt or document changes.
