"""Handoff ticket protocol — cross-boundary mutations via council transaction bus."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from ..blueprint import Blueprint
from ..giv import HandoffTicket
from .merge import (
    changed_files,
    load_blueprint_optional,
    load_worker_giv,
    output_log_path,
    utc_now,
    write_merge_json,
)

HANDOFF_TICKET_START = "++++ GAIJINN_HANDOFF_TICKET_START ++++"
HANDOFF_TICKET_END = "++++ GAIJINN_HANDOFF_TICKET_END ++++"
HANDOFF_TICKET_PATTERN = re.compile(
    re.escape(HANDOFF_TICKET_START) + r"\s*(.*?)\s*" + re.escape(HANDOFF_TICKET_END),
    re.DOTALL,
)
HANDOFF_REQUEST_TYPE = "HANDOFF_TRANSACTION_REQUEST"
HANDOFF_RECEIPT_TYPE = "HANDOFF_TRANSACTION_RECEIPT"
HANDOFF_QUEUE_PATH = Path(".gaijinn/merge/handoff-queue.json")
HANDOFF_SCAFFOLD_TOKENS = (
    "<PATH_TO_FILE>",
    "<TARGET_WORK_UNIT_ID>",
    "<Describe required parameters, fields, or functions>",
)


def file_to_work_unit_map(blueprint: Blueprint | Mapping[str, Any] | None) -> dict[str, str]:
    owners: dict[str, str] = {}
    if blueprint is None:
        return owners
    units = blueprint.work_units if isinstance(blueprint, Blueprint) else blueprint.get("work_units", [])
    if not isinstance(units, Sequence):
        return owners
    for unit in units:
        if isinstance(unit, Mapping):
            unit_id = str(unit.get("id", ""))
            paths = unit.get("allowed_paths", [])
        else:
            unit_id = unit.id
            paths = unit.allowed_paths
        if not unit_id:
            continue
        for path in paths:
            owners[str(path)] = unit_id
    return owners


def work_unit_owner_map(manifest_details: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for worker_id, detail in manifest_details.items():
        for unit_id in detail.get("assigned_work_units", []):
            owners[str(unit_id)] = worker_id
    return owners


def build_sibling_handoff_map(
    sibling_paths: Sequence[str],
    blueprint: Blueprint | Mapping[str, Any] | None,
) -> dict[str, str]:
    path_to_unit = file_to_work_unit_map(blueprint)
    return {path: path_to_unit.get(path, "UNKNOWN") for path in sorted(set(sibling_paths))}


def _blueprint_work_unit_ids(blueprint: Blueprint | Mapping[str, Any] | None) -> set[str]:
    if blueprint is None:
        return set()
    units = blueprint.work_units if isinstance(blueprint, Blueprint) else blueprint.get("work_units", [])
    if not isinstance(units, Sequence):
        return set()
    ids: set[str] = set()
    for unit in units:
        unit_id = str(unit.get("id", "")).strip() if isinstance(unit, Mapping) else str(unit.id).strip()
        if unit_id:
            ids.add(unit_id)
    return ids


def _blueprint_allowed_target_paths(blueprint: Blueprint | Mapping[str, Any] | None) -> set[str]:
    if blueprint is None:
        return set()
    units = blueprint.work_units if isinstance(blueprint, Blueprint) else blueprint.get("work_units", [])
    if not isinstance(units, Sequence):
        return set()
    paths: set[str] = set()
    for unit in units:
        allowed = unit.get("allowed_paths", []) if isinstance(unit, Mapping) else unit.allowed_paths
        for path in allowed:
            normalized = str(path).strip()
            if normalized:
                paths.add(normalized)
    return paths


def _is_scaffold_handoff_payload(raw: Mapping[str, Any]) -> bool:
    """Drop tickets that echo prompt scaffold placeholders instead of concrete intent."""
    for key in ("target_file", "target_work_unit_id", "required_mutation_context"):
        value = str(raw.get(key, "")).strip()
        if not value:
            continue
        if any(token in value for token in HANDOFF_SCAFFOLD_TOKENS):
            return True
        if "<" in value and ">" in value:
            return True
    return False


def _ticket_target_allowed_by_blueprint(
    target_file: str,
    target_unit: str,
    blueprint: Blueprint | Mapping[str, Any] | None,
) -> bool:
    """Validate ticket target against blueprint allowed paths and known work units."""
    if blueprint is None:
        return True
    allowed_paths = _blueprint_allowed_target_paths(blueprint)
    if not allowed_paths:
        return True
    if not any(_path_matches_target(target_file, allowed) for allowed in allowed_paths):
        return False
    unit_ids = _blueprint_work_unit_ids(blueprint)
    if target_unit and target_unit != "UNKNOWN" and unit_ids:
        return target_unit in unit_ids
    return True


def parse_handoff_tickets_from_log(
    worker_id: str,
    log_text: str,
    blueprint: Blueprint | Mapping[str, Any] | None,
    *,
    parse_stats: dict[str, int] | None = None,
) -> list[HandoffTicket]:
    """Parse worker logs for handoff tickets; drop scaffold noise and invalid blueprint targets."""
    path_to_unit = file_to_work_unit_map(blueprint)
    tickets: list[HandoffTicket] = []
    for match in HANDOFF_TICKET_PATTERN.findall(log_text):
        try:
            raw = json.loads(match.strip())
        except json.JSONDecodeError:
            if parse_stats is not None:
                parse_stats["dropped_malformed"] = parse_stats.get("dropped_malformed", 0) + 1
            continue
        if not isinstance(raw, Mapping):
            if parse_stats is not None:
                parse_stats["dropped_malformed"] = parse_stats.get("dropped_malformed", 0) + 1
            continue
        if _is_scaffold_handoff_payload(raw):
            if parse_stats is not None:
                parse_stats["dropped_scaffold"] = parse_stats.get("dropped_scaffold", 0) + 1
            continue
        target_file = str(raw.get("target_file", "")).strip()
        if not target_file:
            if parse_stats is not None:
                parse_stats["dropped_empty_target"] = parse_stats.get("dropped_empty_target", 0) + 1
            continue
        target_unit = str(raw.get("target_work_unit_id") or path_to_unit.get(target_file, "UNKNOWN")).strip()
        if not _ticket_target_allowed_by_blueprint(target_file, target_unit, blueprint):
            if parse_stats is not None:
                parse_stats["dropped_invalid_target"] = parse_stats.get("dropped_invalid_target", 0) + 1
            continue
        tickets.append(
            HandoffTicket(
                ticket_id=_ticket_id(
                    worker_id,
                    target_file,
                    str(raw.get("required_mutation_context", "")).strip(),
                ),
                source_worker_id=worker_id,
                target_work_unit_id=target_unit,
                target_file=target_file,
                required_mutation_context=str(raw.get("required_mutation_context", "")).strip(),
            )
        )
    return tickets


def _path_matches_target(changed_path: str, target_file: str) -> bool:
    normalized = PurePosixPath(changed_path.replace("\\", "/")).as_posix()
    rule = PurePosixPath(target_file.replace("\\", "/")).as_posix().rstrip("/")
    return normalized == rule or normalized.startswith(f"{rule}/")


def ticket_is_resolved(
    ticket: HandoffTicket,
    *,
    target_worker_id: str | None,
    target_worker_dir: Path | None,
    base_ref: str,
    council_receipts: set[str],
    baseline_dir: Path | None = None,
) -> bool:
    if ticket.ticket_id in council_receipts:
        return True
    if target_worker_dir is None or not target_worker_dir.is_dir():
        return False
    scope_paths = None
    if baseline_dir is not None:
        try:
            scope_paths = load_worker_giv(target_worker_dir).allowed_paths
        except (OSError, ValueError, TypeError):
            scope_paths = None
    changed = changed_files(
        target_worker_dir,
        base_ref,
        baseline_dir=baseline_dir,
        scope_paths=scope_paths,
    )
    return any(_path_matches_target(path, ticket.target_file) for path in changed)


def evaluate_handoff_transaction_integrity(
    *,
    project_root: Path,
    workers_path: Path,
    manifest_details: Mapping[str, Mapping[str, Any]],
    base_ref: str,
    council_messages: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    blueprint = load_blueprint_optional(project_root)
    unit_owners = work_unit_owner_map(manifest_details)
    receipts = _handoff_receipt_ticket_ids(council_messages or ())
    raised: list[HandoffTicket] = []

    for worker_id in sorted(manifest_details):
        worker_dir = workers_path / worker_id
        log_path = output_log_path(worker_dir)
        if not log_path.exists():
            continue
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        raised.extend(parse_handoff_tickets_from_log(worker_id, log_text, blueprint))

    resolved_ids: set[str] = set()
    pending: list[dict[str, Any]] = []
    for ticket in raised:
        target_worker = unit_owners.get(ticket.target_work_unit_id)
        target_dir = workers_path / target_worker if target_worker else None
        if ticket_is_resolved(
            ticket,
            target_worker_id=target_worker,
            target_worker_dir=target_dir,
            base_ref=base_ref,
            council_receipts=receipts,
            baseline_dir=project_root,
        ):
            resolved_ids.add(ticket.ticket_id)
        else:
            pending.append(ticket.to_dict())

    return {
        "handoff_tickets_raised": len(raised),
        "handoff_tickets_resolved": len(resolved_ids),
        "transaction_bus_synchronized": len(raised) == len(resolved_ids),
        "pending_tickets": pending,
        "evaluated_at": utc_now(),
    }


def handoff_gate_for_worker(
    worker_id: str,
    log_text: str,
    trespasses: Sequence[str],
    sibling_paths: set[str],
    blueprint: Blueprint | Mapping[str, Any] | None,
) -> dict[str, Any]:
    tickets = parse_handoff_tickets_from_log(worker_id, log_text, blueprint)
    sibling_trespasses = [path for path in trespasses if _matched_sibling_path(path, sibling_paths)]

    if sibling_trespasses:
        return {
            "passed": False,
            "violations": [
                f"{path} (sibling write forbidden — emit HANDOFF ticket instead)" for path in sibling_trespasses
            ],
            "tickets": [ticket.to_dict() for ticket in tickets],
        }

    return {
        "passed": True,
        "tickets": [ticket.to_dict() for ticket in tickets],
        "ticket_count": len(tickets),
    }


def _matched_sibling_path(path: str, sibling_paths: set[str]) -> str | None:
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    for sibling in sorted(sibling_paths):
        rule = PurePosixPath(sibling.replace("\\", "/")).as_posix().rstrip("/")
        if normalized == rule or normalized.startswith(f"{rule}/"):
            return sibling
    return None


def _handoff_receipt_ticket_ids(messages: Sequence[Mapping[str, Any]]) -> set[str]:
    receipts: set[str] = set()
    for message in messages:
        if str(message.get("type", message.get("message_type", ""))) != HANDOFF_RECEIPT_TYPE:
            continue
        payload = message.get("payload", {})
        if isinstance(payload, Mapping):
            ticket_id = str(payload.get("ticket_id", "")).strip()
            if ticket_id:
                receipts.add(ticket_id)
    return receipts


def _ticket_id(worker_id: str, target_file: str, mutation_context: str) -> str:
    digest = hashlib.sha256(f"{worker_id}:{target_file}:{mutation_context}".encode()).hexdigest()[:6].upper()
    return f"TX-HT-{digest}"


def pending_tickets_for_worker(
    worker_id: str,
    assigned_work_units: Sequence[str],
    pending_tickets: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return queue tickets targeting this worker's assigned work units."""
    assigned = {str(unit_id) for unit_id in assigned_work_units}
    selected: list[dict[str, Any]] = []
    for ticket in pending_tickets:
        if not isinstance(ticket, Mapping):
            continue
        target_unit = str(ticket.get("target_work_unit_id", ""))
        if target_unit in assigned:
            selected.append(dict(ticket))
    return selected


def format_pending_handoffs_ingest_block(tickets: Sequence[Mapping[str, Any]]) -> str:
    """Prompt block for target workers ingesting council/queue handoff tickets."""
    if not tickets:
        return ""
    lines = [
        "=" * 80,
        "GAIJINN HANDOFF INGEST — PENDING TRANSACTIONS FOR THIS WORKER",
        "=" * 80,
        "Apply each required mutation inside your ALLOWED PATHS. Do not trespass siblings.",
        "",
    ]
    for ticket in tickets:
        lines.extend(
            [
                f"Ticket `{ticket.get('ticket_id', '')}` from `{ticket.get('source_worker_id', '')}`",
                f"Target file: `{ticket.get('target_file', '')}`",
                "Required mutation:",
                str(ticket.get("required_mutation_context", "")).strip(),
                "",
            ]
        )
    lines.append("Emit no duplicate tickets for the same mutation if already applied.")
    lines.append("=" * 80)
    return "\n".join(lines)


def sync_handoff_queue_at_collect(
    *,
    project_root: Path,
    workers_path: Path,
    manifest_details: Mapping[str, Mapping[str, Any]],
    base_ref: str,
    council_messages: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Ingest worker logs, emit receipts for resolved tickets, persist handoff queue."""
    from .council import append_handoff_receipt, load_messages

    messages = list(council_messages or ())
    if not messages:
        messages = [message.to_dict() for message in load_messages(project_root)]

    integrity = evaluate_handoff_transaction_integrity(
        project_root=project_root,
        workers_path=workers_path,
        manifest_details=manifest_details,
        base_ref=base_ref,
        council_messages=messages,
    )
    existing_receipts = _handoff_receipt_ticket_ids(messages)
    blueprint = load_blueprint_optional(project_root)
    unit_owners = work_unit_owner_map(manifest_details)
    receipts_emitted = 0
    parse_stats: dict[str, int] = {}

    for worker_id in sorted(manifest_details):
        worker_dir = workers_path / worker_id
        log_path = output_log_path(worker_dir)
        if not log_path.exists():
            continue
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        for ticket in parse_handoff_tickets_from_log(worker_id, log_text, blueprint, parse_stats=parse_stats):
            if ticket.ticket_id in existing_receipts:
                continue
            target_worker = unit_owners.get(ticket.target_work_unit_id)
            target_dir = workers_path / target_worker if target_worker else None
            if not ticket_is_resolved(
                ticket,
                target_worker_id=target_worker,
                target_worker_dir=target_dir,
                base_ref=base_ref,
                council_receipts=existing_receipts,
                baseline_dir=project_root,
            ):
                continue
            append_handoff_receipt(
                ticket,
                project_root=project_root,
                resolved_by_worker_id=target_worker,
            )
            existing_receipts.add(ticket.ticket_id)
            receipts_emitted += 1

    if receipts_emitted:
        messages = [message.to_dict() for message in load_messages(project_root)]
        integrity = evaluate_handoff_transaction_integrity(
            project_root=project_root,
            workers_path=workers_path,
            manifest_details=manifest_details,
            base_ref=base_ref,
            council_messages=messages,
        )

    payload = {
        "schema_version": 1,
        "synced_at": utc_now(),
        "receipts_emitted": receipts_emitted,
        "handoff_tickets_raised": integrity.get("handoff_tickets_raised", 0),
        "handoff_tickets_resolved": integrity.get("handoff_tickets_resolved", 0),
        "transaction_bus_synchronized": integrity.get("transaction_bus_synchronized", True),
        "pending_tickets": integrity.get("pending_tickets", []),
        "parse_stats": dict(sorted(parse_stats.items())),
        "dropped_scaffold_tickets": parse_stats.get("dropped_scaffold", 0),
    }
    write_merge_json(project_root / HANDOFF_QUEUE_PATH, payload)
    return payload


def load_handoff_queue(project_root: Path) -> dict[str, Any]:
    path = (project_root / HANDOFF_QUEUE_PATH).resolve()
    if not path.exists():
        return {"pending_tickets": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pending_tickets": []}
    return payload if isinstance(payload, dict) else {"pending_tickets": []}


def format_handoff_protocol_block(
    worker_name: str,
    allowed_paths: Sequence[str],
    sibling_handoff_map: Mapping[str, str],
) -> str:
    sibling_lines = [
        f" - `{path}`: Managed by {unit_id} -> HANDOFF_ONLY" for path, unit_id in sorted(sibling_handoff_map.items())
    ]
    return "\n".join(
        [
            "=" * 80,
            "GAIJINN CORE RUNTIME RULES: ENFORCED PROTOCOL",
            "=" * 80,
            f"WORKER_ID: {worker_name}",
            "GAIJINN_TOKENS: [SCOPE_STRICT=TRUE, NO_SIBLING_TRESPASS=TRUE, HANDOFF_ONLY=TRUE]",
            "",
            "CRITICAL BOUNDARY RULE:",
            "You have write permissions ONLY for paths listed under ALLOWED PATHS.",
            "You have READ-ONLY visibility into files listed under SIBLING HANDOFF PATHS.",
            "You are strictly FORBIDDEN from writing to, creating, or editing these paths directly.",
            "",
            f"ALLOWED PATHS: {', '.join(allowed_paths) if allowed_paths else 'none'}",
            "SIBLING HANDOFF PATHS:",
            *(sibling_lines if sibling_lines else [" - none"]),
            "",
            "THE HANDOFF PROTOCOL:",
            "If completing your task requires a mutation inside a SIBLING HANDOFF PATH,",
            "do not edit the file. Emit a structured transaction ticket at the end of your output:",
            "",
            HANDOFF_TICKET_START,
            json.dumps(
                {
                    "target_work_unit_id": "<TARGET_WORK_UNIT_ID>",
                    "target_file": "<PATH_TO_FILE>",
                    "required_mutation_context": "<Describe required parameters, fields, or functions>",
                },
                indent=2,
            ),
            HANDOFF_TICKET_END,
            "",
            "Failure to use this ticket structure for cross-boundary changes fails validation.",
            "=" * 80,
        ]
    )
