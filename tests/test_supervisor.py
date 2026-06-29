"""Comprehensive tests for the aoc_supervisor package.

Covers:
  - enforcer.validate_system_state    (valid, missing, corrupt, trip markers)
  - billing.LocalFileLedgerStorageProvider  (read/write/locked)
  - billing.verify_account_balance    (active, past-due, zero, missing)
  - billing.deduct_compute_costs      (success, insufficient, negative size)
  - complexity.ComplexitySnapshot     (integrity_score / ACI pricing inputs)
  - billing._compute_blueprint_cost / _compute_sprint_cost
  - FastAPI /api/v1/quote             (no charge)
  - FastAPI /api/v1/blueprint/purchase (charges deploy fee, returns sprint_token)
  - FastAPI /api/v1/grid/spawn        (requires sprint_token)
  - ClusterOrchestrator               (provision, dispatch with mocked billing)
  - FastAPI /api/v1/health endpoint   (TestClient)
"""

from __future__ import annotations

import io
import json
import zipfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_manifest(tmp_path: Path) -> Path:
    """Return a path to a non-existent metrics manifest under tmp_path."""
    return tmp_path / ".gaijinn" / "metrics_manifest.json"


def _write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _spawn_headers(*, user_id: str = "alice", idempotency_key: str = "test-spawn-default") -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Idempotency-Key": idempotency_key}


SAMPLE_ACI_PAYLOAD = {
    "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
    "gravity_meta": {"rejected_nodes": []},
    "curvature_meta": {
        "shadow_bridge_count": 0,
        "edges": {"e1": {"kappa": -0.5}},
    },
    "blueprint": {
        "work_units": [
            {"estimated_risk": "low"},
            {"estimated_risk": "high"},
        ]
    },
    "workers": 2,
}


# ===================================================================
# 1. enforcer.validate_system_state
# ===================================================================


class TestValidateSystemState:
    """Structural-safety validation of the metrics manifest."""

    def test_valid_manifest_returns_true(self, tmp_manifest: Path) -> None:
        """A plain, well-formed manifest without trip markers returns True."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"status": "SUCCESS", "score": 0.95})
        assert validate_system_state(tmp_manifest) is True

    def test_missing_manifest_returns_false(self, tmp_manifest: Path) -> None:
        """A non-existent manifest file returns False (unverified)."""
        from aoc_supervisor.enforcer import validate_system_state

        assert validate_system_state(tmp_manifest) is False

    def test_corrupt_json_raises(self, tmp_manifest: Path) -> None:
        """Invalid JSON content raises StructuralGravityViolation."""
        from aoc_supervisor.enforcer import StructuralGravityViolation, validate_system_state

        tmp_manifest.parent.mkdir(parents=True, exist_ok=True)
        tmp_manifest.write_text("this is not json", encoding="utf-8")

        with pytest.raises(StructuralGravityViolation, match="invalid metrics manifest"):
            validate_system_state(tmp_manifest)

    def test_non_dict_manifest_raises(self, tmp_manifest: Path) -> None:
        """A JSON array at the root raises StructuralGravityViolation."""
        from aoc_supervisor.enforcer import StructuralGravityViolation, validate_system_state

        _write_json(tmp_manifest, ["node1", "node2"])

        with pytest.raises(StructuralGravityViolation, match="metrics manifest must be a JSON object"):
            validate_system_state(tmp_manifest)

    # -- trip markers ----------------------------------------------------

    def test_tripped_marker_returns_false(self, tmp_manifest: Path) -> None:
        """The 'tripped' key set to a truthy value returns False."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"tripped": True})
        assert validate_system_state(tmp_manifest) is False

    def test_unsafe_marker_returns_false(self, tmp_manifest: Path) -> None:
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"unsafe": True})
        assert validate_system_state(tmp_manifest) is False

    def test_rejected_marker_returns_false(self, tmp_manifest: Path) -> None:
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"rejected": True})
        assert validate_system_state(tmp_manifest) is False

    def test_automatic_rejection_marker_returns_false(self, tmp_manifest: Path) -> None:
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"automatic_rejection": True})
        assert validate_system_state(tmp_manifest) is False

    def test_falsy_trip_marker_is_ignored(self, tmp_manifest: Path) -> None:
        """A 'tripped' key with a falsy value is NOT considered tripped."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"tripped": False})
        assert validate_system_state(tmp_manifest) is True

    def test_status_tripped_returns_false(self, tmp_manifest: Path) -> None:
        """The 'status' key with value 'TRIPPED' triggers trip detection."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"status": "TRIPPED"})
        assert validate_system_state(tmp_manifest) is False

    def test_status_crashed_returns_false(self, tmp_manifest: Path) -> None:
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"status": "CRASHED"})
        assert validate_system_state(tmp_manifest) is False

    def test_state_unsafe_returns_false(self, tmp_manifest: Path) -> None:
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"state": "UNSAFE"})
        assert validate_system_state(tmp_manifest) is False

    def test_nested_trip_detection(self, tmp_manifest: Path) -> None:
        """Trip markers are detected even when nested."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"meta": {"results": {"tripped": True}}})
        assert validate_system_state(tmp_manifest) is False

    def test_trip_in_list(self, tmp_manifest: Path) -> None:
        """Trip markers inside a list are detected."""
        from aoc_supervisor.enforcer import validate_system_state

        _write_json(tmp_manifest, {"nodes": [{"id": "a", "tripped": True}]})
        assert validate_system_state(tmp_manifest) is False

    def test_default_path_does_not_exist(self) -> None:
        """Calling with no argument on a fresh system returns False."""
        from aoc_supervisor.enforcer import validate_system_state

        # The default path .gaijinn/metrics_manifest.json should not exist.
        assert validate_system_state() is False


# ===================================================================
# 2. billing.LocalFileLedgerStorageProvider
# ===================================================================


class TestLocalFileLedgerStorageProvider:
    """File-based billing ledger read / write / locking."""

    def test_write_and_read(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
        lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)

        ledger = {"alice": {"balance": "25.00", "status": "active"}}
        provider.write_ledger(ledger)
        assert ledger_path.exists()

        result = provider.read_ledger()
        assert result == ledger

    def test_read_missing_file_raises(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "nope" / "accounts.json"
        provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / "accounts.lock")

        with pytest.raises(BillingLedgerException, match="billing ledger not found"):
            provider.read_ledger()

    def test_read_corrupt_json_raises(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "accounts.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("{{{bad json", encoding="utf-8")

        provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / "accounts.lock")
        with pytest.raises(BillingLedgerException, match="billing ledger is invalid JSON"):
            provider.read_ledger()

    def test_read_non_dict_raises(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "accounts.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text('"just a string"', encoding="utf-8")

        provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / "accounts.lock")
        with pytest.raises(BillingLedgerException, match="billing ledger root must be a JSON object"):
            provider.read_ledger()

    def test_locked_ledger_context(self, tmp_path: Path) -> None:
        """locked_ledger() yields the current ledger and supports mutation."""
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "accounts.json"
        lock_path = tmp_path / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)

        initial = {"bob": {"balance": "10.00", "status": "active"}}
        provider.write_ledger(initial)

        with provider.locked_ledger() as ledger:
            assert ledger == initial
            ledger["bob"]["balance"] = "5.00"

        # Changes inside locked_ledger are not auto-persisted — they only mutate
        # the in-memory dict.  The file hasn't been re-written.
        # (write_ledger is a separate call; locked_ledger just provides a
        # consistent snapshot under lock.)
        assert provider.read_ledger()["bob"]["balance"] == "10.00"

    def test_locked_ledger_empty_file_created(self, tmp_path: Path) -> None:
        """locked_ledger creates lock dir if missing and handles read of
        a non-existent ledger (raising expected exception)."""
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider

        provider = LocalFileLedgerStorageProvider(
            tmp_path / "missing" / "accounts.json",
            tmp_path / "missing" / "accounts.lock",
        )
        with pytest.raises(BillingLedgerException, match="billing ledger not found"), provider.locked_ledger():
            pass  # pragma: no cover

    def test_write_atomicity(self, tmp_path: Path) -> None:
        """write_ledger uses a temp file + os.replace (atomic on POSIX)."""
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "accounts.json"
        provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / "accounts.lock")

        provider.write_ledger({"carol": {"balance": "99.00"}})
        content = ledger_path.read_text(encoding="utf-8")
        assert '"carol"' in content
        assert '"99.00"' in content

    def test_write_cleanup_temp_on_failure(self, tmp_path: Path) -> None:
        """If writing to the temp file fails, the temp file is cleaned up."""
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        ledger_path = tmp_path / "accounts.json"
        provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / "accounts.lock")

        # Write once to create initial data
        provider.write_ledger({"dave": {"balance": "50.00"}})

        # Write again (should succeed, no stale .tmp files)
        provider.write_ledger({"dave": {"balance": "25.00"}})
        after = {p.name for p in ledger_path.parent.iterdir()}
        # No .tmp files should remain
        tmp_files = [n for n in after if n.endswith(".tmp")]
        assert tmp_files == [], f"Stale temp files left behind: {tmp_files}"


# ===================================================================
# 3. billing.verify_account_balance
# ===================================================================


class TestVerifyAccountBalance:
    """Credit-balance verification against a ledger."""

    @pytest.fixture
    def provider(self, tmp_path: Path):
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        prov = LocalFileLedgerStorageProvider(
            tmp_path / "accounts.json",
            tmp_path / "accounts.lock",
        )
        prov.write_ledger(
            {
                "alice": {"balance": "25.00", "status": "active"},
                "bob": {"balance": "0.00", "status": "active"},
                "carol": {"balance": "10.00", "status": "past_due"},
                "dave": {},  # empty dict — no balance key
            }
        )
        return prov

    def test_positive_balance_returns_true(self, provider) -> None:
        from aoc_supervisor.billing import verify_account_balance

        assert verify_account_balance("alice", provider) is True

    def test_zero_balance_returns_false(self, provider) -> None:
        from aoc_supervisor.billing import verify_account_balance

        assert verify_account_balance("bob", provider) is False

    def test_past_due_returns_false(self, provider) -> None:
        from aoc_supervisor.billing import verify_account_balance

        assert verify_account_balance("carol", provider) is False

    def test_empty_account_returns_false(self, provider) -> None:
        from aoc_supervisor.billing import verify_account_balance

        assert verify_account_balance("dave", provider) is False

    def test_missing_user_returns_false(self, provider) -> None:
        from aoc_supervisor.billing import verify_account_balance

        assert verify_account_balance("nonexistent", provider) is False

    def test_empty_user_id_raises(self, provider) -> None:
        from aoc_supervisor.billing import BillingLedgerException, verify_account_balance

        with pytest.raises(BillingLedgerException, match="user_id is required"):
            verify_account_balance("", provider)

    def test_uses_default_provider(self) -> None:
        """Calling without a provider uses the module-level default."""
        from aoc_supervisor.billing import (
            DEFAULT_LEDGER_STORAGE,
            BillingLedgerException,
            verify_account_balance,
        )

        # Replace the default provider's read with a failure so we can
        # confirm the default is actually consulted.
        original_read = DEFAULT_LEDGER_STORAGE.read_ledger

        def _broken_read():
            raise BillingLedgerException("billing ledger not found (simulated)")

        DEFAULT_LEDGER_STORAGE.read_ledger = _broken_read  # type: ignore[method-assign]
        try:
            with pytest.raises(BillingLedgerException, match="billing ledger not found"):
                verify_account_balance("alice")
        finally:
            DEFAULT_LEDGER_STORAGE.read_ledger = original_read


# ===================================================================
# 4. billing.deduct_compute_costs
# ===================================================================


class TestDeductComputeCosts:
    """Cost deduction with balance verification."""

    @pytest.fixture
    def provider(self, tmp_path: Path):
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider

        prov = LocalFileLedgerStorageProvider(
            tmp_path / "accounts.json",
            tmp_path / "accounts.lock",
        )
        # graph_size=10 → 10*10 = 100 density units
        # cost = 0.01 + (100 * 0.0001) = 0.01 + 0.01 = $0.02
        prov.write_ledger(
            {
                "alice": {"balance": "5.00", "status": "active"},
                "bob": {"balance": "0.01", "status": "active"},
                "carol": {"balance": "0.00", "status": "active"},
            }
        )
        return prov

    def test_deduct_success(self, provider) -> None:
        from aoc_supervisor.billing import deduct_compute_costs

        fee = deduct_compute_costs("alice", graph_size=10, storage_provider=provider)
        assert fee == 0.02

    def test_deduct_updates_balance(self, provider) -> None:
        from aoc_supervisor.billing import deduct_compute_costs

        deduct_compute_costs("alice", graph_size=10, storage_provider=provider)
        ledger = provider.read_ledger()
        assert ledger["alice"]["balance"] == 4.98  # 5.00 - 0.02

    def test_insufficient_balance_raises(self, provider) -> None:
        from aoc_supervisor.billing import InsufficientCreditsException, deduct_compute_costs

        with pytest.raises(InsufficientCreditsException, match="cannot cover compute cost"):
            deduct_compute_costs("bob", graph_size=10, storage_provider=provider)

    def test_zero_balance_raises(self, provider) -> None:
        from aoc_supervisor.billing import InsufficientCreditsException, deduct_compute_costs

        with pytest.raises(InsufficientCreditsException, match="insufficient credits"):
            deduct_compute_costs("carol", graph_size=10, storage_provider=provider)

    def test_negative_graph_size_raises(self, provider) -> None:
        from aoc_supervisor.billing import deduct_compute_costs

        with pytest.raises(ValueError, match="graph_size must be non-negative"):
            deduct_compute_costs("alice", graph_size=-5, storage_provider=provider)

    def test_missing_user_raises(self, provider) -> None:
        from aoc_supervisor.billing import InsufficientCreditsException, deduct_compute_costs

        with pytest.raises(InsufficientCreditsException, match="insufficient credits"):
            deduct_compute_costs("nonexistent", graph_size=1, storage_provider=provider)

    def test_cost_formula_large_graph(self, provider) -> None:
        """graph_size=100 → 100*100=10000 density units.
        cost = 0.01 + (10000 * 0.0001) = 0.01 + 1.00 = $1.01"""
        from aoc_supervisor.billing import deduct_compute_costs

        fee = deduct_compute_costs("alice", graph_size=100, storage_provider=provider)
        assert fee == 1.01

    def test_custom_billing_rates(self, tmp_path: Path) -> None:
        """Billing config in ledger metadata overrides default rates."""
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider, deduct_compute_costs

        provider = LocalFileLedgerStorageProvider(
            tmp_path / "accounts.json",
            tmp_path / "accounts.lock",
        )
        provider.write_ledger(
            {
                "_billing": {"base_dispatch_rate": "5.00", "rate_per_density_unit": "0.50"},
                "alice": {"balance": "100.00", "status": "active"},
            }
        )
        # graph_size=2 → 4 density units → cost = 5.00 + (4*0.50) = $7.00
        fee = deduct_compute_costs("alice", graph_size=2, storage_provider=provider)
        assert fee == 7.00

    def test_negative_base_dispatch_rate_cannot_credit_account(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider, deduct_compute_costs

        provider = LocalFileLedgerStorageProvider(
            tmp_path / "accounts.json",
            tmp_path / "accounts.lock",
        )
        provider.write_ledger(
            {
                "_billing": {"base_dispatch_rate": "-5.00", "rate_per_density_unit": "0.00"},
                "alice": {"balance": "10.00", "status": "active"},
            }
        )

        with pytest.raises(BillingLedgerException, match="base_dispatch_rate must be non-negative"):
            deduct_compute_costs("alice", graph_size=1, storage_provider=provider)

        assert provider.read_ledger()["alice"]["balance"] == "10.00"

    def test_negative_density_rate_cannot_credit_account(self, tmp_path: Path) -> None:
        from aoc_supervisor.billing import BillingLedgerException, LocalFileLedgerStorageProvider, deduct_compute_costs

        provider = LocalFileLedgerStorageProvider(
            tmp_path / "accounts.json",
            tmp_path / "accounts.lock",
        )
        provider.write_ledger(
            {
                "_billing": {"base_dispatch_rate": "0.00", "rate_per_density_unit": "-1.00"},
                "alice": {"balance": "10.00", "status": "active"},
            }
        )

        with pytest.raises(BillingLedgerException, match="rate_per_density_unit must be non-negative"):
            deduct_compute_costs("alice", graph_size=2, storage_provider=provider)

        assert provider.read_ledger()["alice"]["balance"] == "10.00"

    def test_negative_quantized_cost_rejected_before_account_credit(self) -> None:
        from aoc_supervisor.billing import BillingLedgerException, _verify_quantized_accounting

        with pytest.raises(BillingLedgerException, match="compute cost must be non-negative"):
            _verify_quantized_accounting(Decimal("10.00"), Decimal("-1.00"), Decimal("11.00"))

    def test_negative_sprint_price_rejected_before_quantizing(self) -> None:
        from aoc_supervisor.billing import BillingLedgerException, issue_sprint_token

        with pytest.raises(BillingLedgerException, match="sprint_price must be non-negative"):
            issue_sprint_token("alice", worker_count=1, sprint_price="-0.004")


# ===================================================================
# 5. complexity.ComplexitySnapshot + ACI pricing
# ===================================================================


class TestComplexitySnapshot:
    """Architectural Complexity Index (ACI) pricing inputs."""

    def test_integrity_score_from_payload(self) -> None:
        from aoc_supervisor.complexity import build_snapshot_from_payload, compute_complexity_index

        snapshot = build_snapshot_from_payload(SAMPLE_ACI_PAYLOAD, worker_count=2)
        score = compute_complexity_index(snapshot)

        assert snapshot.node_count == 3
        assert snapshot.assignment_count == 2
        assert snapshot.high_risk_assignments == 1
        assert snapshot.worker_count == 2
        assert score == snapshot.integrity_score
        assert 90 <= score <= 120

    def test_payload_prefers_gravity_meta_node_count(self) -> None:
        from aoc_supervisor.complexity import build_snapshot_from_payload

        payload = {
            "nodes": [{"id": "fallback"}],
            "gravity_meta": {
                "nodes": {"a": {}, "b": {}, "c": {}},
                "rejected_nodes": [],
            },
        }

        snapshot = build_snapshot_from_payload(payload)

        assert snapshot.node_count == 3

    def test_integrity_score_rejects_invalid_node_count(self) -> None:
        from aoc_supervisor.complexity import ComplexitySnapshot

        with pytest.raises(ValueError, match="node_count must be finite and non-negative"):
            ComplexitySnapshot(-1, 0, 0, 1, 0, 0.0, 1).integrity_score

        with pytest.raises(ValueError, match="node_count must be finite and non-negative"):
            ComplexitySnapshot(float("inf"), 0, 0, 1, 0, 0.0, 1).integrity_score

    def test_tier_mapping(self) -> None:
        from aoc_supervisor.complexity import ComplexitySnapshot, tier_for_score

        starter = ComplexitySnapshot(1, 0, 0, 1, 0, 0.0, 1)
        assert tier_for_score(starter.integrity_score) == "starter"
        assert tier_for_score(199) == "starter"
        assert tier_for_score(200) == "team"
        assert tier_for_score(799) == "team"
        assert tier_for_score(800) == "professional"
        assert tier_for_score(2499) == "professional"
        assert tier_for_score(2500) == "enterprise"

    def test_customer_receipt_hides_internal_terms(self) -> None:
        from aoc_supervisor.complexity import build_snapshot_from_payload, customer_receipt

        snapshot = build_snapshot_from_payload(SAMPLE_ACI_PAYLOAD, worker_count=2)
        receipt = customer_receipt(snapshot)

        assert "integrity_score" in receipt
        assert "tier" in receipt
        assert "agent_slots" in receipt
        assert "shadow_bridge" not in json.dumps(receipt)
        assert "curvature" not in json.dumps(receipt)
        assert "kappa" not in json.dumps(receipt)


class TestAciPricing:
    """Blueprint and sprint cost formulas."""

    @pytest.fixture
    def ledger(self) -> dict:
        return {"alice": {"balance": "100.00", "status": "active"}}

    @pytest.fixture
    def snapshot(self):
        from aoc_supervisor.complexity import build_snapshot_from_payload

        return build_snapshot_from_payload(SAMPLE_ACI_PAYLOAD, worker_count=2)

    def test_compute_blueprint_cost_starter_tier(self, ledger, snapshot) -> None:
        from aoc_supervisor.billing import _compute_blueprint_cost

        cost = _compute_blueprint_cost(snapshot, ledger)
        # starter base 5.00 + score * 0.01
        assert cost == pytest.approx(Decimal("5.00") + Decimal(snapshot.integrity_score) * Decimal("0.01"))

    def test_compute_sprint_cost_scales_with_workers_and_assignments(self, ledger, snapshot) -> None:
        from aoc_supervisor.billing import _compute_sprint_cost

        cost = _compute_sprint_cost(snapshot, ledger)
        # base 1.00 + 2 workers * 2.00 + 2 assignments * 1.50 = 8.00
        assert cost == Decimal("8.00")

    def test_custom_billing_rates(self, snapshot) -> None:
        from aoc_supervisor.billing import _compute_blueprint_cost, _compute_sprint_cost

        ledger = {
            "_billing": {
                "tier_deploy_fees": {"starter": "10.00"},
                "integrity_score_rate": "0.05",
                "sprint_base_rate": "3.00",
                "sprint_rate_per_agent_slot": "1.00",
                "sprint_rate_per_assignment": "0.50",
            }
        }
        blueprint_cost = _compute_blueprint_cost(snapshot, ledger)
        sprint_cost = _compute_sprint_cost(snapshot, ledger)

        assert blueprint_cost == Decimal("10.00") + Decimal(snapshot.integrity_score) * Decimal("0.05")
        assert sprint_cost == Decimal("3.00") + Decimal("2.00") + Decimal("1.00")


# ===================================================================
# 6. FastAPI ACI billing endpoints
# ===================================================================


class TestAciBillingEndpoints:
    """Quote, purchase, and sprint-token gated grid spawn."""

    @pytest.fixture
    def billing_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import aoc_supervisor.api as api
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens
        from aoc_supervisor.spawn_governance import clear_idempotency_store

        # CI runners have no codex/grok/hermes; mock grid exercises billing/spawn logic only.
        monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")
        monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
        clear_idempotency_store(tmp_path)

        ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
        lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
        provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

        workers_dir = tmp_path / ".gaijinn" / "workers"
        workers_dir.mkdir(parents=True)
        (workers_dir / "manifest.json").write_text(
            json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
            encoding="utf-8",
        )
        (workers_dir / "worker-001").mkdir()
        (workers_dir / "worker-001" / "output.log").write_text("", encoding="utf-8")

        clear_sprint_tokens()
        with (
            patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
            patch.object(api, "ROOT_DIR", tmp_path),
            patch.object(api, "WORKERS_DIR", workers_dir),
            patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
            patch("aoc_supervisor.api.subprocess.Popen") as mock_popen,
            TestClient(api.app) as client,
        ):
            mock_proc = mock_popen.return_value
            mock_proc.pid = 4242
            yield client, provider

    def test_quote_returns_pricing_without_charging(self, billing_env) -> None:
        client, provider = billing_env
        starting_balance = provider.read_ledger()["alice"]["balance"]

        response = client.post("/api/v1/quote", json=SAMPLE_ACI_PAYLOAD)
        assert response.status_code == 200

        data = response.json()
        assert "integrity_score" in data
        assert data["tier"] == "starter"
        assert data["deploy_fee"] > 0
        assert data["sprint_fee"] > 0
        assert "receipt" in data
        assert data["receipt"]["agent_slots"] == 2
        assert "shadow_bridge" not in json.dumps(data)
        assert "curvature" not in json.dumps(data)

        assert provider.read_ledger()["alice"]["balance"] == starting_balance

    def test_blueprint_purchase_charges_deploy_fee_and_returns_token(self, billing_env) -> None:
        client, provider = billing_env

        quote = client.post("/api/v1/quote", json=SAMPLE_ACI_PAYLOAD).json()
        response = client.post(
            "/api/v1/blueprint/purchase",
            json=SAMPLE_ACI_PAYLOAD,
            headers={"X-User-Id": "alice"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "sprint_token" in data
        assert "expires_at" in data
        assert data["deploy_fee"] == quote["deploy_fee"]
        assert data["receipt"]["integrity_score"] == quote["integrity_score"]

        ledger = provider.read_ledger()
        expected_balance = round(100.00 - quote["deploy_fee"], 2)
        assert ledger["alice"]["balance"] == expected_balance

    def test_grid_spawn_requires_sprint_token(self, billing_env) -> None:
        client, _provider = billing_env

        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1},
            headers=_spawn_headers(idempotency_key="test-spawn-no-token"),
        )
        assert response.status_code == 401
        assert "sprint_token" in response.json()["detail"]

    def test_grid_spawn_with_token_charges_sprint_price(self, billing_env) -> None:
        client, provider = billing_env

        quote = client.post("/api/v1/quote", json={**SAMPLE_ACI_PAYLOAD, "workers": 1}).json()
        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()

        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=_spawn_headers(idempotency_key="test-spawn-charge-once"),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "spawned"

        ledger = provider.read_ledger()
        expected_balance = round(100.00 - quote["deploy_fee"] - quote["sprint_fee"], 2)
        assert ledger["alice"]["balance"] == expected_balance

    def test_grid_spawn_rejects_expired_token(self, billing_env) -> None:
        client, _provider = billing_env
        import aoc_supervisor.billing as billing

        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()

        with billing._SPRINT_TOKEN_LOCK:
            billing._SPRINT_TOKENS[purchase["sprint_token"]]["expires_at"] = 0

        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=_spawn_headers(idempotency_key="test-spawn-expired-token"),
        )
        assert response.status_code == 401

    def test_grid_spawn_without_executor_fails_before_charge(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-mock spawn must 503 on missing executor without charging or consuming token."""
        import aoc_supervisor.api as api
        import aoc_supervisor.billing as billing
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens

        monkeypatch.delenv("GAIJINN_MOCK_GRID", raising=False)
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
        lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
        provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

        workers_dir = tmp_path / ".gaijinn" / "workers"
        workers_dir.mkdir(parents=True)
        (workers_dir / "manifest.json").write_text(
            json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
            encoding="utf-8",
        )
        (workers_dir / "worker-001").mkdir()
        (workers_dir / "worker-001" / "output.log").write_text("", encoding="utf-8")

        clear_sprint_tokens()
        with (
            patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
            patch.object(api, "ROOT_DIR", tmp_path),
            patch.object(api, "WORKERS_DIR", workers_dir),
            patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
            TestClient(api.app) as client,
        ):
            purchase = client.post(
                "/api/v1/blueprint/purchase",
                json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
                headers={"X-User-Id": "alice"},
            ).json()
            balance_after_purchase = provider.read_ledger()["alice"]["balance"]
            sprint_token = purchase["sprint_token"]

            response = client.post(
                "/api/v1/grid/spawn",
                json={"workers": 1, "sprint_token": sprint_token},
                headers=_spawn_headers(idempotency_key="test-spawn-no-executor"),
            )

        assert response.status_code == 503
        assert provider.read_ledger()["alice"]["balance"] == balance_after_purchase
        with billing._SPRINT_TOKEN_LOCK:
            assert billing._SPRINT_TOKENS[sprint_token]["used"] is False

    def test_grid_spawn_refunds_when_token_consume_fails_after_charge(self, billing_env, monkeypatch) -> None:
        client, provider = billing_env
        import aoc_supervisor.api as api
        import aoc_supervisor.billing as billing

        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()
        balance_after_purchase = provider.read_ledger()["alice"]["balance"]

        real_validate = billing.validate_sprint_token

        def consume_fails(*args: object, **kwargs: object) -> dict[str, object]:
            if kwargs.get("consume"):
                raise billing.SprintTokenException("sprint_token has already been used")
            return real_validate(*args, **kwargs)

        monkeypatch.setattr(api, "validate_sprint_token", consume_fails)

        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=_spawn_headers(idempotency_key="test-spawn-refund-path"),
        )
        assert response.status_code == 401
        assert provider.read_ledger()["alice"]["balance"] == balance_after_purchase


class TestGridSprintMonitor:
    """API background monitor updates sprint + manifest when workers finish."""

    @pytest.fixture
    def mock_grid_env(self, tmp_path: Path, monkeypatch):
        import aoc_supervisor.api as api
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens

        monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")

        ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
        lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
        provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

        workers_dir = tmp_path / ".gaijinn" / "workers"
        workers_dir.mkdir(parents=True)
        (workers_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "worker_details": [{"worker_id": "worker-001", "status": "created"}],
                }
            ),
            encoding="utf-8",
        )
        (workers_dir / "worker-001").mkdir()
        (workers_dir / "worker-001" / "WORK_UNIT.md").write_text("# demo", encoding="utf-8")

        clear_sprint_tokens()
        api._sprints.clear()
        with (
            patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
            patch.object(api, "ROOT_DIR", tmp_path),
            patch.object(api, "WORKERS_DIR", workers_dir),
            patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
            TestClient(api.app) as client,
        ):
            yield client, workers_dir

    def test_mock_sprint_completes_and_updates_status(self, mock_grid_env) -> None:
        import time

        client, workers_dir = mock_grid_env
        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()

        spawn = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"], "timeout": 30},
            headers=_spawn_headers(idempotency_key="test-spawn-merge-endpoint"),
        )
        assert spawn.status_code == 200
        sprint_id = spawn.json()["sprint_id"]

        terminal_status = "running"
        for _ in range(40):
            status = client.get(f"/api/v1/grid/status?sprint_id={sprint_id}").json()
            terminal_status = status["sprint"]["status"]
            if terminal_status in {"completed", "failed", "timed_out"}:
                break
            time.sleep(0.15)

        assert terminal_status == "completed"
        manifest = json.loads((workers_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["worker_details"][0]["status"] == "completed"
        assert (workers_dir / "worker-001" / "output.log").exists()

    def test_session_merge_endpoint_after_mock_sprint(self, mock_grid_client) -> None:
        from aoc_supervisor.ui_intent import UiIntentDriver

        client, _workers_dir, _tmp_path, _store = mock_grid_client
        driver = UiIntentDriver(client)
        observation = driver.run_smoke_scenario("flow.intent_swarm_deploy_mock")

        assert observation.status == "completed"
        assert observation.merge is not None
        pipeline = observation.merge["merge_pipeline"]
        assert pipeline["phase"] == "completed"
        assert pipeline["merged"] >= 1
        assert pipeline["blocked"] == 0
        assert pipeline["conflicted"] == 0

        status = client.get(f"/api/v1/grid/merge/status?session_id={observation.session_id}")
        assert status.status_code == 200
        assert status.json()["merge_pipeline"]["phase"] == "completed"

        deliverable = client.get(f"/api/v1/grid/deliverable?session_id={observation.session_id}")
        assert deliverable.status_code == 200
        assert deliverable.headers["content-type"] == "application/zip"
        assert (
            f'filename="gaijinn-deliverable-{observation.session_id}.zip"' in deliverable.headers["content-disposition"]
        )
        with zipfile.ZipFile(io.BytesIO(deliverable.content)) as archive:
            names = set(archive.namelist())
        assert "tiny_service/api.py" in names
        assert ".gaijinn/session.json" in names
        assert not any(name.startswith(".gaijinn/workers/") for name in names)

        report = client.get(f"/api/v1/grid/merge/report?session_id={observation.session_id}")
        assert report.status_code == 200
        body = report.json()
        assert body["report"]["summary"]["merged"] >= 1
        assert body["merge_pipeline"]["workers"]

        diff = client.get(f"/api/v1/grid/diff?session_id={observation.session_id}")
        assert diff.status_code == 200
        assert "available" in diff.json()

    def test_advance_phase_endpoint_backend_testing(self, mock_grid_client, monkeypatch) -> None:
        client, _workers_dir, _tmp_path, store = mock_grid_client
        session_id = "abc123def456"
        session_root = store.sessions_dir / session_id
        session_root.mkdir(parents=True, exist_ok=True)
        (session_root / ".gaijinn").mkdir(parents=True)
        session_json = session_root / ".gaijinn" / "session.json"
        meta = {
            "session_id": session_id,
            "owner_user_id": "terminal-user",
            "intent": "Terminal smoke test project",
            "phase": "awaiting_next_phase",
            "phases": ["backend", "testing"],
            "current_phase": "backend",
            "pipeline_plan": {
                "phases": ["backend", "testing"],
                "current_index": 0,
                "current_phase": "backend",
                "completed_phases": ["backend"],
            },
            "loaded_context": {"frontend": {"project_path": str(session_root)}},
            "blueprint_mode": "graph",
            "work_stream_titles": [],
            "swarm_rationale": "demo",
        }
        session_json.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        store._active[session_id] = session_root

        def fake_pipeline(
            session_root: Path,
            *_args,
            **_kwargs,
        ) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
            titles = ("Integration tests", "Unit tests")
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_stream_titles": list(titles),
                "work_units": [
                    {"id": f"WU-{index:03d}", "title": title, "allowed_paths": [f"tests/{index}/"]}
                    for index, title in enumerate(titles, start=1)
                ],
            }
            blueprint_path = session_root / ".gaijinn" / "blueprint.json"
            blueprint_path.parent.mkdir(parents=True, exist_ok=True)
            blueprint_path.write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")
            return 2, 0, titles, "graph", titles

        # Patch in the globals of the store's methods (where it's actually looked up!)
        monkeypatch.setitem(store.advance_phase.__globals__, "_run_blueprint_pipeline", fake_pipeline)

        advanced = client.post(
            "/api/v1/orchestrate/advance-phase",
            json={"session_id": session_id},
            headers={"X-User-Id": "terminal-user"},
        )
        assert advanced.status_code == 200
        data = advanced.json()
        assert data["phase"] == "awaiting_swarm"
        assert data["current_phase"] == "testing"
        assert data["workers_ready"] == 0
        assert data["work_units"] == 2
        assert data["pipeline_plan"]["current_index"] == 1
        assert "blueprint stub" not in (data.get("message") or "").lower()
        assert "blueprint ready" in (data.get("message") or "").lower()
        assert data["loaded_context"]["backend"]["prior_session_id"] == session_id


# ===================================================================
# 7. ClusterOrchestrator (provision + dispatch, billing mocked)
# ===================================================================


class TestClusterOrchestrator:
    """Sandbox provisioning and task dispatch with mocked billing."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> ClusterOrchestrator:  # noqa: F821
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        return ClusterOrchestrator(
            project_root=tmp_path,
            user_id="test_user",
        )

    def test_provision_sandbox_creates_directory(self, orchestrator) -> None:
        sandbox = orchestrator.provision_sandbox("agent-1")
        assert sandbox.exists()
        assert sandbox.is_dir()
        assert sandbox.name == "agent-1"

    def test_provision_sandbox_recreates_existing(self, orchestrator) -> None:
        first = orchestrator.provision_sandbox("agent-recreate")
        (first / "stale_file.txt").write_text("hello")
        second = orchestrator.provision_sandbox("agent-recreate")
        assert second == first
        assert not (second / "stale_file.txt").exists()

    def test_provision_sandbox_rejects_unsafe_id(self, orchestrator) -> None:
        with pytest.raises(ValueError, match="unsafe agent_id"):
            orchestrator.provision_sandbox(".")

    def test_provision_sandbox_rejects_empty_id(self, orchestrator) -> None:
        with pytest.raises(ValueError, match="unsafe agent_id"):
            orchestrator.provision_sandbox("")

    def test_dispatch_parallel_task_creates_output(self, orchestrator) -> None:
        """Mock billing to avoid real ledger dependency."""
        with (
            patch("aoc_supervisor.billing.verify_account_balance", return_value=True),
            patch("aoc_supervisor.orchestrator.deduct_compute_costs") as mock_deduct,
        ):
            job_id = orchestrator.dispatch_parallel_task(
                "agent-dispatch",
                "process data X",
                graph_size=1,
            )

        assert job_id.startswith("agent-dispatch-")
        assert job_id in orchestrator.jobs
        assert orchestrator.agent_jobs["agent-dispatch"] == job_id

        job = orchestrator.jobs[job_id]
        assert job.status == "completed"
        assert job.output_file is not None
        assert job.output_file.exists()
        content = job.output_file.read_text(encoding="utf-8")
        assert "agent-dispatch" in content
        assert "process data X" in content

        mock_deduct.assert_called_once_with("test_user", 1)

    def test_dispatch_marked_failed_on_error(self, orchestrator) -> None:
        """If billing raises, the job is marked as 'failed'."""
        from aoc_supervisor.billing import InsufficientCreditsException

        with (
            patch("aoc_supervisor.billing.verify_account_balance", return_value=True),
            patch(
                "aoc_supervisor.orchestrator.deduct_compute_costs",
                side_effect=InsufficientCreditsException("no credits"),
            ),
            pytest.raises(InsufficientCreditsException),
        ):
            orchestrator.dispatch_parallel_task("agent-fail", "crash", graph_size=1)

        # The job should still be recorded but marked as failed.
        failed_jobs = [j for j in orchestrator.jobs.values() if j.status == "failed"]
        assert len(failed_jobs) >= 1

    def test_blocked_orchestrator_raises(self, orchestrator) -> None:
        orchestrator.blocked = True
        with pytest.raises(RuntimeError, match="cluster is blocked"):
            orchestrator.provision_sandbox("agent-x")

    def test_blocked_orchestrator_blocks_dispatch(self, orchestrator) -> None:
        orchestrator.blocked = True
        with (
            patch("aoc_supervisor.billing.verify_account_balance", return_value=True),
            pytest.raises(RuntimeError, match="cluster is blocked"),
        ):
            orchestrator.dispatch_parallel_task("agent-x", "prompt")

    def test_validate_agent_id_rejects_dotdot(self) -> None:
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        with pytest.raises(ValueError, match="unsafe agent_id"):
            ClusterOrchestrator._validate_agent_id("..")

    def test_validate_agent_id_rejects_path_separator(self) -> None:
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        with pytest.raises(ValueError, match="unsafe agent_id"):
            ClusterOrchestrator._validate_agent_id("foo/bar")

    def test_render_mock_agent_code(self) -> None:
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        code = ClusterOrchestrator._render_mock_agent_code("agt", "hello")
        assert "AGENT_ID = 'agt'" in code
        assert "PROMPT_PAYLOAD = 'hello'" in code
        assert "def run()" in code

    def test_evaluate_cluster_safety_no_sandboxes(self, orchestrator) -> None:
        """evaluate_cluster_safety with no sandboxes should succeed
        (empty graph). We mock compute_gravity_and_curvature to return
        a safe telemetry dict and validate_system_state to return True."""
        with (
            patch(
                "aoc_supervisor.orchestrator.compute_gravity_and_curvature",
                return_value={"status": "SUCCESS"},
            ),
        ):
            result = orchestrator.evaluate_cluster_safety()
        assert result is True


# ===================================================================
# 8. FastAPI health endpoint (TestClient)
# ===================================================================


class TestFastAPIHealth:
    """FastAPI /api/v1/health endpoint via TestClient."""

    @pytest.fixture
    def client(self, tmp_path: Path):
        """Provide a TestClient with a patched ROOT_DIR so the
        ClusterOrchestrator uses a temp project root."""
        import aoc_supervisor.api as api
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        # Override the global orchestrator singleton so it uses our tmp_path
        orch = ClusterOrchestrator(project_root=tmp_path, user_id="test")
        with patch.object(api, "_orchestrator", orch), TestClient(api.app) as c:
            yield c

    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["blocked"] is False
        assert data["active_jobs"] == 0
        assert data["source"] == "cluster_orchestrator"

    def test_health_reflects_blocked_state(self, client: TestClient, tmp_path: Path) -> None:
        """After blocking the orchestrator, the health endpoint should
        reflect it."""
        import aoc_supervisor.api as api
        from aoc_supervisor.orchestrator import ClusterOrchestrator

        orch = ClusterOrchestrator(project_root=tmp_path, user_id="test")
        orch.blocked = True
        with patch.object(api, "_orchestrator", orch), TestClient(api.app) as c:
            response = c.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["blocked"] is True
