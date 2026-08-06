# Definition of Done — Test Case Generation Pipeline

Formal acceptance rubric for a generated test case. Two tiers, because "must always be true" and "needs judgment" are different kinds of criteria and get enforced differently. Decided 2026-08-06; see `requirements.md` item 3 and `guardrails.md` for the rules this rubric operationalizes.

## Status lifecycle

```
DRAFT  →  Tier 1 (hard gates)  →  Tier 2 (quality checks)  →  sign-off policy  →  RELEASED
                 │ any fail                │ any fail
                 ▼                         ▼
             REJECTED                 NEEDS_REVIEW
          (regenerate)             (human decides, not discarded)
```

A test case is never silently dropped. Tier 1 failure = regenerate. Tier 2 failure = route to a human, don't auto-reject — a Tier 2 check can be wrong (e.g. flagging a legitimately unusual scenario as "category mismatch"), so a person should be the one who discards it, not the pipeline.

## Tier 1 — Hard gates (automatic, binary, block release)

1. **Schema validity.** Passes `Schema/test_case_schema.json` — all required fields present, all enums valid, `sr_no`/`issue_type` numbering consistent.
2. **Signal verification — two-source check, not one.**
   - First check `Signal_Catalogs/unified_signal_index.json`. If found with `bit_position_match: true`, pass.
   - If **not** found in the index, **do not conclude `SIGNAL NOT FOUND` yet** — check the raw DBC directly (`cantools.database.load_file(...)`, search by signal name across all messages). The index only covers 2,544 of 3,593 DBC signals (70.8%) because it's built from the Master Signal Catalog, which lacks VSS mappings for ~1,375 real DBC signals. A signal missing from the index is not necessarily fake.
   - Only if the signal is absent from **both** the index and the raw DBC does it get flagged `SIGNAL NOT FOUND — flag for review`, and the test case hard-blocks (per team decision: no release with a visible-flag exception — must be resolved first).
   - **Why this two-step matters, not hypothetically:** during this rubric's own build, `Test_91`'s `SASSUnLockAllDoorCommand` signal wasn't in the index and was initially — wrongly — flagged as a likely fabrication. Checking the raw DBC directly found it exactly as used (message `SASS_Event2_RC`, frame ID 538, bit 7/length 1, receiver `TM`). It was correct all along; only the index was incomplete. See `guardrails.md` #2.
3. **Requirement traceability.** Every ID in `requirement_id` exists in `Requirement_Docs/`. No fabricated requirement IDs.
4. **Summary/Description identity.** `summary` and `test_description` are byte-identical.
5. **Category populated.** `test_set_category` is a non-empty, valid enum value.
6. **Not a duplicate — exact-field match (current method).** Flag as duplicate if `parent_id` + `requirement_id` + `test_set_category` + the primary trigger signal (first row of `can_signals_referenced`) all match an existing row in `Existing_TestCases/` or elsewhere in the same generation batch.
   - **Known limitation:** this catches true/near-identical duplicates but not paraphrased ones (same scenario, differently worded). Embedding-based semantic similarity is the documented upgrade path — see `requirements.md` item 3 follow-up — not built yet, no new infra required until it is.

## Tier 2 — Quality checks (judgment, route to NEEDS_REVIEW on failure)

1. **Category matches logic.** A `Negative Case` doesn't accidentally assert the alarm *should* fire; a `Happy Path` doesn't contain a failure-path assertion.
2. **No orphan signal claims.** Every signal value asserted in the Gherkins `Expected Result` section appears somewhere in `can_signals_referenced` / `vss_signals_referenced` — nothing referenced in prose that isn't also in the structured columns.
3. **Specific and repeatable steps.** Exact wait times, exact signal values, exact trigger actions — no "wait some time" or "check if it works." Two different lab engineers should be able to execute the same test case identically.
4. **Confidence tag present and accurate.** Marked "directly derived from documented requirement" vs. "inferred cross-module interaction — needs SME confirmation," and the tag actually matches how the case was produced (an Interaction-Mapper-sourced edge case should never be silently marked as directly-derived).

## Human sign-off policy (before "released", after all automated checks pass)

- **Mandatory human sign-off**: any `test_set_category` starting with `Edge Case -` (Cross-Module Interaction, Signal Fault/Boundary, DFMEA-Derived), and any case confidence-tagged "inferred." Matches `guardrails.md` #10 exactly — not a new rule, just formalized as a release gate here.
- **Can auto-release once Tier 1 + Tier 2 pass**: `Happy Path`, `Negative Case`. Lower risk, directly traceable, no inference involved.
- **`User-Journey`** category: treat as mandatory-review until there's a track record — it involves the connected app / user-facing behavior, not just CAN state, and hasn't been exercised by this rubric yet.

## Worked example — applied to the 3 existing generated test cases (2026-08-06)

| Test | Category | Tier 1 | Tier 2 | Sign-off required? | Status |
|---|---|---|---|---|---|
| Test_89 | Edge Case - Cross-Module Interaction | Pass (11/11 signals verified) | Pass | Yes (Edge Case) | NEEDS_REVIEW — awaiting human |
| Test_90 | Happy Path | Pass (6/6 signals verified) | Pass | No | Eligible for RELEASED |
| Test_91 | Negative Case | Pass (8/8 signals verified — see two-source note above) | Pass | No | Eligible for RELEASED |

This is the rubric doing its job as intended: the one case that actually needed a second pair of eyes (a cross-module race condition, inferred rather than directly stated in any single requirement) is the one the policy holds back. The other two, which are directly traceable to explicit requirement text, don't need to wait on a human.
