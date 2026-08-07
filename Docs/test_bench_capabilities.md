# Test Bench Capability List — Test Case Generation Pipeline

Started 2026-08-06, substantially answered 2026-08-07. See `requirements.md` item 6.

## Confirmed environments

Four: `LabCar`, `Vehicle`, `Bench`, and **`HIL`** (Hardware-in-the-Loop) — the fourth confirmed 2026-08-06, matching a Jira `Environment` field value never actually used in Intrusion Alert's test history until now.

## HIL capability — real data, not inferred (2026-08-07)

Team provided `HIL_Automation/Keywords.xlsx` — the actual HIL rig automation keyword library (also parsed into `HIL_Automation/hil_keyword_index.json` for programmatic lookup; see that file's `parsing_caveats` field before trusting every module — CAN, Fault Insertion Unit, GNSS, and Cellular Network were manually spot-checked against the source and match; a few others weren't). This is real hardware capability data, not something inferred or guessed.

**Confirmed: HIL can inject any signal defined in the loaded DBC file**, via the CAN module (`hil.simulation.can` — NI PXIe 8510, 4 channels, 5 Mbps). Key keywords:

| Keyword | What it does |
|---|---|
| `Add CANX Database` | Load a DBC file for the simulation |
| `Set CANX Signals` | Set arbitrary signal values by name — cyclic or event-triggered |
| `Set CANX Configuration` | Modify baudrate/database/termination from DBC config |
| `Check CANX Signal` | Validate an actual signal value against an expected value + tolerance |
| `Check CANX Message` | Validate a full frame (by name, ID, or payload) |
| `Send CANX Raw Message` | Inject an arbitrary raw CAN/CAN-FD frame, including UDS |
| `Get CANX Bus Load` | Read current bus load % |

This directly resolves the open question from the earlier pass: fault/boundary-condition test cases (e.g. setting `IntrusionInfoState` directly without physically opening a door) are realistically executable on HIL.

**Also confirmed: dedicated fault-injection hardware exists**, separate from CAN signal-setting — the **Fault Insertion Unit** (`hil.simulation.fault` — NI PXI 2510, 68 channels, 2 buses). Keywords: `Open FIU "Channel"` (open-circuit a channel — simulates a disconnected sensor) and `Short FIU Group` (short-circuit a group of channels). **This is the concrete answer to whether `SIGNAL NOT FOUND` / implausible-signal conditions are physically testable, not just settable via CAN injection** — a genuinely disconnected/faulted sensor can be reproduced at the hardware level, not just simulated by writing a signal value.

## Full HIL module list (from `hil_keyword_index.json`)

19–20 modules total, covering far more than CAN. Ones most relevant to this pipeline beyond CAN/FIU:

| Module | Namespace | Relevance |
|---|---|---|
| GNSS | `hil.simulation.gnss` | Location-dependent scenarios (geofencing, tracking-link features) |
| Cellular Network | `hil.simulation.bse` | Network availability/signal-strength scenarios (the "no mobile network" / "weak signal" edge cases already in `golden_eval_set.md`) |
| Programmable Power Supply | `hil.simulation.pps` | Battery/power-mode scenarios |
| Analog/Digital I/O | `hil.simulation.io` | Generic discrete signal simulation beyond CAN |
| Mobile Application Tester | `hil.validation.mobileapp` | Validating the actual mobile app response, not just the CAN side |
| Bluetooth / Wi-Fi | `hil.simulation.bluetooth` / `hil.simulation.wifi` | Connectivity-dependent scenarios |

Full detail (every keyword, input/output params, per module) is in `HIL_Automation/hil_keyword_index.json` — query it rather than re-reading `Keywords.xlsx` by hand.

## New implication for Gherkin generation

`HIL_Automation/Keywords.xlsx`'s `Sheet1` (App Automation Tester keywords) gives **exact Gherkin phrasing** for mobile-app-side actions (e.g. `I Set TimeFence StartTime "5 mins" later than current time`). This means Gherkin steps the pipeline generates for HIL-executed test cases should prefer these real keywords over free-prose descriptions where an equivalent keyword exists — otherwise the generated Gherkin reads fine to a human but isn't actually executable by the real automation harness. See `guardrails.md` for this as a new rule.

## Still open

- Full validation of the parsing caveats noted in `hil_keyword_index.json` (Automotive Ethernet / Bluetooth showing 0 entries, Mobile Application Tester keyword-module name mismatch, Wi-Fi signal/keyword count gap).
- `LabCar`/`Vehicle`/`Bench` (non-HIL) capability detail — this pass only substantially answered HIL. The other three environments' capability matrices are still not documented beyond "used historically for physical-trigger scenarios."
