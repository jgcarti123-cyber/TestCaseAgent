"""Signal resolution tests, using signal names from Docs/guardrails.md's
own worked examples so the expected values are traceable to real data,
not invented fixtures.
"""

from fastapi.testclient import TestClient

from service.main import app

client = TestClient(app)


def test_found_in_unified_index():
    # ABsActive is the first entry in unified_signal_index.json.
    response = client.post("/tools/resolve_signal", json={"signal_name": "ABsActive"})
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["source"] == "unified_signal_index"
    assert body["can_message_id"] == 370
    assert body["bit_start"] == 1
    assert body["bit_length"] == 1


def test_found_via_dbc_fallback_not_in_index():
    # guardrails.md #2's worked example: not in the index (no VSS mapping),
    # but real - message SASS_Event2_RC, frame 538, bit 7, length 1.
    response = client.post("/tools/resolve_signal", json={"signal_name": "SASSUnLockAllDoorCommand"})
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["source"] in ("dbc_raw_reference", "dbc_live")
    assert body["can_message_id"] == 538
    assert body["bit_start"] == 7
    assert body["bit_length"] == 1


def test_fabricated_signal_not_found():
    # guardrails.md #1's worked example of a fabricated signal name.
    response = client.post("/tools/resolve_signal", json={"signal_name": "RemoteLockStatus"})
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is False
    assert body["flag"] == "SIGNAL NOT FOUND - flag for review"
