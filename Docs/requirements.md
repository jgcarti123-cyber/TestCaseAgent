# Requirements — Test Case Generation Pipeline

Living checklist of what the pipeline needs beyond the raw feature documents. Update status as items get resolved. See `architecture.md` for how these feed the 8-stage pipeline, `guardrails.md` for the accuracy rules these requirements exist to support.

## 1. Authoritative signal ground truth — ✅ DONE (2026-08-06)

Real `.dbc` file + Master Signal Catalog, not PDF-parsed tables.

- **Source files**: `Signal_Catalogs/TML_IVN_Communication_Matrix_CM_CANFD_V1.1.5_TM.dbc` (436 messages, 3,623 signals), `Signal_Catalogs/Master_Signal_Catalog_V4.4_20.8.25.xlsx` (VSS↔CAN cross-reference, 3,684 rows).
- **Built artifact**: `Signal_Catalogs/unified_signal_index.json` — cross-validated index, every entry flagged `bit_position_match: true/false`. This is what Signal Resolution queries; never re-derive from the raw PDFs.
- **Known gaps**: 345 residual catalog-vs-DBC discrepancies unresolved (see task #6), `DoorStateDrvr` naming ambiguity between message 748/946 unresolved (task #7), 1,376 DBC signals have no VSS mapping yet (`dbc_signals_without_vss_mapping.json`).

## 2. Machine-readable test case schema — ✅ DONE (2026-08-06)

- **Built artifact**: `Schema/test_case_schema.json` — formal JSON Schema, derived empirically from 2,704 rows across the 22 existing feature files, not guessed.
- **Key decisions** (see git/chat history for full reasoning):
  - `Environment` enum enforced (`LabCar`/`Vehicle`/`Bench`) for new rows only — 22 historical files keep their 6 inconsistent spellings, not retroactively fixed.
  - The two identically-named "Test Type" columns (execution method vs. validation scope) kept as-is, documented rather than renamed.
  - `Test Set Category` (Happy Path / Negative / Edge Case taxonomy) is now **required** for all new/AI-generated rows — it was empty in all 2,704 historical rows.
  - `CAN Signals Referenced` / `VSS Signals Referenced` columns adopted as the new standard schema for all future test cases, not just this pipeline.
- Validated against all 3 generated test cases with zero schema errors.

## 3. A "definition of done" rubric — ⬜ PENDING

What makes a generated test case acceptable, as an explicit, checkable list — not vibes. Draft candidate criteria (confirm with team before finalizing):

- Traces to a real requirement ID present in `Requirement_Docs/`.
- Every CAN/VSS signal is `bit_position_match: true` in `unified_signal_index.json`, or explicitly flagged `SIGNAL NOT FOUND`.
- Passes `Schema/test_case_schema.json` validation.
- Not a near-duplicate of an existing test case (dedup threshold TBD).
- `Test Set Category` is populated and matches the actual scenario logic.

This becomes the rubric for the Reviewer stage and for a human spot-check.

## 4. Requirement traceability data — ⬜ PENDING

Where does official coverage/traceability data live (Polarion / DOORS / Jira / an RTM spreadsheet)? The Coverage Checker stage currently only has the 2,704 rows in `Existing_TestCases/` as its "already covered" reference — needs to know if that's the full picture or a subset.

## 5. Field/bug history feed — ⬜ PENDING

Bug tracker or known-issues export for Intrusion Alert (and eventually other features). This is where genuinely novel edge cases come from — cross-referencing documents harder has diminishing returns.

## 6. Test bench capability list — ⬜ PENDING

What can the physical LabCar/Vehicle/Bench rigs actually simulate/inject? No point generating a test case for a fault condition the lab can't produce.

## 7. Compliance/safety mapping — ⬜ PENDING

UNECE R155/ASIL classification for Intrusion Alert, if one exists, so test case severity/priority can reflect it.

## 8. A golden eval set — ⬜ PENDING

10–15 hand-reviewed, expert-approved test cases (can draw from the 2,704 existing rows) held out specifically to regression-test the pipeline whenever a prompt or document changes.
