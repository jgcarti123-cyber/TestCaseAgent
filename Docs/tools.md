# Tools — Test Case Generation Pipeline

What's actually installed/used vs. what's still needed. See `architecture.md` for which pipeline stage uses which tool, `harness_design.md` for the confirmed implementation stack.

## Implementation stack — confirmed 2026-08-07

**Python + FastAPI**, team-confirmed with no competing infra constraint identified. Reasoning: every tool below is already Python; FastAPI is a strong, production-proven fit for the confirmed deployment shape (persistent service, callable via API, possibly CI/CD-triggered — see `harness_design.md`); Anthropic's Python SDK has first-class tool-runner support that maps directly onto the tool list below. See chat history (2026-08-06/07) for the full reasoning, including why this beat Java/TypeScript alternatives.

## In use today

| Tool | Purpose | Notes |
|---|---|---|
| `cantools` (Python, `pip install cantools`) | Parses the `.dbc` file into structured message/signal objects — bit positions, byte order, enum choices. | Ground truth for CAN signals. Never hand-parse a `.dbc` with regex. |
| `openpyxl` | Reads/writes all `.xlsx` files — the Master Signal Catalog, the 22 existing test suites, `HIL_Automation/Keywords.xlsx`, and the generated output. | Used for both reading reference data and writing the final test case file. |
| `jsonschema` (Python) | Validates generated test case rows against `Schema/test_case_schema.json`. | Run this before writing a row to the output file, not just after. |
| `PyMuPDF` (`fitz`) | Full-text search across `Requirement_Docs/*.pdf` — confirmed available and used (2026-08-07) to search 523 pages for ASIL/UNECE compliance keywords in seconds. Supersedes the originally-planned `pdfplumber`. | Table extraction specifically (not just keyword search) still needs evaluation — `fitz` handles plain text well, tables less proven. |
| Atlassian MCP connector | Live Jira queries (`getJiraIssue`, `searchJiraIssuesUsingJql`, field metadata) — used throughout item 4/5/traceability work. | Session-scoped, OAuth-based (see `traceability.md` for setup). Not yet a standalone tool a deployed service can call the same way — needs a service-side auth pattern (see below). |

## FastAPI service scaffolding — 🟢 SCAFFOLDED (2026-08-07)

**Built artifact**: `Scripts/service/` — a running FastAPI app, not yet wired to the Claude tool-runner orchestration layer (that's still the next step, see below).

```
Scripts/service/
├── main.py              # app entrypoint + /health — run with `cd Scripts && uvicorn service.main:app --reload`
├── config.py             # all repo paths in one place (Signal_Catalogs, Schema, Existing_TestCases, etc.)
├── models.py              # pydantic request/response models per endpoint
├── routers/tools.py       # HTTP layer — thin wrappers over tools/*.py
├── tools/                 # pure, unit-testable functions with no FastAPI dependency
│   ├── signal_resolution.py   # /tools/resolve_signal
│   ├── schema_validation.py   # /tools/validate_schema
│   └── dedup.py                # /tools/check_dedup
├── tests/                 # pytest + FastAPI TestClient, 12 tests, run from Scripts/: `python -m pytest service/tests/`
└── requirements.txt
```

**Implemented for real, not stubbed:**
- `/tools/resolve_signal` — the two-source deterministic lookup from `guardrails.md` #1/#2 and `definition_of_done.md` Tier 1 gate #2: `unified_signal_index.json` first, then `dbc_raw_reference.json`, then a live `cantools` parse of the `.dbc` as a last-resort ground-truth check. Verified against both worked examples in the docs (`ABsActive` via the index, `SASSUnLockAllDoorCommand` via DBC fallback) plus the two known-fabricated names (`RemoteLockStatus`, `RKEUnlockEvent`) correctly returning `SIGNAL NOT FOUND`.
- **New finding while building this**: `dbc_raw_reference.json` values are lists, not single objects — 28 signal names are legitimately defined on more than one CAN message. The tool never silently picks one; it returns `ambiguous: true` + `all_matches` and refuses to guess a `can_message_id`. This is the same class of risk as guardrail #1, just discovered from the data shape rather than anticipated in advance.
- `/tools/validate_schema` — `jsonschema` against `Schema/test_case_schema.json`, plus the two Tier 1 gates that are cheap to check alongside it: summary/test_description byte-identity (gate 4) and `sr_no`/`issue_type` numbering consistency (part of gate 1).
- `/tools/check_dedup` — the exact-field-match method from `definition_of_done.md` Tier 1 gate #6, category-scoped per `guardrails.md` #6 (blocking only for `Edge Case - *`/`User-Journey`). **Deliberately scoped to same-batch + `Generated_TestCases/` only** — it does not check `Existing_TestCases/` (empty `Requirement ID`/`Test Set Category` on all 2,704 rows makes exact-field match meaningless there) or Jira (feature-level only, not per-requirement). Both gaps are reported back in the response's `unchecked_sources` field rather than silently passing. Closing them for real is still the Dedup/similarity tool below.

**Stubbed on purpose (return HTTP 501 with a doc pointer, not a fake answer):** `/tools/hil_keyword_lookup`, `/tools/jira_traceability_check` — see the table below for why each is still open.

## Needed, not yet built

| Tool | Purpose | Priority |
|---|---|---|
| **Claude tool-runner orchestration layer** | Wire the Anthropic Python SDK's tool-runner up to the `Scripts/service/` endpoints above so the 8-stage pipeline actually runs as an agent loop, per `harness_design.md`'s coordinator/specialist pattern. `anthropic` SDK not yet installed in this environment. | **Highest — now that the tool endpoints exist, this is the next concrete build step.** |
| Service-side Jira/Xray auth | The Atlassian MCP connector used so far is session-scoped (OAuth via `/mcp` in an interactive terminal). A deployed service needs its own auth pattern — likely a service account + API token, not the interactive OAuth flow. Blocks `/tools/jira_traceability_check`, currently stubbed. | High — blocks any tool that needs live Jira/Xray access from the deployed service, not just this conversation. |
| Retrieval / embedding search | Once documents are indexed, fetch just the relevant slice per query instead of stuffing everything into context. Simple embedding search over indexed chunks is enough for this corpus size — no heavyweight vector DB needed. | Medium |
| Dedup/similarity tool | Compare a newly generated test case against `Existing_TestCases/` rows and real Jira Test summaries (`Traceability/requirement_traceability.json`) using embedding similarity — category-scoped per `guardrails.md` #6 (only blocks Edge Case/User-Journey matches). Must be a deterministic tool call, not an LLM self-report. This is what closes the two `unchecked_sources` gaps in `/tools/check_dedup` above. | High — named guardrail, repeatedly flagged as the last unbuilt piece of the Coverage Checker. |
| HIL keyword lookup tool | Query `HIL_Automation/hil_keyword_index.json` for a real automation keyword given an intended action, feeding `guardrails.md` #11 (prefer real keywords over free-prose Gherkin). Endpoint exists at `/tools/hil_keyword_lookup` and currently returns 501. | Medium — new as of 2026-08-07. |
| Version control on the generated suite | Track diffs in the output file between pipeline runs to catch regressions. | Low, but cheap to do early. |

## Explicitly rejected / not needed

- **Heavyweight vector DB** (Pinecone, Weaviate, etc.) — corpus is a handful of documents per feature; a simple in-memory embedding search is sufficient and avoids an infra dependency.
- **Hand-rolled Motorola bit-numbering conversion** — attempted during signal cross-validation, produced an edge-case bug (interdependent-signal encoding conflict) and was abandoned in favor of trusting `cantools`' own parsing rather than re-deriving it. If deeper DBC bit-math is ever needed again, lean on `cantools`'s internals, not a fresh reimplementation.
