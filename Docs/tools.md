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

## Needed, not yet built

| Tool | Purpose | Priority |
|---|---|---|
| **FastAPI service scaffolding** | Wrap the tools below as actual HTTP endpoints (`/tools/resolve_signal`, `/tools/check_dedup`, `/tools/validate_schema`, etc.) plus the Claude tool-runner orchestration layer. This is the actual "agentic pipeline as running code" gap flagged 2026-08-06 — everything else in this list is raw material for it. | **Highest — this is the next concrete build step.** |
| Service-side Jira/Xray auth | The Atlassian MCP connector used so far is session-scoped (OAuth via `/mcp` in an interactive terminal). A deployed service needs its own auth pattern — likely a service account + API token, not the interactive OAuth flow. | High — blocks any tool that needs live Jira/Xray access from the deployed service, not just this conversation. |
| Retrieval / embedding search | Once documents are indexed, fetch just the relevant slice per query instead of stuffing everything into context. Simple embedding search over indexed chunks is enough for this corpus size — no heavyweight vector DB needed. | Medium |
| Dedup/similarity tool | Compare a newly generated test case against `Existing_TestCases/` rows and real Jira Test summaries (`Traceability/requirement_traceability.json`) using embedding similarity — category-scoped per `guardrails.md` #6 (only blocks Edge Case/User-Journey matches). Must be a deterministic tool call, not an LLM self-report. | High — named guardrail, repeatedly flagged as the last unbuilt piece of the Coverage Checker. |
| HIL keyword lookup tool | Query `HIL_Automation/hil_keyword_index.json` for a real automation keyword given an intended action, feeding `guardrails.md` #11 (prefer real keywords over free-prose Gherkin). | Medium — new as of 2026-08-07. |
| Version control on the generated suite | Track diffs in the output file between pipeline runs to catch regressions. | Low, but cheap to do early. |

## Explicitly rejected / not needed

- **Heavyweight vector DB** (Pinecone, Weaviate, etc.) — corpus is a handful of documents per feature; a simple in-memory embedding search is sufficient and avoids an infra dependency.
- **Hand-rolled Motorola bit-numbering conversion** — attempted during signal cross-validation, produced an edge-case bug (interdependent-signal encoding conflict) and was abandoned in favor of trusting `cantools`' own parsing rather than re-deriving it. If deeper DBC bit-math is ever needed again, lean on `cantools`'s internals, not a fresh reimplementation.
