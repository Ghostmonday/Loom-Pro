"""Focused unit tests for analysis receipt validation."""

import pytest
from aoc_supervisor.analysis_receipts import validate_receipt


@pytest.fixture
def valid_receipt():
    """Returns a perfectly valid analysis receipt."""
    return {
        "receipt_id": "rcpt_1234567890ab",
        "timestamp": "2023-10-27T10:00:00Z",
        "provider_id": "openai",
        "model_id": "gpt-4",
        "policy_version": "2.0.0-adaptive",
        "next_action": "FINALIZE",
        "status": "completed",
        "input_digest": "sha256:" + "a" * 64,
        "output_digest": "sha256:" + "b" * 64,
        "analysis_revision": 1,
        "evidence_revision": 1,
        "readiness_score": 0.95,
        "ready_to_finalize": True,
    }


def test_validate_receipt_success(valid_receipt):
    """Verifies that a valid receipt passes validation."""
    result = validate_receipt(valid_receipt)
    assert result.ok is True
    assert not result.errors


def test_validate_receipt_not_dict():
    """Verifies that a non-dict input fails validation."""
    result = validate_receipt(["not", "a", "dict"])
    assert result.ok is False
    assert "receipt must be an object" in result.errors


def test_validate_receipt_missing_required_fields(valid_receipt):
    """Verifies that missing required fields trigger validation errors."""
    required_fields = ("receipt_id", "timestamp", "provider_id", "model_id", "policy_version", "next_action")
    for field in required_fields:
        invalid_receipt = valid_receipt.copy()
        del invalid_receipt[field]
        result = validate_receipt(invalid_receipt)
        assert result.ok is False
        assert any(f"receipt missing {field}" in err for err in result.errors)


def test_validate_receipt_empty_required_fields(valid_receipt):
    """Verifies that empty/whitespace required fields trigger validation errors."""
    required_fields = ("receipt_id", "timestamp", "provider_id", "model_id", "policy_version", "next_action")
    for field in required_fields:
        invalid_receipt = valid_receipt.copy()
        invalid_receipt[field] = "  "
        result = validate_receipt(invalid_receipt)
        assert result.ok is False
        assert any(f"receipt missing {field}" in err for err in result.errors)


def test_validate_receipt_invalid_digests(valid_receipt):
    """Verifies validation of input_digest and output_digest."""
    digest_fields = ("input_digest", "output_digest")
    invalid_values = [
        "not-a-digest",
        "sha256:short",
        "sha256:" + "G" * 64,  # non-hex
        None,
    ]
    for field in digest_fields:
        for value in invalid_values:
            invalid_receipt = valid_receipt.copy()
            invalid_receipt[field] = value
            result = validate_receipt(invalid_receipt)
            assert result.ok is False
            assert any(f"receipt has invalid {field}" in err for err in result.errors)


def test_validate_receipt_invalid_status(valid_receipt):
    """Verifies validation of the status field."""
    invalid_receipt = valid_receipt.copy()
    invalid_receipt["status"] = "unknown_status"
    result = validate_receipt(invalid_receipt)
    assert result.ok is False
    assert any("receipt status invalid" in err for err in result.errors)


def test_validate_receipt_invalid_numeric_fields(valid_receipt):
    """Verifies validation of analysis_revision and evidence_revision."""
    numeric_fields = ("analysis_revision", "evidence_revision")
    # We use "1.5" (string) because int(1.5) (float) would succeed in Python
    # but the intent is to catch non-integer values.
    invalid_values = ["not-an-int", -5, "1.5"]
    for field in numeric_fields:
        for value in invalid_values:
            invalid_receipt = valid_receipt.copy()
            invalid_receipt[field] = value
            result = validate_receipt(invalid_receipt)
            assert result.ok is False
            assert any(f"receipt {field} must be" in err for err in result.errors)


def test_validate_receipt_invalid_readiness_score(valid_receipt):
    """Verifies validation of the readiness_score field."""
    invalid_receipt = valid_receipt.copy()
    invalid_receipt["readiness_score"] = "not-a-float"
    result = validate_receipt(invalid_receipt)
    assert result.ok is False
    assert any("receipt readiness_score must be numeric" in err for err in result.errors)


def test_validate_receipt_forbidden_hidden_fields(valid_receipt):
    """Verifies that hidden fields are forbidden."""
    hidden_fields = ("chain_of_thought", "raw_model_output", "private_reasoning")
    for hidden in hidden_fields:
        invalid_receipt = valid_receipt.copy()
        invalid_receipt[hidden] = "some-internal-data"
        result = validate_receipt(invalid_receipt)
        assert result.ok is False
        assert any(f"receipt must not contain hidden field: {hidden}" in err for err in result.errors)
