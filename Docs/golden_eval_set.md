# Golden Eval Set — Test Case Generation Pipeline

Started 2026-08-06. Purpose: a fixed, held-out set the pipeline gets re-run against whenever a prompt, document, or schema changes, so a regression is something you can actually detect instead of just suspect. See `requirements.md` item 8.

## Why two tiers, not one

A "golden" test case implies two things: it matches the format the pipeline is actually supposed to produce, and a human has confirmed it's correct. Nothing in this project satisfies both at once yet — the 2,704 historical rows are real and human-written, but predate the current schema (no CAN/VSS signal columns, no Test Set Category) and have never been reviewed by anyone on this project; the 3 AI-generated cases match the current schema but come from an AI, not a domain expert filing a bug report from the field. Rather than pretend either is a clean "golden set," this is split honestly into two tiers with different levels of trust.

## Tier 1 — Confirmed golden (3 cases)

`Test_89`, `Test_90`, `Test_91` in `Generated_TestCases/IntrusionAlert_AI_Generated_Sample_TestCase.xlsx`. These are the only test cases in the project matching the current schema (`Schema/test_case_schema.json`) end to end — CAN/VSS signal references, `Test Set Category`, Summary/Description byte-identical — **and** the only ones that have actually been reviewed and iterated on by a human across this project (team feedback on Summary/Description merging, the negative-case addition, the column reordering — all real review cycles, not a single rubber-stamp). Category coverage: Happy Path (`Test_90`), Negative Case (`Test_91`), Edge Case - Cross-Module Interaction (`Test_89`).

**Use**: re-run the pipeline against the same inputs (Intrusion Alert requirement docs, signal catalog, DFMEA) periodically and diff the output against these three. A material drift in the CAN/VSS signals cited, the Gherkin structure, or the category classification is a real regression signal.

## Tier 2 — Scenario-coverage candidates (12 cases, need human sign-off before promotion)

Selected from the 88 historical Intrusion Alert rows in `Existing_TestCases/UST_TML_Connected Cars_IntrusionAlert_v1.0.xlsx` (old schema — Summary column only, no CAN/VSS references, no Test Set Category). **Not yet expert-approved** — these are a reasoned shortlist, not a rubber-stamped set. Promote to Tier 1 once someone with domain knowledge confirms each one is actually correct.

**Selection logic**: the 88 rows are two parallel blocks — Sr. 1–41 run in the "Vehicle" environment, Sr. 42–87 repeat the *same* scenarios in "LabCar" (real-world instance of the environment-duplication pattern behind the dedup-exemption decision in `definition_of_done.md` gate #6). Exhaustively including every door/tailgate/bonnet/power-mode permutation would make this "large," not "golden" — picked instead for scenario-type diversity, plus one deliberate Vehicle/LabCar pair to explicitly test whether the pipeline's dedup logic correctly treats that pair as expected-recurring rather than flagging it.

| Sr. | Environment | Scenario type | Summary |
|---|---|---|---|
| 1 | Vehicle | Default-state / config check | TCM intrusion alert is enabled by default and cannot be disabled on the connected app |
| 2 | Vehicle | Happy path — Sleep mode | TCM receive the condition for Intrusion Alert from BCM in Sleep mode |
| 3 | Vehicle | Happy path — Awake mode | TCM receive the condition for Intrusion Alert from BCM in awake mode |
| 10 | Vehicle | Happy path — trigger source diversity (tailgate) | TCM receive the condition for Intrusion Alert from BCM by opening tailgate in Sleep mode |
| 12 | Vehicle | Happy path — trigger source diversity (bonnet) | TCM receive the condition for Intrusion Alert from BCM by opening bonnet in Sleep mode |
| 14 | Vehicle | Adjacent capability — location tracking bundled with alert | User receives a vehicle tracking link with the intrusion alert in Sleep mode |
| 18 | Vehicle | Negative — wrong power mode (Accessory) | TCM does not receive the condition for Intrusion Alert from BCM in Accessory mode |
| 20 | Vehicle | Negative — wrong power mode (IGN ON) | TCM does not receive the condition for Intrusion Alert from BCM in IGN ON mode |
| 36 | Vehicle | Edge case — no mobile network | Connected app does not receive the condition for Intrusion Alert in no mobile network area in Sleep mode |
| 38 | Vehicle | Edge case — deferred delivery on reconnect | Mobile app receives the Intrusion alert triggered in Sleep mode once the mobile is connected back to the network |
| 40 | Vehicle | Edge case — weak/low signal | TCM does not receive the condition for Intrusion Alert when TCM network is low/weak in Sleep mode |
| 42 | LabCar | Deliberate duplicate of Sr. 2, different environment | TCM receive the condition for Intrusion Alert from BCM in Sleep mode |

**Cross-check already worth noting**: Sr. 2 is conceptually the same scenario as `Test_90` (our Tier 1 happy path), and Sr. 18 is conceptually close to `Test_91` (our Tier 1 negative case) — this is a reasonable sanity check that the pipeline's own output lines up with what the historical human-written baseline considered a core scenario, even though neither pair is a byte-identical match.

## What's still needed to actually close this out

- Human review of the 12 Tier 2 candidates — promote to Tier 1 (or reject/replace) based on actual domain-expert sign-off, not just "this row looked reasonable."
- A defined diffing method for re-runs — right now this is "read the output and compare by eye." Once the semantic-similarity piece (`requirements.md` item 4, `architecture.md` Coverage Checker) exists, the same embedding comparison could drive an automated "did this drift" check instead.
- Coverage for other features once their generation pipelines exist — this set is Intrusion-Alert-only, matching the only feature the pipeline currently generates for.
