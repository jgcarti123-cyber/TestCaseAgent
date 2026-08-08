"""HTTP surface for the deterministic pipeline tools.

Endpoint list matches Docs/tools.md's "Needed, not yet built" table.
Each deterministic tool (resolve_signal, validate_schema, check_dedup)
wraps a pure function in tools/ so the lookup logic stays unit-testable
without spinning up the app. Endpoints not yet backed by real logic
return 501 with a pointer to the doc explaining why, rather than a
fake/partial answer - see Docs/guardrails.md #1 on never producing a
plausible-looking guess in place of "not resolved yet."
"""

from fastapi import APIRouter, HTTPException

from ..models import (
    CheckDedupRequest,
    CheckDedupResponse,
    ResolveSignalRequest,
    ResolveSignalResponse,
    ValidateSchemaRequest,
    ValidateSchemaResponse,
)
from ..tools import dedup as dedup_tool
from ..tools import schema_validation
from ..tools import signal_resolution

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/resolve_signal", response_model=ResolveSignalResponse)
def resolve_signal(request: ResolveSignalRequest) -> dict:
    return signal_resolution.resolve_signal(request.signal_name)


@router.post("/validate_schema", response_model=ValidateSchemaResponse)
def validate_schema(request: ValidateSchemaRequest) -> dict:
    valid, errors = schema_validation.validate_row(request.row)
    return {"valid": valid, "errors": errors}


@router.post("/check_dedup", response_model=CheckDedupResponse)
def check_dedup(request: CheckDedupRequest) -> dict:
    candidate = request.candidate.model_dump()
    batch = [item.model_dump() for item in request.batch]
    return dedup_tool.check_dedup(candidate, batch)


@router.post("/hil_keyword_lookup")
def hil_keyword_lookup():
    raise HTTPException(
        status_code=501,
        detail=(
            "Not built yet - see Docs/tools.md 'HIL keyword lookup tool' (Medium priority, added "
            "2026-08-07). HIL_Automation/hil_keyword_index.json exists and is real, but the query "
            "tool over it (intended action -> real keyword, per guardrails.md #11) isn't wired up."
        ),
    )


@router.post("/jira_traceability_check")
def jira_traceability_check():
    raise HTTPException(
        status_code=501,
        detail=(
            "Not built yet - see Docs/tools.md 'Service-side Jira/Xray auth'. The Atlassian MCP "
            "connector used so far is session-scoped OAuth (interactive /mcp), not something a "
            "deployed service can call the same way; needs a service-account auth pattern first. "
            "Traceability/requirement_traceability.json can be read directly in the meantime."
        ),
    )
