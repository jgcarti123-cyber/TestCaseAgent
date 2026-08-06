# Architecture — Test Case Generation Pipeline

## The 8 stages

1. **Document Ingestion & Indexing** — parses every requirement PDF, the Master Signal Catalog, DFMEA, and existing test suites into a structured, queryable index tagged by feature, requirement ID, CAN signal, VSS path, and message ID. Run once per document version, not once per test case.
2. **Feature Understanding (Requirement Analyst)** — for the target feature, extracts user stories, preconditions, the documented CAN signal list, requirement IDs, and lifecycle rules.
3. **Signal Resolution** — resolves every signal name mentioned anywhere into its full definition. **This is a deterministic tool call, never LLM free-generation.** Two-source lookup order: `Signal_Catalogs/unified_signal_index.json` first, then the raw `.dbc` file directly if not found there (the index only covers 70.8% of DBC signals — see `guardrails.md` #2). Only flagged `SIGNAL NOT FOUND` if absent from both.
4. **Module Interaction Mapper** — scans sibling feature docs and the DFMEA to find where CAN frames, ECUs, or state machines overlap with the target feature. This is what surfaces edge cases nobody explicitly wrote down (see Test_89 as the worked example).
5. **Test Case Generator** — produces cases across the fixed taxonomy in `Schema/test_case_schema.json`'s `test_set_category` enum: Happy Path, Negative Case, Edge Case (Cross-Module / Signal-Fault-Boundary / DFMEA-Derived), User-Journey.
6. **Coverage & Dedupe Checker** — three checks, not one, since neither local nor Jira data alone is enough:
   - **Exact-field match against `Existing_TestCases/`** (2,704 rows across 22 features) — per `definition_of_done.md` Tier 1 gate #6.
   - **Feature-level Jira check against `Traceability/requirement_traceability.json`** (`traceability.md`) — Jira only has feature-granularity traceability (Xray Parent-Child, Feature → Test), not per-requirement-line, so this answers "does Jira show *any* coverage for this feature" rather than "is this exact requirement covered."
   - **Semantic similarity against real Jira Test issue summaries** (not yet built — the chosen way to close the granularity gap without depending on Jira admins adding line-level linkage; see `traceability.md` → Granularity gap decision, 2026-08-06). Needed because naive keyword-overlap dedup produces false positives from shared boilerplate phrasing (demonstrated: a network-availability Jira test "matched" two unrelated generated cases at 75% purely on shared words like "verify"/"intrusion"/"vehicle"/"IGN") — this is the same limitation already flagged for local dedup in `definition_of_done.md` Tier 1 gate #6, now confirmed to also apply to Jira comparison, not just local.

   All three enforced by tools, never by asking the LLM "did you check?"
7. **Formatter** — writes output conforming to `Schema/test_case_schema.json`. Validate with `jsonschema` before writing to the `.xlsx`.
8. **Reviewer (QA-of-QA)** — applies `Docs/definition_of_done.md`: Tier 1 hard gates (schema, signal verification, traceability, dedup) auto-reject; Tier 2 quality checks (category-logic match, no orphan signal claims, step specificity, confidence-tag accuracy) route to human review rather than auto-reject. Not the final gate for Edge Case categories or low-confidence cases — those need mandatory human sign-off regardless of automated pass/fail. See `guardrails.md` and `definition_of_done.md`.

## Effort allocation per stage

Not every stage deserves the same reasoning budget:

- **High effort, worth the spend**: Feature Understanding, Module Interaction Mapper — this is the actual "what did nobody think of" work.
- **Low/medium effort, mechanical**: Formatter — once the scenario and signals are resolved, writing the row is templated.
- **No LLM at all**: Signal Resolution, Dedupe Checker — deterministic tool calls, not reasoning tasks. Keeping these out of the LLM's hands is itself a guardrail, not just a cost optimization.

## Folder structure

```
Test Case/
├── CLAUDE.md                    ← start here every session
├── Docs/                        ← this file + requirements/tools/harness/guardrails/definition_of_done/traceability
├── Schema/                      ← test_case_schema.json (formal, validated)
├── Scripts/                     ← jira_traceability_sync.py and future pipeline tooling
├── Signal_Catalogs/             ← DBC + Master Catalog + derived indexes (ground truth)
├── Requirement_Docs/            ← NF-FFW PDFs + DFMEA (stage 1/2/4 input)
├── Existing_TestCases/          ← 22 features, 2,704 rows (stage 6 reference; formerly "Draft")
├── Generated_TestCases/         ← pipeline output
└── Traceability/                ← requirement_traceability.json (Jira-sourced, gitignored, stage 6 input)
```

## Batching, not per-test-case calls

Generate test cases in groups (8–10 at a time) once the scenario list is decided, rather than one API call per test case. Same accuracy benefit as cost benefit — the model can cross-check for duplication within a batch, and the fixed cost of loading context is amortized across more output.

## What changed after building the real index (2026-08-06)

Building `unified_signal_index.json` against the real `.dbc` caught 2 fabricated signal names in the 3 hand-authored test cases (`RemoteLockStatus`, `RKEUnlockEvent` — neither exists) and corrected them. It also caught a false alarm: an initial "1,592 discrepancies" report between the catalog and DBC turned out to be 78% explainable by a bit-numbering-convention difference (catalog anchors to LSB, `cantools` reports MSB) rather than real data errors. See `guardrails.md` for the rule this produced.
