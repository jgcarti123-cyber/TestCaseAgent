# Test Case — Project Context

AI agentic test case generation for TML Connected Cars features. Read this first in any new session; it points to everything else.

## What this project is

Generating positive, negative, and edge-case test cases for connected-car features (currently: Intrusion Alert, `NIO-F001`), grounded in real requirement docs, DFMEA, and CAN/VSS signal ground truth — not documents alone. Full design rationale lives in `Docs/`.

## Read next, in this order

1. **`Docs/architecture.md`** — the 8-stage pipeline and folder structure.
2. **`Docs/guardrails.md`** — accuracy rules, including two that were validated against real failures in this project (not hypothetical).
3. **`Docs/requirements.md`** — living checklist of what's done vs. pending.
4. **`Docs/tools.md`** / **`Docs/harness_design.md`** — implementation detail.
5. **`Schema/test_case_schema.json`** — formal schema for every column; validate output against this before writing to Excel.

## Folder map

```
CLAUDE.md                 ← you are here
Docs/                     ← architecture, guardrails, requirements, tools, harness_design
Schema/test_case_schema.json
Signal_Catalogs/          ← DBC + Master Signal Catalog + derived JSON indexes (ground truth)
Requirement_Docs/         ← NF-FFW PDFs + DFMEA
Existing_TestCases/       ← 22 features, 2,704 rows (dedup/coverage reference)
Generated_TestCases/      ← pipeline output (currently: Intrusion Alert, 3 test cases)
```

## Critical facts to not re-derive

- **Signal ground truth is `Signal_Catalogs/unified_signal_index.json`.** Never resolve a CAN/VSS signal from a PDF or from memory — see `Docs/guardrails.md` #1. This was violated once already in this project (2 fabricated signal names slipped into hand-authored test cases) and caught only after the real DBC was cross-checked.
- **The Master Signal Catalog and the `.dbc` disagree on ~345 signals even after accounting for a known numbering-convention artifact** — see `Docs/guardrails.md` #2 for why the original ~1,592-count first reported was wrong, and don't re-report the raw number without applying the same correction.
- **`Test Set Category` is required for new test cases; it's empty in all 2,704 historical rows.** Don't assume its absence in existing files means it's optional.
- **Two columns are both named "Test Type"** (execution method vs. validation scope) — kept as-is by team decision, not a bug to fix.
- **`Summary` and `Test Description` must always be byte-identical** — short, one-sentence text, not a separate long-form paragraph. This was explicit team feedback (2026-08-06); don't regress to writing them differently.

## Open items

See `Docs/requirements.md` items 3–8 (definition-of-done rubric, traceability data source, bug history feed, test bench capability list, compliance mapping, golden eval set) and the two pending tasks logged in-session (residual signal discrepancies, `DoorStateDrvr` naming ambiguity) — both need a domain expert, not further agent investigation.
