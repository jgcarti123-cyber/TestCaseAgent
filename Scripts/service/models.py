"""Pydantic request/response models for the tool endpoints.

One model pair per tool in Docs/tools.md's "Needed, not yet built" table.
Kept separate from the tool implementations (tools/*.py) so the HTTP
contract can be reviewed independent of the lookup logic.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---- /tools/resolve_signal ----------------------------------------------


class ResolveSignalRequest(BaseModel):
    signal_name: str = Field(..., min_length=1, description="Exact DBC signal name, e.g. 'SASSUnLockAllDoorCommand'.")


class ResolveSignalResponse(BaseModel):
    signal_name: str
    found: bool
    source: Optional[Literal["unified_signal_index", "dbc_raw_reference", "dbc_live"]] = None
    can_message_id: Optional[int] = None
    message_name: Optional[str] = None
    bit_start: Optional[int] = None
    bit_length: Optional[int] = None
    vss_path: Optional[str] = None
    possible_values: Optional[dict] = None
    bit_position_match: Optional[bool] = Field(
        None, description="Only meaningful for source='unified_signal_index' — whether catalog and DBC bit positions agree (see guardrails.md #2)."
    )
    ambiguous: bool = Field(
        False, description="True when the raw DBC defines this signal name on more than one message — see all_matches. Never silently picked one; caller/human must disambiguate."
    )
    all_matches: Optional[list[dict]] = Field(
        None, description="Populated only when ambiguous=true — every message-level definition found for this signal name."
    )
    flag: Optional[str] = Field(
        None, description="'SIGNAL NOT FOUND - flag for review' when found=false, or an ambiguity flag when ambiguous=true, per guardrails.md #1. Never populate a guess instead."
    )
    raw: Optional[dict] = Field(None, description="Full source record, for traceability/debugging.")


# ---- /tools/validate_schema ----------------------------------------------


class ValidateSchemaRequest(BaseModel):
    row: dict[str, Any] = Field(..., description="One candidate test case row, keyed by the schema's property names (see Schema/test_case_schema.json).")


class ValidateSchemaResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list, description="Human-readable validation failures, schema violations first, then the extra Tier 1 gates (summary/description identity, sr_no/issue_type numbering).")


# ---- /tools/check_dedup ----------------------------------------------


class DedupCandidate(BaseModel):
    parent_id: str
    requirement_id: str
    test_set_category: str
    primary_trigger_signal: str = Field(..., description="First row of can_signals_referenced — the exact-match key per definition_of_done.md Tier 1 gate #6.")


class CheckDedupRequest(BaseModel):
    candidate: DedupCandidate
    batch: list[DedupCandidate] = Field(default_factory=list, description="Other rows in the same generation batch, checked alongside Generated_TestCases/.")


class DedupMatch(BaseModel):
    source: Literal["batch", "generated_test_cases"]
    location: str = Field(..., description="Batch index, or 'file.xlsx:row N' for Generated_TestCases matches.")


class CheckDedupResponse(BaseModel):
    is_duplicate: bool
    blocking: bool = Field(..., description="True only if is_duplicate and test_set_category is in DEDUP_BLOCKING_CATEGORIES (Edge Case - */User-Journey). See guardrails.md #6.")
    matches: list[DedupMatch] = Field(default_factory=list)
    unchecked_sources: list[str] = Field(
        default_factory=list,
        description="Sources this check could not meaningfully cover, and why — never silently pretend coverage. See Docs/tools.md 'Dedup/similarity tool'.",
    )
