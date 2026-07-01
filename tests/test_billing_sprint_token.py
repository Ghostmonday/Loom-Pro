from unittest.mock import patch

import pytest
from aoc_supervisor.billing import (
    SprintTokenException,
    clear_sprint_tokens,
    issue_sprint_token,
    validate_sprint_token,
)


@pytest.fixture(autouse=True)
def clean_tokens():
    clear_sprint_tokens()
    yield
    clear_sprint_tokens()


def test_validate_sprint_token_success():
    token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00")
    token = token_record["token"]

    result = validate_sprint_token(token, user_id="user1", workers=4)
    assert result["token"] == token
    assert result["used"] is False


def test_validate_sprint_token_consume():
    token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00")
    token = token_record["token"]

    # First validation with consume=True
    result = validate_sprint_token(token, user_id="user1", workers=4, consume=True)
    assert result["used"] is True

    # Second validation should fail
    with pytest.raises(SprintTokenException, match="sprint_token has already been used"):
        validate_sprint_token(token, user_id="user1", workers=4)


def test_validate_sprint_token_required():
    with pytest.raises(SprintTokenException, match="sprint_token is required"):
        validate_sprint_token("", user_id="user1")


def test_validate_sprint_token_invalid():
    with pytest.raises(SprintTokenException, match="sprint_token is invalid"):
        validate_sprint_token("non-existent", user_id="user1")


def test_validate_sprint_token_user_mismatch():
    token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00")
    token = token_record["token"]

    with pytest.raises(SprintTokenException, match="sprint_token does not match the requesting account"):
        validate_sprint_token(token, user_id="user2")


def test_validate_sprint_token_worker_mismatch():
    token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00")
    token = token_record["token"]

    with pytest.raises(SprintTokenException, match="sprint_token worker_count does not match request"):
        validate_sprint_token(token, user_id="user1", workers=5)


def test_validate_sprint_token_expired():
    with patch("time.time", return_value=1000.0):
        token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00", ttl_seconds=60)
        token = token_record["token"]

    with patch("time.time", return_value=1100.0), pytest.raises(SprintTokenException, match="sprint_token has expired"):
        validate_sprint_token(token, user_id="user1")


def test_validate_sprint_token_no_worker_check():
    token_record = issue_sprint_token("user1", worker_count=4, sprint_price="10.00")
    token = token_record["token"]

    # Should pass if workers is None even if record has 4
    result = validate_sprint_token(token, user_id="user1", workers=None)
    assert result["token"] == token
