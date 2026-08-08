from fastapi.testclient import TestClient

from service.main import app

client = TestClient(app)


def _valid_row(**overrides):
    row = {
        "sr_no": 1,
        "issue_type": "Test_01",
        "test_type_execution": "Manual",
        "summary": "To verify intrusion alert fires when a door is forced open while armed",
        "parent_id": "NIO-F001",
        "requirement_id": "NIO-F0001_INT_REQ_001",
        "test_description": "To verify intrusion alert fires when a door is forced open while armed",
        "gherkins": "Preconditions:\n1. Vehicle armed\n\nTest Steps:\n1. Force door open\n\nExpected Result:\n1. Alert fires",
        "environment": "Vehicle",
        "test_set_type": "Functional",
        "testing_agency": "TML COC",
        "test_type_validation_scope": "Full validation",
        "test_set_category": "Happy Path",
        "can_signals_referenced": "SASSUnLockAllDoorCommand | 538 | 7/1 | SASS>TCU | 1=Unlock",
        "vss_signals_referenced": "V.Auto.ABSU.ABsAct",
    }
    row.update(overrides)
    return row


def test_valid_row_passes():
    response = client.post("/tools/validate_schema", json={"row": _valid_row()})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["errors"] == []


def test_summary_description_mismatch_fails():
    row = _valid_row(test_description="A different sentence than summary")
    response = client.post("/tools/validate_schema", json={"row": row})
    body = response.json()
    assert body["valid"] is False
    assert any("byte-identical" in e for e in body["errors"])


def test_bad_environment_enum_fails():
    row = _valid_row(environment="Labcar")  # lowercase variant, not the enforced canonical casing
    response = client.post("/tools/validate_schema", json={"row": row})
    body = response.json()
    assert body["valid"] is False
    assert any("environment" in e for e in body["errors"])


def test_issue_type_sr_no_mismatch_fails():
    row = _valid_row(sr_no=2, issue_type="Test_01")
    response = client.post("/tools/validate_schema", json={"row": row})
    body = response.json()
    assert body["valid"] is False
    assert any("does not numerically match" in e for e in body["errors"])
