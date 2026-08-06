# Test Bench Capability List — Test Case Generation Pipeline

Started 2026-08-06. See `requirements.md` item 6. Purpose: don't generate a test case for a fault condition the physical/simulated rig can't actually produce.

## Confirmed environments (2026-08-06)

Four, not three — local historical data (`Existing_TestCases/`) only ever used `LabCar`/`Vehicle` for Intrusion Alert, and the formal schema (`Schema/test_case_schema.json`) only enumerates `LabCar`/`Vehicle`/`Bench`. Team confirmed a fourth is also real and relevant: **`HIL`** (Hardware-in-the-Loop) — this matches a value already present in Jira's own `Environment` custom field (`customfield_10155` on the Validation Bug issue type) that just hadn't shown up in this feature's test history yet.

**Action needed**: `Schema/test_case_schema.json`'s `environment` enum currently only has `LabCar`/`Vehicle`/`Bench` — needs `HIL` added once the capability detail below is filled in enough to actually generate HIL-targeted test cases correctly.

## Confirmed capability

**At least one rig supports direct CAN signal injection** — setting a signal value (e.g. `IntrusionInfoState = 1`) directly via a bus tool, without physically triggering the real sensor/actuator (e.g. actually opening a door). This matters a lot: it's what makes fault/boundary-condition test cases (`SIGNAL NOT FOUND`, implausible values, `IntrusionInfoStateStatus = 3`) realistically executable rather than theoretical.

## Still needed — genuinely needs a domain expert, not more agent investigation

- **Which specific environment(s)** support direct CAN injection — confirmed "at least one," not yet confirmed which. Matters because it determines which environment a fault/boundary-condition test case should be assigned to.
- **Per-environment capability matrix** — for each of LabCar / Vehicle / Bench / HIL: what can it physically or programmatically produce? E.g., can any rig simulate a real GPS/cellular signal degradation (relevant to the "no mobile network" / "low signal" scenarios already in the historical test suite, Sr. 36/40 in `golden_eval_set.md`)? Can any rig simulate multi-module race conditions (relevant to `Test_89`'s cross-module interaction category)?
- **What's explicitly NOT possible** — the inverse of the above. Knowing what can't be tested is as valuable as knowing what can, since it's a hard constraint on what the pipeline should ever propose generating.

Once this is filled in, the Test Case Generator stage (`architecture.md`) should cross-check every proposed test case's required environment/signal-injection capability against this list before finalizing — a test case for a fault condition no rig can produce should either be flagged or reassigned, not silently generated as if it were executable.
