# Tools — Test Case Generation Pipeline

What's actually installed/used vs. what's still needed. See `architecture.md` for which pipeline stage uses which tool.

## In use today

| Tool | Purpose | Notes |
|---|---|---|
| `cantools` (Python, `pip install cantools`) | Parses the `.dbc` file into structured message/signal objects — bit positions, byte order, enum choices. | Ground truth for CAN signals. Never hand-parse a `.dbc` with regex. |
| `openpyxl` | Reads/writes all `.xlsx` files — the Master Signal Catalog, the 22 existing test suites, and the generated output. | Used for both reading reference data and writing the final test case file. |
| `jsonschema` (Python) | Validates generated test case rows against `Schema/test_case_schema.json`. | Run this before writing a row to the output file, not just after. |

## Needed, not yet built

| Tool | Purpose | Priority |
|---|---|---|
| PDF table extraction (`pdfplumber` or Claude's native PDF input with citations) | Extracting requirement text and DFMEA tables from `Requirement_Docs/*.pdf` with page/section citations. | High — Feature Understanding and Module Interaction Mapper both depend on this. |
| Retrieval / embedding search | Once documents are indexed, fetch just the relevant slice per query instead of stuffing everything into context. Simple embedding search over indexed chunks is enough for this corpus size — no need for a heavyweight vector DB. | Medium |
| Dedup/similarity tool | Compare a newly generated test case against the 2,704 existing rows (and against other cases in the same generation batch) using embedding similarity + exact requirement-ID overlap. Must be a deterministic tool call, not an LLM self-report. | High — this is a named guardrail (see `guardrails.md`). |
| ALM/requirement-tracking integration | If traceability data lives in Polarion/DOORS/Jira rather than a flat file, the Coverage Checker needs API access. | Depends on requirement #4 in `requirements.md`. |
| Version control on the generated suite | Track diffs in the output file between pipeline runs to catch regressions. `git init` this folder once it stabilizes. | Low, but cheap to do early. |

## Explicitly rejected / not needed

- **Heavyweight vector DB** (Pinecone, Weaviate, etc.) — corpus is a handful of documents per feature; a simple in-memory embedding search is sufficient and avoids an infra dependency.
- **Hand-rolled Motorola bit-numbering conversion** — attempted during signal cross-validation, produced an edge-case bug (interdependent-signal encoding conflict) and was abandoned in favor of trusting `cantools`' own parsing rather than re-deriving it. If deeper DBC bit-math is ever needed again, lean on `cantools`'s internals, not a fresh reimplementation.
