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

- **`Existing_TestCases/` has zero Requirement ID links across all 2,704 rows.** Don't assume it's a "mostly complete, some gaps" traceability source — it has none at all. Real traceability lives in Jira (`jiratatamotors.atlassian.net`, Xray-based) — an Atlassian MCP connector was set up and used to live-query it for Intrusion Alert on 2026-08-06 (in a separate terminal Claude Code session, not this conversation's own tool set — don't assume Jira tools are available here without checking first). **Jira's traceability is feature-level only, not per-requirement-line** — the local `NIO-F0001_INT_REQ_NNN` scheme doesn't exist in Jira at all (confirmed: zero hits on a full-instance text search). See `Docs/traceability.md` for the full finding and the chosen fix (feature-level check + semantic similarity against real Jira Test summaries, not yet built).
- **Never ask the user for a Jira/Atlassian API token in chat** — OAuth via `/mcp` in their own terminal is how this got connected, and that's the pattern for any future connector too.

## Open items

See `Docs/requirements.md` items 6–8 (test bench capability list, compliance mapping, golden eval set) and the two pending tasks logged in-session (residual signal discrepancies, `DoorStateDrvr` naming ambiguity) — both need a domain expert, not further agent investigation. Item 4 (traceability) has a live Jira connector and real data for Intrusion Alert, but the semantic-similarity dedup piece isn't built yet, and only 1 of 22 features has been checked. Item 5 (bug history) has partial real data for Intrusion Alert (27 closed Jira bugs), not yet wired into test case generation.
