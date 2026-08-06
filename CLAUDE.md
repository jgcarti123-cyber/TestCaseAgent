# Test Case — Project Context

AI agentic test case generation for TML Connected Cars features. Read this first in any new session; it points to everything else.

## What this project is

Generating positive, negative, and edge-case test cases for connected-car features (currently: Intrusion Alert, `NIO-F001`), grounded in real requirement docs, DFMEA, and CAN/VSS signal ground truth — not documents alone. Full design rationale lives in `Docs/`.

## Read next, in this order

1. **`Docs/architecture.md`** — the 8-stage pipeline and folder structure.
2. **`Docs/guardrails.md`** — accuracy rules, including three validated against real failures in this project (not hypothetical).
3. **`Docs/definition_of_done.md`** — the acceptance rubric a test case must pass before release; also the model for the two-source signal verification rule (see below).
4. **`Docs/requirements.md`** — living checklist of what's done vs. pending.
5. **`Docs/tools.md`** / **`Docs/harness_design.md`** — implementation detail.
6. **`Schema/test_case_schema.json`** — formal schema for every column; validate output against this before writing to Excel.
7. **`Docs/golden_eval_set.md`** — the fixed regression baseline; re-check pipeline output against this after any prompt/schema change.
8. **`Docs/test_bench_capabilities.md`** / **`Docs/compliance_mapping.md`** — what the physical rigs can actually simulate, and ASIL/UNECE R155 status (both still open, needs safety/compliance team).

## Folder map

```
CLAUDE.md                 ← you are here
Docs/                     ← architecture, guardrails, requirements, tools, harness_design, definition_of_done, traceability
Schema/test_case_schema.json
Scripts/jira_traceability_sync.py
Signal_Catalogs/          ← DBC + Master Signal Catalog + derived JSON indexes (ground truth)
Requirement_Docs/         ← NF-FFW PDFs + DFMEA
Existing_TestCases/       ← 22 features, 2,704 rows (dedup/coverage reference — zero Requirement ID links, see traceability.md)
Generated_TestCases/      ← pipeline output (currently: Intrusion Alert, 3 test cases)
Traceability/             ← requirement_traceability.json, Jira-sourced, gitignored (not yet populated with real data)
```

## Critical facts to not re-derive

- **Signal ground truth is two sources, checked in order: `Signal_Catalogs/unified_signal_index.json` first, then the raw `.dbc` file directly.** Never resolve a CAN/VSS signal from a PDF or from memory — see `Docs/guardrails.md` #1. The index only covers 70.8% of DBC signals (2,544/3,593) because it's built from the Master Signal Catalog, which lacks a VSS mapping for 1,375 real signals — a signal missing from the index is **not** automatically fabricated; check the raw DBC before concluding that (see `Docs/guardrails.md` #2, second entry — this was almost gotten wrong once already, on `Test_91`). Only flag `SIGNAL NOT FOUND` if absent from both sources.
- **The Master Signal Catalog and the `.dbc` disagree on ~345 signals even after accounting for a known numbering-convention artifact** — see `Docs/guardrails.md` #2 for why the original ~1,592-count first reported was wrong, and don't re-report the raw number without applying the same correction.
- **`Test Set Category` is required for new test cases; it's empty in all 2,704 historical rows.** Don't assume its absence in existing files means it's optional.
- **Two columns are both named "Test Type"** (execution method vs. validation scope) — kept as-is by team decision, not a bug to fix.
- **`Summary` and `Test Description` must always be byte-identical** — short, one-sentence text, not a separate long-form paragraph. This was explicit team feedback (2026-08-06); don't regress to writing them differently.
- **Before a test case is "released"**: Tier 1 + Tier 2 checks in `Docs/definition_of_done.md` must pass, and Edge Case categories / low-confidence cases need mandatory human sign-off regardless — see that file's status lifecycle before marking anything final.

- **`Existing_TestCases/` has zero Requirement ID links across all 2,704 rows.** Don't assume it's a "mostly complete, some gaps" traceability source — it has none at all. Real traceability lives in Jira (`jiratatamotors.atlassian.net`, Xray-based) — an Atlassian MCP connector was set up and used to live-query it for Intrusion Alert (NIO-F001) and Time Fencing Alert (NIO-F003) on 2026-08-06. **Jira does carry per-requirement-line linkage** — requirement IDs matching the local `NIO-F00NN_INT_REQ_NNN` scheme are embedded as free text inside each Xray Test issue's `description` field (not a dedicated field, and not reliably found by cross-project text search — the separator between "NIO" and "F00NN" varies: real hyphen, a stray control character, or none; read individual issues directly, don't trust a broad JQL text search for this). Coverage is coarse relative to `Requirement_Docs/`, though: Intrusion Alert's 40 Test issues cite only `REQ_001`/`REQ_002`, not the fuller set used locally (up to `REQ_014`). Xray's Parent-Child link (Feature → Test issues) additionally gives feature-level coverage. See `Docs/traceability.md` for the full finding and `Traceability/requirement_traceability.json` for the real per-requirement data pulled so far (2 of 22 features).
- **Never ask the user for a Jira/Atlassian API token in chat** — OAuth via `/mcp` in their own terminal is how this got connected, and that's the pattern for any future connector too.

## Open items

See `Docs/requirements.md` items 6–7 (test bench capability list, compliance mapping) and the two pending tasks logged in-session (residual signal discrepancies, `DoorStateDrvr` naming ambiguity) — all need a domain expert, not further agent investigation. Item 4 (traceability) has a live Jira connector: full per-requirement data for 2 features (Intrusion Alert, Time Fencing Alert), feature-level data (Test + bug counts) for 18 more — 4 local features (`Auto Ecall`, `E-Call Manual`, `RESS`, `B-Call SoftSwitch`) deliberately skipped, ambiguous/no Jira match, needs team confirmation. Semantic-similarity dedup piece still not built. Item 5 (bug history) has real, field-verified severity/associated-project/due-date/comment data for Intrusion Alert's 27 linked bugs (not yet wired into test case generation). Xray execution status (Pass/Fail) is **deferred** — blocked on Xray admin access, not a code problem; `Scripts/xray_execution_status_sync.py` stays built and ready. Item 6 (test bench) confirmed a 4th environment (`HIL`) and that direct CAN injection exists somewhere, but not which rig or the full capability matrix — needs the lab/test team. Item 7 (compliance) confirmed both ASIL and UNECE R155 status are genuinely undocumented anywhere locally (not an agent-search gap) — needs the safety/compliance team. Item 8 (golden eval set) started — `Docs/golden_eval_set.md`, 3 confirmed + 12 candidates pending human review.
