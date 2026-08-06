# Harness Design — Test Case Generation Pipeline

How the 8 stages in `architecture.md` should actually be wired up as an agent system.

## Split "lookup" from "reasoning"

Signal Resolution and dedupe-checking are deterministic — they belong in tool calls over indexed data (`Signal_Catalogs/unified_signal_index.json`), not LLM judgment calls. Reserve the model's reasoning budget for the two stages that need it: Feature Understanding and Module Interaction Mapping. This is both a cost optimization and a guardrail (see `guardrails.md` #1) — narrowing the hallucination surface to only where judgment is genuinely required.

## Index once, reuse many times

Document Ingestion runs once per document *version*, not once per test case generation. Cache the indexed content — prompt caching if it's going straight into context, a persisted index if doing retrieval — so the other 7 stages aren't re-paying to re-read the same corpus on every call.

## Coordinator + specialist pattern

The 8 stages map onto a coordinator that delegates: one setup pass for ingestion/indexing, then a coordinator handing off to Feature Understanding → Signal Resolution → Interaction Mapper → Generator → Dedupe → Formatter → Reviewer. Either as sequential tool-augmented calls, or as genuinely separate sub-agent threads if independent reasoning is wanted for each.

## Batch generation, not per-test-case calls

Generate test cases in groups (8–10) once the scenario list is decided. Same accuracy and cost benefit — more context to cross-check duplication within a batch, and the fixed cost of loading reference material is amortized across more output.

## Effort tuned per stage, not globally

- **High effort**: Interaction Mapping, edge-case brainstorming — the genuine reasoning work.
- **Low/medium effort**: Formatter — mechanical once scenario + signals are resolved.
- Don't set one global effort level for the whole pipeline; it either overspends on the mechanical stages or underthinks the hard ones.

## Human checkpoint before "released"

Not a suggestion — a required stage. See `guardrails.md` #10. Route Interaction Mapper output and any low-confidence-tagged case to a human SME before it's final, especially for anything safety/security relevant like Intrusion Alert.

## Cost architecture (from the Sonnet 5 cost analysis, 2026-08-06)

For ~50 test cases on Sonnet 5:

- **Naive** (no caching, one call per test case, full reference docs resent each time): ~$3.68 for a clean pass, before agentic overhead — realistically $10–25 with multi-turn reasoning.
- **Optimized** (prompt caching on the reference material + Message Batches API + batched generation): under $1–3 for the same output.

**The single highest-leverage lever**: cache the CAN/VSS reference material (it's identical across every test case in a feature) instead of re-sending it raw on every call. Second: batch generation in groups instead of per-test-case round trips. Both are architecture decisions, not runtime tuning — bake them into the harness from the start rather than retrofitting.
