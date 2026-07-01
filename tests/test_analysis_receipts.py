from aoc_supervisor.analysis_receipts import build_analysis_receipt, validate_receipt


def test_validate_receipt_success():
    receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )
    result = validate_receipt(receipt)
    assert result.ok is True
    assert not result.errors


def test_validate_receipt_missing_fields():
    valid_receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )

    fields_to_test = ("receipt_id", "timestamp", "provider_id", "model_id", "policy_version", "next_action")
    for field in fields_to_test:
        bad_receipt = valid_receipt.copy()
        bad_receipt[field] = " "  # Empty or whitespace
        result = validate_receipt(bad_receipt)
        assert result.ok is False
        assert any(f"receipt missing {field}" in e for e in result.errors)


def test_validate_receipt_invalid_digests():
    valid_receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )

    # Invalid prefix
    bad_receipt = valid_receipt.copy()
    bad_receipt["input_digest"] = "md5:" + "a" * 32
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt has invalid input_digest" in e for e in result.errors)

    # Invalid length
    bad_receipt = valid_receipt.copy()
    bad_receipt["output_digest"] = "sha256:abc"
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt has invalid output_digest" in e for e in result.errors)

    # None value
    bad_receipt = valid_receipt.copy()
    bad_receipt["input_digest"] = None
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt has invalid input_digest" in e for e in result.errors)


def test_validate_receipt_invalid_status():
    valid_receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )

    bad_receipt = valid_receipt.copy()
    bad_receipt["status"] = "invalid_status"
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt status invalid: invalid_status" in e for e in result.errors)


def test_validate_receipt_numeric_validation():
    valid_receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )

    # Negative revision
    bad_receipt = valid_receipt.copy()
    bad_receipt["analysis_revision"] = -1
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt analysis_revision must be non-negative" in e for e in result.errors)

    # Non-integer revision (using dict directly as build_analysis_receipt would cast it)
    bad_receipt = valid_receipt.copy()
    bad_receipt["evidence_revision"] = "not-an-int"
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt evidence_revision must be an integer" in e for e in result.errors)

    # Non-numeric readiness score
    bad_receipt = valid_receipt.copy()
    bad_receipt["readiness_score"] = "high"
    result = validate_receipt(bad_receipt)
    assert result.ok is False
    assert any("receipt readiness_score must be numeric" in e for e in result.errors)


def test_validate_receipt_hidden_fields():
    valid_receipt = build_analysis_receipt(
        input_digest="sha256:" + "a" * 64,
        output_digest="sha256:" + "b" * 64,
        provider_id="test-provider",
        model_id="test-model",
        policy_version="1.0",
        analysis_revision=1,
        evidence_revision=1,
        next_action="ASK",
        readiness_score=0.8,
        ready_to_finalize=False,
    )

    for hidden in ("chain_of_thought", "raw_model_output", "private_reasoning"):
        bad_receipt = valid_receipt.copy()
        bad_receipt[hidden] = "secret"
        result = validate_receipt(bad_receipt)
        assert result.ok is False
        assert any(f"receipt must not contain hidden field: {hidden}" in e for e in result.errors)


def test_validate_receipt_not_an_object():
    result = validate_receipt("not a dict")
    assert result.ok is False
    assert "receipt must be an object" in result.errors
