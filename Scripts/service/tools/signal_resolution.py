"""Deterministic CAN/VSS signal resolution — never LLM free-generation.

Two-source lookup order, per Docs/guardrails.md #1/#2 and
Docs/definition_of_done.md Tier 1 gate #2:

  1. Signal_Catalogs/unified_signal_index.json (covers 70.8% of DBC
     signals - built from the Master Signal Catalog, which lacks a VSS
     mapping for ~1,375 real DBC signals).
  2. If not found there, the raw DBC directly - first the pre-parsed
     Signal_Catalogs/dbc_raw_reference.json cache, then (if even that
     cache misses, e.g. it goes stale relative to the .dbc) a live
     cantools parse of the .dbc file itself, which is the actual ground
     truth the cache is derived from.

Only if a signal is absent from all three does it come back
found=false - "not in the derived index" is not the same as "doesn't
exist" (this is exactly the mistake guardrails.md #2 documents almost
happening on Test_91's SASSUnLockAllDoorCommand).
"""

import json
from functools import lru_cache
from typing import Optional

from ..config import DBC_FILE_PATH, DBC_RAW_REFERENCE_PATH, SIGNAL_INDEX_PATH


@lru_cache(maxsize=1)
def _load_signal_index() -> list[dict]:
    with open(SIGNAL_INDEX_PATH) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_dbc_raw_reference() -> dict[str, list[dict]]:
    # Each value is a list, not a single dict - the same signal name can
    # legitimately be defined on more than one message (28 such names as
    # of this build). Collapsing to "first match" would be exactly the
    # kind of silent guess guardrails.md #1 exists to prevent.
    with open(DBC_RAW_REFERENCE_PATH) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_dbc_database():
    # Deferred import: cantools + a 4.9MB .dbc parse (~1s) only pays off
    # if the two cheaper sources above both miss.
    import cantools

    return cantools.database.load_file(str(DBC_FILE_PATH))


def _search_index(signal_name: str) -> Optional[dict]:
    for entry in _load_signal_index():
        if entry.get("dbc_signal_name") == signal_name:
            return entry
    return None


def _search_dbc_raw_reference(signal_name: str) -> Optional[list[dict]]:
    return _load_dbc_raw_reference().get(signal_name)


def _search_dbc_live(signal_name: str) -> Optional[list[dict]]:
    db = _load_dbc_database()
    matches = []
    for message in db.messages:
        for signal in message.signals:
            if signal.name == signal_name:
                matches.append(
                    {
                        "message_id": message.frame_id,
                        "message_name": message.name,
                        "bit_start": signal.start,
                        "bit_length": signal.length,
                        "byte_order": signal.byte_order,
                        "scale": signal.scale,
                        "offset": signal.offset,
                        "unit": signal.unit,
                        "choices": dict(signal.choices) if signal.choices else None,
                    }
                )
    return matches or None


def _response_from_dbc_matches(signal_name: str, source: str, matches: list[dict]) -> dict:
    if len(matches) > 1:
        return {
            "signal_name": signal_name,
            "found": True,
            "source": source,
            "can_message_id": None,
            "message_name": None,
            "bit_start": None,
            "bit_length": None,
            "vss_path": None,
            "possible_values": None,
            "bit_position_match": None,
            "ambiguous": True,
            "all_matches": matches,
            "flag": f"AMBIGUOUS - {len(matches)} messages define a signal named {signal_name!r}, see all_matches - do not pick one without confirming which message applies",
            "raw": None,
        }

    match = matches[0]
    return {
        "signal_name": signal_name,
        "found": True,
        "source": source,
        "can_message_id": match.get("message_id"),
        "message_name": match.get("message_name"),
        "bit_start": match.get("bit_start"),
        "bit_length": match.get("bit_length"),
        "vss_path": None,
        "possible_values": match.get("choices"),
        "bit_position_match": None,
        "ambiguous": False,
        "all_matches": None,
        "flag": None,
        "raw": match,
    }


def resolve_signal(signal_name: str) -> dict:
    """Look up one signal by exact name. Returns a dict matching ResolveSignalResponse."""

    index_hit = _search_index(signal_name)
    if index_hit is not None:
        return {
            "signal_name": signal_name,
            "found": True,
            "source": "unified_signal_index",
            "can_message_id": index_hit.get("can_message_id"),
            "message_name": index_hit.get("dbc_message_name"),
            "bit_start": index_hit.get("bit_start_dbc", index_hit.get("bit_start_catalog")),
            "bit_length": index_hit.get("bit_length_dbc", index_hit.get("bit_length_catalog")),
            "vss_path": index_hit.get("vss_path"),
            "possible_values": index_hit.get("possible_values"),
            "bit_position_match": index_hit.get("bit_position_match"),
            "ambiguous": False,
            "all_matches": None,
            "flag": None,
            "raw": index_hit,
        }

    raw_hit = _search_dbc_raw_reference(signal_name)
    if raw_hit is not None:
        return _response_from_dbc_matches(signal_name, "dbc_raw_reference", raw_hit)

    live_hit = _search_dbc_live(signal_name)
    if live_hit is not None:
        return _response_from_dbc_matches(signal_name, "dbc_live", live_hit)

    return {
        "signal_name": signal_name,
        "found": False,
        "source": None,
        "can_message_id": None,
        "message_name": None,
        "bit_start": None,
        "bit_length": None,
        "vss_path": None,
        "possible_values": None,
        "bit_position_match": None,
        "ambiguous": False,
        "all_matches": None,
        "flag": "SIGNAL NOT FOUND - flag for review",
        "raw": None,
    }
