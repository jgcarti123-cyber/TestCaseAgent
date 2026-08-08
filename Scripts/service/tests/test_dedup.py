from fastapi.testclient import TestClient

from service.main import app

client = TestClient(app)


def _candidate(**overrides):
    c = {
        "parent_id": "NIO-F001",
        "requirement_id": "NIO-F0001_INT_REQ_001",
        "test_set_category": "Happy Path",
        "primary_trigger_signal": "SASSUnLockAllDoorCommand",
    }
    c.update(overrides)
    return c


def test_no_match_when_batch_empty_and_nothing_generated_yet():
    response = client.post("/tools/check_dedup", json={"candidate": _candidate(), "batch": []})
    assert response.status_code == 200
    body = response.json()
    assert body["is_duplicate"] is False
    assert body["blocking"] is False
    assert len(body["unchecked_sources"]) == 2


def test_batch_match_on_happy_path_is_duplicate_but_not_blocking():
    candidate = _candidate()
    response = client.post("/tools/check_dedup", json={"candidate": candidate, "batch": [candidate]})
    body = response.json()
    assert body["is_duplicate"] is True
    assert body["blocking"] is False  # Happy Path is never blocking, per guardrails.md #6
    assert body["matches"][0]["source"] == "batch"


def test_batch_match_on_edge_case_is_blocking():
    candidate = _candidate(test_set_category="Edge Case - Cross-Module Interaction")
    response = client.post("/tools/check_dedup", json={"candidate": candidate, "batch": [candidate]})
    body = response.json()
    assert body["is_duplicate"] is True
    assert body["blocking"] is True


def test_different_signal_does_not_match():
    candidate = _candidate()
    other = _candidate(primary_trigger_signal="SomeOtherSignal")
    response = client.post("/tools/check_dedup", json={"candidate": candidate, "batch": [other]})
    body = response.json()
    assert body["is_duplicate"] is False
