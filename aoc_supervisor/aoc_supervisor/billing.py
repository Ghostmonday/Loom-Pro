"""Credit billing guardrails for supervisor task dispatch.

The default billing gate reads and updates the local account ledger at
``.aoc/billing/accounts.json``. Ledger access is routed through a storage
provider interface so the same balance rules can be used by external account
repositories.
"""

from __future__ import annotations

import functools
import inspect
import json
import os
import tempfile
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .complexity import ComplexitySnapshot

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback.
    fcntl = None  # type: ignore[assignment]


LEDGER_PATH = Path(".aoc/billing/accounts.json")
LOCK_PATH = Path(".aoc/billing/accounts.lock")
DEFAULT_BASE_RATE = Decimal("0.01")
DEFAULT_DENSITY_RATE = Decimal("0.0001")
MONEY_QUANT = Decimal("0.01")
DEFAULT_TIER_DEPLOY_FEES = {
    "starter": Decimal("5.00"),
    "team": Decimal("15.00"),
    "professional": Decimal("50.00"),
    "enterprise": Decimal("150.00"),
}
DEFAULT_INTEGRITY_SCORE_RATE = Decimal("0.01")
DEFAULT_SPRINT_BASE_RATE = Decimal("1.00")
DEFAULT_SPRINT_RATE_PER_AGENT_SLOT = Decimal("2.00")
DEFAULT_SPRINT_RATE_PER_ASSIGNMENT = Decimal("1.50")
DEFAULT_SPRINT_TOKEN_TTL_SECONDS = 3600

F = TypeVar("F", bound=Callable[..., Any])
_LEDGER_THREAD_LOCK = threading.RLock()
_SPRINT_TOKEN_LOCK = threading.RLock()
_SPRINT_TOKENS: dict[str, dict[str, Any]] = {}


class BillingException(Exception):
    """Base exception for billing failures."""


class InsufficientCreditsException(BillingException):
    """Raised when an account is not allowed to dispatch compute tasks."""


class BillingLedgerException(BillingException):
    """Raised when the local billing ledger cannot be read or updated."""


class LedgerStorageProvider(ABC):
    """Repository interface for billing ledger persistence."""

    @abstractmethod
    def read_ledger(self) -> dict[str, Any]:
        """Return the complete account ledger as a JSON-like mapping."""

    @abstractmethod
    def write_ledger(self, ledger: dict[str, Any]) -> None:
        """Persist the complete account ledger."""

    @contextmanager
    def locked_ledger(self) -> Iterator[dict[str, Any]]:
        """Yield a ledger snapshot under the provider's consistency boundary."""
        yield self.read_ledger()


class LocalFileLedgerStorageProvider(LedgerStorageProvider):
    """Local JSON file provider for the default billing ledger."""

    def __init__(
        self,
        ledger_path: Path = LEDGER_PATH,
        lock_path: Path = LOCK_PATH,
    ) -> None:
        self.ledger_path = ledger_path
        self.lock_path = lock_path

    @contextmanager
    def locked_ledger(self) -> Iterator[dict[str, Any]]:
        with _LEDGER_THREAD_LOCK:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            with self.lock_path.open("a+", encoding="utf-8") as lock_file:
                if fcntl is not None:
                    deadline = time.monotonic() + _ledger_lock_timeout_seconds()
                    while True:
                        try:
                            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                            break
                        except BlockingIOError as exc:
                            if time.monotonic() >= deadline:
                                message = f"timed out waiting for billing ledger lock: {self.lock_path}"
                                raise BillingLedgerException(message) from exc
                            time.sleep(0.05)
                try:
                    yield self.read_ledger()
                finally:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def read_ledger(self) -> dict[str, Any]:
        try:
            with self.ledger_path.open("r", encoding="utf-8") as ledger_file:
                ledger = json.load(ledger_file)
        except FileNotFoundError as exc:
            raise BillingLedgerException(f"billing ledger not found: {self.ledger_path}") from exc
        except json.JSONDecodeError as exc:
            raise BillingLedgerException(f"billing ledger is invalid JSON: {self.ledger_path}") from exc

        if not isinstance(ledger, dict):
            raise BillingLedgerException("billing ledger root must be a JSON object")
        return ledger

    def write_ledger(self, ledger: dict[str, Any]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.ledger_path.name}.",
            suffix=".tmp",
            dir=str(self.ledger_path.parent),
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(ledger, tmp_file, indent=2, sort_keys=True)
                tmp_file.write("\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(tmp_name, self.ledger_path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)


DEFAULT_LEDGER_STORAGE = LocalFileLedgerStorageProvider()


def verify_account_balance(
    user_id: str,
    storage_provider: LedgerStorageProvider | None = None,
) -> bool:
    """Return whether the user has an active account with positive balance."""
    storage = _resolve_storage_provider(storage_provider)
    with storage.locked_ledger() as ledger:
        account = _get_account(ledger, user_id)
        return _account_is_billable(account)


def enforce_billing_gate(dispatch_parallel_task: F) -> F:
    """Block orchestrator dispatch unless the caller has usable credits.

    The wrapped callable must expose a ``user_id`` argument either by name or as
    an attribute on the first positional object argument.
    """

    @functools.wraps(dispatch_parallel_task)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user_id = _extract_user_id(dispatch_parallel_task, args, kwargs)
        if not verify_account_balance(user_id):
            raise InsufficientCreditsException(f"Account {user_id!r} has insufficient credits or is past due.")
        return dispatch_parallel_task(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


class SprintTokenException(BillingException):
    """Raised when a sprint token is missing, expired, or invalid."""


def _compute_blueprint_cost(snapshot: ComplexitySnapshot, ledger: dict[str, Any]) -> Decimal:
    """Compute the deploy fee charged when purchasing a sprint entitlement."""
    from .complexity import tier_for_score

    billing_config = ledger.get("_billing", {})
    if not isinstance(billing_config, dict):
        billing_config = {}

    tier = tier_for_score(snapshot.integrity_score)
    tier_fees = billing_config.get("tier_deploy_fees", {})
    if not isinstance(tier_fees, dict):
        tier_fees = {}

    base_fee = _coerce_money(tier_fees.get(tier, DEFAULT_TIER_DEPLOY_FEES.get(tier, Decimal("5.00"))))
    score_rate = _coerce_decimal(billing_config.get("integrity_score_rate", DEFAULT_INTEGRITY_SCORE_RATE))
    return _quantize_money(base_fee + (score_rate * Decimal(snapshot.integrity_score)))


def _compute_sprint_cost(snapshot: ComplexitySnapshot, ledger: dict[str, Any]) -> Decimal:
    """Compute the execution fee charged when spawning the agent grid."""
    billing_config = ledger.get("_billing", {})
    if not isinstance(billing_config, dict):
        billing_config = {}

    base_rate = _coerce_money(billing_config.get("sprint_base_rate", DEFAULT_SPRINT_BASE_RATE))
    per_agent_slot = _coerce_decimal(
        billing_config.get("sprint_rate_per_agent_slot", DEFAULT_SPRINT_RATE_PER_AGENT_SLOT)
    )
    per_assignment = _coerce_decimal(
        billing_config.get("sprint_rate_per_assignment", DEFAULT_SPRINT_RATE_PER_ASSIGNMENT)
    )
    cost = (
        base_rate
        + (per_agent_slot * Decimal(snapshot.worker_count))
        + (per_assignment * Decimal(snapshot.assignment_count))
    )
    return _quantize_money(cost)


def deduct_deployment_fee(
    user_id: str,
    amount: Decimal | float | str,
    storage_provider: LedgerStorageProvider | None = None,
) -> float:
    """Deduct a quantized deployment fee and return the amount charged."""
    cost = _quantize_money(_coerce_decimal(amount))
    if cost < Decimal("0.00"):
        raise ValueError("deployment fee must be non-negative")

    storage = _resolve_storage_provider(storage_provider)
    with storage.locked_ledger() as ledger:
        account = _get_account(ledger, user_id)
        if not _account_is_billable(account):
            raise InsufficientCreditsException(f"Account {user_id!r} has insufficient credits or is past due.")

        balance = _coerce_quantized_money(account.get("balance", "0"), "balance")
        if balance < cost:
            raise InsufficientCreditsException(f"Account {user_id!r} cannot cover deployment fee ${cost}.")

        new_balance = _quantize_money(balance - cost)
        _verify_quantized_accounting(balance, cost, new_balance)
        account["balance"] = float(new_balance)
        ledger[user_id] = account
        storage.write_ledger(ledger)
        return float(cost)


def credit_account(
    user_id: str,
    amount: Decimal | float | str,
    storage_provider: LedgerStorageProvider | None = None,
) -> float:
    """Credit an account (refund / rollback helper)."""
    credit = _quantize_money(_coerce_decimal(amount))
    if credit <= Decimal("0.00"):
        return 0.0

    storage = _resolve_storage_provider(storage_provider)
    with storage.locked_ledger() as ledger:
        account = _get_account(ledger, user_id)
        balance = _coerce_quantized_money(account.get("balance", "0"), "balance")
        new_balance = _quantize_money(balance + credit)
        account["balance"] = float(new_balance)
        account.setdefault("status", "active")
        ledger[user_id] = account
        storage.write_ledger(ledger)
        return float(credit)


def release_sprint_token(token: str) -> None:
    """Mark a consumed sprint token as unused (spawn rollback helper)."""
    with _SPRINT_TOKEN_LOCK:
        record = _SPRINT_TOKENS.get(token)
        if isinstance(record, dict):
            record["used"] = False


def issue_sprint_token(
    user_id: str,
    *,
    worker_count: int,
    sprint_price: Decimal | float | str,
    ttl_seconds: int = DEFAULT_SPRINT_TOKEN_TTL_SECONDS,
) -> dict[str, Any]:
    """Create a single-use sprint entitlement token after deploy fee payment."""
    if worker_count < 1:
        raise ValueError("worker_count must be positive")
    sprint_price_decimal = _coerce_decimal(sprint_price)
    if sprint_price_decimal < Decimal("0.00"):
        raise BillingLedgerException("sprint_price must be non-negative")

    token = str(uuid.uuid4())
    expires_at = time.time() + max(1, ttl_seconds)
    record = {
        "token": token,
        "user_id": user_id,
        "worker_count": worker_count,
        "sprint_price": float(_quantize_money(sprint_price_decimal)),
        "expires_at": expires_at,
        "sprint_paid": False,
        "used": False,
    }
    with _SPRINT_TOKEN_LOCK:
        _SPRINT_TOKENS[token] = record
    return record


def validate_sprint_token(
    token: str,
    *,
    user_id: str,
    workers: int | None = None,
    consume: bool = False,
) -> dict[str, Any]:
    """Validate a sprint token and optionally mark it as consumed."""
    if not token:
        raise SprintTokenException("sprint_token is required")

    with _SPRINT_TOKEN_LOCK:
        record = _SPRINT_TOKENS.get(token)
        if record is None:
            raise SprintTokenException("sprint_token is invalid")
        if record.get("used"):
            raise SprintTokenException("sprint_token has already been used")
        if record.get("user_id") != user_id:
            raise SprintTokenException("sprint_token does not match the requesting account")
        if time.time() > float(record.get("expires_at", 0)):
            raise SprintTokenException("sprint_token has expired")
        if workers is not None and int(record.get("worker_count", 0)) != workers:
            raise SprintTokenException("sprint_token worker_count does not match request")

        if consume:
            record["used"] = True

        return dict(record)


def clear_sprint_tokens() -> None:
    """Reset in-memory sprint tokens (primarily for tests)."""
    with _SPRINT_TOKEN_LOCK:
        _SPRINT_TOKENS.clear()


def deduct_compute_costs(
    user_id: str,
    graph_size: int,
    storage_provider: LedgerStorageProvider | None = None,
) -> float:
    """Deduct graph execution cost from the ledger and return the fee charged.

    Cost is data-driven through optional ledger metadata:

    ``_billing.rate_per_density_unit``
        Dollar rate multiplied by graph matrix density units.
    ``_billing.base_dispatch_rate``
        Flat dollar rate per dispatch.

    With only ``graph_size`` available, the matrix density proxy is ``n * n``:
    the number of addressable cells in the parsed graph matrix.
    """
    if graph_size < 0:
        raise ValueError("graph_size must be non-negative")

    storage = _resolve_storage_provider(storage_provider)
    with storage.locked_ledger() as ledger:
        account = _get_account(ledger, user_id)
        if not _account_is_billable(account):
            raise InsufficientCreditsException(f"Account {user_id!r} has insufficient credits or is past due.")

        cost = _compute_cost(ledger, graph_size)
        balance = _coerce_quantized_money(account.get("balance", "0"), "balance")
        if balance < cost:
            raise InsufficientCreditsException(f"Account {user_id!r} cannot cover compute cost ${cost}.")

        new_balance = _quantize_money(balance - cost)
        _verify_quantized_accounting(balance, cost, new_balance)
        account["balance"] = float(new_balance)
        storage.write_ledger(ledger)
        return float(cost)


@contextmanager
def _locked_ledger(
    storage_provider: LedgerStorageProvider | None = None,
) -> Iterator[dict[str, Any]]:
    storage = _resolve_storage_provider(storage_provider)
    with storage.locked_ledger() as ledger:
        yield ledger


def _read_ledger() -> dict[str, Any]:
    return DEFAULT_LEDGER_STORAGE.read_ledger()


def _write_ledger(ledger: dict[str, Any]) -> None:
    DEFAULT_LEDGER_STORAGE.write_ledger(ledger)


def _resolve_storage_provider(
    storage_provider: LedgerStorageProvider | None,
) -> LedgerStorageProvider:
    return storage_provider or DEFAULT_LEDGER_STORAGE


def _ledger_lock_timeout_seconds() -> float:
    raw = os.environ.get("GAIJINN_LEDGER_LOCK_TIMEOUT", "5").strip()
    try:
        return max(0.1, float(raw))
    except ValueError:
        return 5.0


def _get_account(ledger: dict[str, Any], user_id: str) -> dict[str, Any]:
    if not user_id:
        raise BillingLedgerException("user_id is required for billing verification")

    account = ledger.get(user_id)
    if not isinstance(account, dict):
        return {}
    return account


def _account_is_billable(account: dict[str, Any]) -> bool:
    if account.get("status") == "past_due":
        return False
    return _coerce_money(account.get("balance", "0")) > Decimal("0.00")


def _extract_user_id(
    dispatch_parallel_task: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    if "user_id" in kwargs:
        return str(kwargs["user_id"])

    try:
        bound = inspect.signature(dispatch_parallel_task).bind_partial(*args, **kwargs)
    except TypeError:
        bound = None
    if bound is not None and "user_id" in bound.arguments:
        return str(bound.arguments["user_id"])

    if args:
        maybe_user_id = getattr(args[0], "user_id", None)
        if maybe_user_id is not None:
            return str(maybe_user_id)

    raise BillingLedgerException(f"{dispatch_parallel_task.__name__} must receive a user_id for billing enforcement")


def _compute_cost(ledger: dict[str, Any], graph_size: int) -> Decimal:
    billing_config = ledger.get("_billing", {})
    if not isinstance(billing_config, dict):
        billing_config = {}

    base_rate = _coerce_money(billing_config.get("base_dispatch_rate", DEFAULT_BASE_RATE))
    density_rate = _coerce_decimal(billing_config.get("rate_per_density_unit", DEFAULT_DENSITY_RATE))
    if base_rate < Decimal("0.00"):
        raise BillingLedgerException("base_dispatch_rate must be non-negative")
    if density_rate < Decimal("0.00"):
        raise BillingLedgerException("rate_per_density_unit must be non-negative")
    matrix_density_units = Decimal(graph_size) * Decimal(graph_size)
    return _quantize_money(base_rate + (matrix_density_units * density_rate))


def _verify_quantized_accounting(
    starting_balance: Decimal,
    cost: Decimal,
    new_balance: Decimal,
) -> None:
    if starting_balance != _quantize_money(starting_balance):
        raise BillingLedgerException(f"starting balance must be quantized to {MONEY_QUANT}")
    if cost < Decimal("0.00"):
        raise BillingLedgerException("compute cost must be non-negative")
    if cost != _quantize_money(cost):
        raise BillingLedgerException(f"compute cost must be quantized to {MONEY_QUANT}")
    if new_balance != _quantize_money(new_balance):
        raise BillingLedgerException(f"new balance must be quantized to {MONEY_QUANT}")
    if new_balance != _quantize_money(starting_balance - cost):
        raise BillingLedgerException("new balance does not match quantized deduction")
    if new_balance < Decimal("0.00"):
        raise BillingLedgerException("new balance cannot be negative")


def _coerce_money(value: Any) -> Decimal:
    return _quantize_money(_coerce_decimal(value))


def _coerce_quantized_money(value: Any, field_name: str) -> Decimal:
    decimal_value = _coerce_decimal(value)
    quantized_value = _quantize_money(decimal_value)
    if decimal_value != quantized_value:
        raise BillingLedgerException(f"{field_name} must be quantized to {MONEY_QUANT}")
    return quantized_value


def _coerce_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BillingLedgerException(f"invalid numeric value: {value!r}") from exc


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
