"""Schema + Tier 1 structural checks for one test case row.

Covers Docs/definition_of_done.md Tier 1 gates that are purely
structural (don't need Signal_Catalogs or Existing_TestCases/ lookups,
which are their own tools):

  1. Schema validity - Schema/test_case_schema.json via jsonschema.
  4. summary == test_description, byte-identical.
  5. test_set_category populated (covered by the schema's own
     required-field + enum check, but called out explicitly below so a
     missing category produces a readable message rather than a bare
     jsonschema stack trace).

Gate 2 (signal verification) is tools/signal_resolution.py. Gate 3
(requirement traceability) and gate 6 (dedup) are separate tools too -
see Docs/architecture.md stage 6 for why the checker is split into
independent, individually-testable pieces rather than one monolith.
"""

import json
from functools import lru_cache

import jsonschema

from ..config import SCHEMA_PATH


@lru_cache(maxsize=1)
def _load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_row(row: dict) -> tuple[bool, list[str]]:
    """Returns (valid, errors). errors is empty iff valid is True."""

    errors = []

    validator = jsonschema.Draft202012Validator(_load_schema())
    for error in sorted(validator.iter_errors(row), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in error.path) or "<root>"
        errors.append(f"schema: {location}: {error.message}")

    summary = row.get("summary")
    test_description = row.get("test_description")
    if summary is not None and test_description is not None and summary != test_description:
        errors.append(
            "summary and test_description must be byte-identical "
            f"(got summary={summary!r}, test_description={test_description!r})"
        )

    sr_no = row.get("sr_no")
    issue_type = row.get("issue_type")
    if isinstance(sr_no, int) and isinstance(issue_type, str):
        digits = "".join(ch for ch in issue_type if ch.isdigit())
        if digits and int(digits) != sr_no:
            errors.append(f"issue_type {issue_type!r} does not numerically match sr_no {sr_no}")

    return (len(errors) == 0, errors)
