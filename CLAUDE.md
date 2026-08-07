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
Docs/                     ← architecture, guardrails, requirements, tools, harness_design, definition_of_done,
                             traceability, golden_eval_set, test_bench_capabilities, compliance_mapping
Schema/test_case_schema.json
Scripts/                  ← jira_traceability_sync.py, xray_execution_status_sync.py (built, Xray one unrun - needs Xray admin access)
Signal_Catalogs/          ← DBC + Master Signal Catalog + derived JSON indexes (ground truth) — gitignored
Requirement_Docs/         ← NF-FFW PDFs + DFMEA — gitignored
Existing_TestCases/       ← 22 features, 2,704 rows (dedup/coverage reference — zero Requirement ID links, see traceability.md) — gitignored
Generated_TestCases/      ← pipeline output (currently: Intrusion Alert, 3 test cases) — gitignored
Traceability/             ← requirement_traceability.json, Jira-sourced — gitignored
HIL_Automation/           ← Keywords.xlsx (team-provided) + hil_keyword_index.json (parsed) — real HIL rig
                             automation keyword library, 19-20 modules. Gitignored.
```

Everything gitignored above is real TML data that stays local-only — see `.gitignore`. Only `CLAUDE.md`, `Docs/`, `Schema/`, and `Scripts/` are pushed to the `TestCaseAgent` GitHub repo.

## Implementation stack — confirmed 2026-08-07

**Python + FastAPI.** See `Docs/tools.md` for the full reasoning. The actual agentic pipeline (tools an agent calls autonomously, per `Docs/architecture.md`'s 8 stages) is **not built as running code yet** — everything so far has been manually orchestrated across this conversation. `Docs/tools.md`'s "Needed, not yet built" table, topped by FastAPI service scaffolding, is the concrete next-build list.

## Critical facts to not re-derive

- **Signal ground truth is two sources, checked in order: `Signal_Catalogs/unified_signal_index.json` first, then the raw `.dbc` file directly.** Never resolve a CAN/VSS signal from a PDF or from memory — see `Docs/guardrails.md` #1. The index only covers 70.8% of DBC signals (2,544/3,593) because it's built from the Master Signal Catalog, which lacks a VSS mapping for 1,375 real signals — a signal missing from the index is **not** automatically fabricated; check the raw DBC before concluding that (see `Docs/guardrails.md` #2, second entry — this was almost gotten wrong once already, on `Test_91`). Only flag `SIGNAL NOT FOUND` if absent from both sources.
- **The Master Signal Catalog and the `.dbc` disagree on ~345 signals even after accounting for a known numbering-convention artifact** — see `Docs/guardrails.md` #2 for why the original ~1,592-count first reported was wrong, and don't re-report the raw number without applying the same correction.
- **`Test Set Category` is required for new test cases; it's empty in all 2,704 historical rows.** Don't assume its absence in existing files means it's optional.
- **Two columns are both named "Test Type"** (execution method vs. validation scope) — kept as-is by team decision, not a bug to fix.
- **`Summary` and `Test Description` must always be byte-identical** — short, one-sentence text, not a separate long-form paragraph. This was explicit team feedback (2026-08-06); don't regress to writing them differently.
- **Before a test case is "released"**: Tier 1 + Tier 2 checks in `Docs/definition_of_done.md` must pass, and Edge Case categories / low-confidence cases need mandatory human sign-off regardless — see that file's status lifecycle before marking anything final.

- **`Existing_TestCases/` has zero Requirement ID links across all 2,704 rows.** Don't assume it's a "mostly complete, some gaps" traceability source — it has none at all. Real traceability lives in Jira (`jiratatamotors.atlassian.net`, Xray-based) — an Atlassian MCP connector was set up and used to live-query it. **Jira does carry per-requirement-line linkage** for the 2 features checked at that depth (Intrusion Alert, Time Fencing Alert) — requirement IDs matching the local `NIO-F00NN_INT_REQ_NNN` scheme are embedded as free text inside each Xray Test issue's `description` field (not a dedicated field, and not reliably found by cross-project text search — the separator between "NIO" and "F00NN" varies: real hyphen, a stray control character, or none; read individual issues directly, don't trust a broad JQL text search for this). Coverage is coarse relative to `Requirement_Docs/`, though: Intrusion Alert's 40 Test issues cite only `REQ_001`/`REQ_002`, not the fuller set used locally (up to `REQ_014`). 18 more features have feature-level-only data (Test + bug counts, no per-requirement extraction — see `Docs/traceability.md`). 4 local features (`Auto Ecall`, `E-Call Manual`, `RESS`, `B-Call SoftSwitch`) have no Jira mapping — deliberately skipped, not guessed. See `Traceability/requirement_traceability.json` for all of it (20 of 22 features).
- **Never ask the user for a Jira/Atlassian API token in chat** — OAuth via `/mcp` in their own terminal is how this got connected, and that's the pattern for any future connector too. Same rule for Xray credentials (separate system, separate API, see below).
- **HIL rig capability is real and documented, not inferred** — `HIL_Automation/hil_keyword_index.json`, parsed from a team-provided keyword library. HIL can inject any DBC CAN signal by name and has dedicated fault-insertion hardware (open/short-circuit specific channels) — fault/boundary-condition test cases for `environment: HIL` are genuinely executable. Prefer real keywords from that index over free-prose Gherkin where one exists (`guardrails.md` #11) — a few modules in the index have known parsing gaps, see its own `parsing_caveats` field before trusting every entry blindly.

## Open items

See `Docs/requirements.md` items 6–7 (test bench capability list, compliance mapping) and the two pending tasks logged in-session (residual signal discrepancies, `DoorStateDrvr` naming ambiguity) — item 7 and the two pending tasks need a domain expert, not further agent investigation; item 6 is now substantially answered for HIL (see above), just needs LabCar/Vehicle/Bench detail and a few parsing-caveat spot-checks. Item 4 (traceability): full per-requirement data for 2 features, feature-level data for 18 more, 4 skipped needing team confirmation — semantic-similarity dedup piece still not built. Item 5 (bug history) has real, field-verified severity/associated-project/due-date/comment data for Intrusion Alert's 27 linked bugs (not yet wired into test case generation). Xray execution status (Pass/Fail) is **deferred** — blocked on Xray admin access, not a code problem; `Scripts/xray_execution_status_sync.py` stays built and ready. Item 8 (golden eval set) started — `Docs/golden_eval_set.md`, 3 confirmed + 12 candidates pending human review.

**The bigger gap than any single requirements item**: the actual agentic pipeline isn't built as running code — see "Implementation stack" above. That's the next real work, not more data-gathering.
