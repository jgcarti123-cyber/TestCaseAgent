"""Paths and settings shared by every tool module in the service.

Mirrors the folder map in Docs/architecture.md. Centralized here so a
future repo-layout change (e.g. splitting Signal_Catalogs onto a shared
volume in a real deployment) touches one file, not every tool module.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = REPO_ROOT / "Schema" / "test_case_schema.json"

SIGNAL_CATALOGS_DIR = REPO_ROOT / "Signal_Catalogs"
SIGNAL_INDEX_PATH = SIGNAL_CATALOGS_DIR / "unified_signal_index.json"
DBC_RAW_REFERENCE_PATH = SIGNAL_CATALOGS_DIR / "dbc_raw_reference.json"
DBC_FILE_PATH = SIGNAL_CATALOGS_DIR / "TML_IVN_Communication_Matrix_CM_CANFD_V1.1.5_TM.dbc"

EXISTING_TEST_CASES_DIR = REPO_ROOT / "Existing_TestCases"
GENERATED_TEST_CASES_DIR = REPO_ROOT / "Generated_TestCases"
TRACEABILITY_PATH = REPO_ROOT / "Traceability" / "requirement_traceability.json"
HIL_KEYWORD_INDEX_PATH = REPO_ROOT / "HIL_Automation" / "hil_keyword_index.json"

# Tier 1 gate #6 (Docs/definition_of_done.md) only blocks release for these
# categories; Happy Path / Negative Case matches are expected regression
# coverage and are logged, never blocked. See guardrails.md #6.
DEDUP_BLOCKING_CATEGORIES = {
    "Edge Case - Cross-Module Interaction",
    "Edge Case - Signal Fault/Boundary",
    "Edge Case - DFMEA-Derived",
    "User-Journey",
}
