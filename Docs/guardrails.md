# Guardrails — Test Case Generation Pipeline

Rules that exist because of a specific, demonstrated failure mode, not hypothetical ones. Where a guardrail was validated against real data in this project, that's noted.

## 1. Never let the model invent a signal

The single highest-risk failure mode in this domain. Signal Resolution must be a deterministic tool call against `Signal_Catalogs/unified_signal_index.json` / `dbc_raw_reference.json` — never LLM free-generation from memory of a document.

**Validated (2026-08-06):** cross-checking the 3 hand-authored test cases against the real DBC found exactly this failure — `RemoteLockStatus` and `RKEUnlockEvent` were fabricated, plausible-looking signal names that don't exist anywhere. 7 of 9 signals used were correct; 2 were not. Both were corrected once real data was available. This is not a hypothetical risk — it already happened once in this project.

**Rule**: if a signal can't be found in the index, output `SIGNAL NOT FOUND — flag for review`. Never produce a plausible guess.

## 2. Verify apparent data conflicts before reporting them as errors

**Added 2026-08-06, from a real near-miss.** An initial cross-validation pass reported ~1,592 "discrepancies" between the Master Signal Catalog and the DBC file and nearly got reported to the user as a data-quality problem requiring escalation. It wasn't, mostly — 78% was a bit-numbering-convention artifact (catalog anchors "Bit Start" to a signal's LSB; `cantools` reports the MSB from the raw `.dbc` text; for an N-bit signal these differ by exactly N−1, and are identical when N=1).

**Rule**: before reporting "source A and source B disagree," check whether the disagreement fits a systematic pattern (a numbering/unit/encoding-convention difference) rather than assuming it's a genuine conflict. Only escalate what survives that check. In this project, that dropped the discrepancy count from 1,592 to 345 genuinely-unresolved entries — a 4.6x difference between what looked true at first glance and what was actually defensible.

**Second near-miss, same rule (2026-08-06, while building `definition_of_done.md`).** `unified_signal_index.json` only covers 2,544 of 3,593 DBC signal names (70.8%) — it's built from the Master Signal Catalog, which lacks a VSS mapping for 1,375 real DBC signals. `Test_91`'s `SASSUnLockAllDoorCommand` wasn't in the index and was initially — wrongly — flagged as a likely fabrication. Checking the **raw DBC directly** found it exactly as used (message `SASS_Event2_RC`, frame ID 538, bit 7/length 1). "Not in the derived index" ≠ "doesn't exist" — the index is a convenience artifact with known incomplete coverage, not the ground truth itself. The raw `.dbc` is. See `definition_of_done.md` Tier 1 gate #2 for the two-source check this produced: index first, raw DBC fallback, only flag `SIGNAL NOT FOUND` if absent from both.

## 3. Mandatory citation on every test case

Each generated case must carry the exact source (document, section/page, requirement ID) its logic came from. Makes review fast, makes hallucination visible immediately — a case with no citable source is automatically suspect.

## 4. Confidence tagging

Interaction Mapper and edge-case generation should mark output as "directly derived from documented requirement" vs. "inferred cross-module interaction — needs SME confirmation." Don't let inferred and confirmed cases look identical in the output.

## 5. Schema/enum enforcement at generation time, not review time

Validate against `Schema/test_case_schema.json` with `jsonschema` before writing a row, not after. Reject anything that doesn't match the allowed enums (`Environment`, `Test Set Category`, etc.) rather than catching it downstream.

## 6. Dedup enforced by a tool with a real similarity threshold

Never trust the model's self-report of "I checked, no duplicates." Diff against `Existing_TestCases/` (2,704 rows) and against other cases in the same batch, programmatically. Current method: exact-field match (`parent_id` + `requirement_id` + `test_set_category` + primary trigger signal) — see `definition_of_done.md` Tier 1 gate #6 for the exact rule and its known limitation (won't catch paraphrased duplicates; embedding similarity is the documented future upgrade).

## 7. Executability guardrail

Cross-check generated cases against the test bench capability list (requirement #6 in `requirements.md`, not yet built) before marking them ready. A well-written test case for hardware the lab doesn't have is dead weight.

## 8. Iteration/cost caps

Bound the agentic loop (max iterations, effort ceiling). Prevents a runaway Interaction Mapper from spiraling into low-value speculation, and caps cost per the earlier Sonnet 5 cost analysis (prompt caching + batching + per-stage effort tuning were the main levers identified).

## 9. No real user data

Since this touches the connected app, no real VINs, tokens, or account data should ever appear — even fabricated-looking ones that could be mistaken for real.

## 10. Human sign-off gate before "released"

The Reviewer stage (item 8 in the pipeline) is not the final gate for anything safety/security-relevant. Route Interaction Mapper output and any low-confidence-tagged test case to a human SME before it's considered final.
