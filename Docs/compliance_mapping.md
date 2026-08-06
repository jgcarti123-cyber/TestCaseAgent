# Compliance / Safety Mapping — Test Case Generation Pipeline

Started 2026-08-06. See `requirements.md` item 7. Purpose: let test case severity/priority reflect a real regulatory or functional-safety classification, if one exists for the feature.

## What was checked before asking (2026-08-06)

Confirmed absent from every local source, not just "not found because I didn't look":

- **DFMEA** (`Requirement_Docs/TML_4G TCU_DFMEA_Hardware_V0.1_20260326.xlsx`, `HW DFMEA` sheet): zero mentions of "Intrusion" anywhere — this document is generic 4G TCU hardware failure-mode analysis (S/O/D ratings per component), not feature-specific, and doesn't address Intrusion Alert at all.
- **All 5 requirement PDFs** (`Requirement_Docs/*.pdf`, 523 pages total): searched for `ASIL`, `UNECE`, `R155`, `R156`, `ISO 26262`, `functional safety`, `cybersecurity classification` — zero matches across every page of every document.

So this genuinely isn't documented anywhere in the local project files.

## Status (2026-08-06)

Both open, pending your safety/compliance team — not something either of us can resolve by searching further:

| Classification | Status | Notes |
|---|---|---|
| **ASIL** (ISO 26262) | Unknown — needs safety team confirmation | If Intrusion Alert has no safety-relevant failure mode (arguably true — a missed intrusion alert doesn't itself cause a safety hazard the way a braking or steering failure would), it may simply be `QM` (no ASIL requirement), which would also explain why it's undocumented. Don't assume this though — confirm rather than infer. |
| **UNECE R155** (cybersecurity) | Unknown — needs safety/compliance team confirmation | Worth checking specifically for this feature: unlike a generic ASIL question, Intrusion Alert is explicitly a security-relevant feature (detects unauthorized vehicle entry), which is the kind of feature R155's cybersecurity management system requirements are usually most relevant to. |

## What this means for the pipeline in the meantime

Test case severity/priority currently has no formal-classification input to draw from. Until this resolves, `Schema/test_case_schema.json` and `definition_of_done.md` stay as they are — severity signal comes from `Test Set Category` (Edge Case categories already get mandatory human sign-off) and, where available, the real Jira bug `severity` field (`Docs/traceability.md`) — not from an ASIL/R155 rating that doesn't exist in accessible form yet.

## Next step

Get an answer from the safety/compliance team on both rows in the table above. If either classification exists, update this file with the real value and its source document, then revisit whether `definition_of_done.md`'s human-sign-off policy should tighten for this feature specifically.
