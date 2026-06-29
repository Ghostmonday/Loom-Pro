from __future__ import annotations

import json
from pathlib import Path

from aoc_cli.commands.grid_spawn import _build_task_prompt
from aoc_cli.giv import HandoffTicket
from aoc_cli.helpers.council import append_handoff_receipt, append_handoff_transaction, load_messages
from aoc_cli.helpers.handoff import (
    HANDOFF_QUEUE_PATH,
    HANDOFF_TICKET_END,
    HANDOFF_TICKET_START,
    evaluate_handoff_transaction_integrity,
    format_pending_handoffs_ingest_block,
    handoff_gate_for_worker,
    parse_handoff_tickets_from_log,
    pending_tickets_for_worker,
    sync_handoff_queue_at_collect,
)


def test_parse_handoff_tickets_rejects_off_blueprint_target() -> None:
    blueprint = {
        "work_units": [
            {"id": "WU-001", "allowed_paths": ["tests/test_api.py"]},
            {"id": "WU-002", "allowed_paths": ["tiny_service/service.py"]},
        ]
    }
    log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-999",
  "target_file": "other/module.py",
  "required_mutation_context": "mutate something"
}}
{HANDOFF_TICKET_END}
"""
    stats: dict[str, int] = {}
    tickets = parse_handoff_tickets_from_log("worker-001", log, blueprint, parse_stats=stats)
    assert tickets == []
    assert stats.get("dropped_invalid_target") == 1


def test_parse_handoff_tickets_ignores_prompt_template_placeholders() -> None:
    log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "<TARGET_WORK_UNIT_ID>",
  "target_file": "<PATH_TO_FILE>",
  "required_mutation_context": "<Describe required parameters, fields, or functions>"
}}
{HANDOFF_TICKET_END}
"""
    stats: dict[str, int] = {}
    tickets = parse_handoff_tickets_from_log("worker-001", log, None, parse_stats=stats)
    assert tickets == []
    assert stats.get("dropped_scaffold") == 1


def test_parse_handoff_tickets_from_log() -> None:
    blueprint = {
        "work_units": [
            {"id": "WU-001", "allowed_paths": ["tests/test_api.py"]},
            {"id": "WU-002", "allowed_paths": ["tiny_service/service.py"]},
        ]
    }
    log = f"""
done
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-002",
  "target_file": "tiny_service/service.py",
  "required_mutation_context": "Expose DONE_STATUS constant"
}}
{HANDOFF_TICKET_END}
"""
    tickets = parse_handoff_tickets_from_log("worker-001", log, blueprint)
    assert len(tickets) == 1
    assert tickets[0].source_worker_id == "worker-001"
    assert tickets[0].target_work_unit_id == "WU-002"
    assert tickets[0].target_file == "tiny_service/service.py"


def test_handoff_gate_fails_on_sibling_trespass() -> None:
    gate = handoff_gate_for_worker(
        "worker-001",
        "",
        ["tiny_service/service.py"],
        {"tiny_service/service.py"},
        None,
    )
    assert gate["passed"] is False
    assert gate["violations"]


def test_handoff_gate_passes_with_ticket_and_no_trespass() -> None:
    log = f"""
{HANDOFF_TICKET_START}
{{"target_file": "tiny_service/service.py", "required_mutation_context": "add constant"}}
{HANDOFF_TICKET_END}
"""
    gate = handoff_gate_for_worker("worker-001", log, [], {"tiny_service/service.py"}, None)
    assert gate["passed"] is True
    assert gate["ticket_count"] == 1


def test_build_task_prompt_includes_handoff_protocol() -> None:
    prompt = _build_task_prompt(
        "worker-001",
        "# Task\nDo work.",
        {
            "allowed_paths": ["tests/test_api.py"],
            "denied_paths": ["tiny_service/service.py"],
            "sibling_denied_paths": ["tiny_service/service.py"],
            "structural_tokens": {
                "scope_strict": True,
                "no_sibling_trespass": True,
                "handoff_only": True,
            },
        },
        {"assigned_work_units": ["WU-001"]},
        blueprint={
            "work_units": [
                {"id": "WU-001", "allowed_paths": ["tests/test_api.py"]},
                {"id": "WU-002", "allowed_paths": ["tiny_service/service.py"]},
            ]
        },
    )
    assert "HANDOFF_ONLY=TRUE" in prompt
    assert HANDOFF_TICKET_START in prompt
    assert "tiny_service/service.py" in prompt
    assert "Managed by WU-002" in prompt


def test_evaluate_handoff_transaction_integrity_resolved_by_council_receipt(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    workers = project / ".gaijinn" / "workers"
    (workers / "worker-001").mkdir(parents=True)
    (project / ".gaijinn" / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "g",
                "assumptions": [],
                "work_units": [
                    {
                        "id": "WU-002",
                        "title": "service",
                        "description": "s",
                        "allowed_paths": ["tiny_service/service.py"],
                        "denied_paths": [],
                        "depends_on": [],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "low",
                    },
                ],
                "dependencies": {},
                "risks": [],
            }
        ),
        encoding="utf-8",
    )

    ticket_log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-002",
  "target_file": "tiny_service/service.py",
  "required_mutation_context": "add DONE_STATUS"
}}
{HANDOFF_TICKET_END}
"""
    (workers / "worker-001" / "output.log").write_text(ticket_log, encoding="utf-8")
    tickets = parse_handoff_tickets_from_log(
        "worker-001", ticket_log, json.loads((project / ".gaijinn" / "blueprint.json").read_text())
    )
    ticket_id = tickets[0].ticket_id

    details = {
        "worker-001": {"assigned_work_units": ["WU-001"]},
        "worker-002": {"assigned_work_units": ["WU-002"]},
    }
    integrity = evaluate_handoff_transaction_integrity(
        project_root=project,
        workers_path=workers,
        manifest_details=details,
        base_ref="HEAD",
        council_messages=[
            {
                "type": "HANDOFF_TRANSACTION_RECEIPT",
                "payload": {"ticket_id": ticket_id},
            }
        ],
    )
    assert integrity["handoff_tickets_raised"] == 1
    assert integrity["handoff_tickets_resolved"] == 1
    assert integrity["transaction_bus_synchronized"] is True


def test_pending_handoffs_ingest_block_targets_assigned_units() -> None:
    tickets = [
        {
            "ticket_id": "TX-HT-ABC123",
            "source_worker_id": "worker-001",
            "target_work_unit_id": "WU-002",
            "target_file": "tiny_service/service.py",
            "required_mutation_context": "add DONE_STATUS",
        }
    ]
    selected = pending_tickets_for_worker("worker-002", ["WU-002"], tickets)
    assert len(selected) == 1
    block = format_pending_handoffs_ingest_block(selected)
    assert "HANDOFF INGEST" in block
    assert "DONE_STATUS" in block


def test_build_task_prompt_includes_pending_handoff_ingest(tmp_path: Path) -> None:
    project = tmp_path / "repo"
    queue_dir = project / ".gaijinn" / "merge"
    queue_dir.mkdir(parents=True)
    (queue_dir / "handoff-queue.json").write_text(
        json.dumps(
            {
                "pending_tickets": [
                    {
                        "ticket_id": "TX-HT-ABC123",
                        "source_worker_id": "worker-001",
                        "target_work_unit_id": "WU-002",
                        "target_file": "tiny_service/service.py",
                        "required_mutation_context": "add DONE_STATUS",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    prompt = _build_task_prompt(
        "worker-002",
        "# Task\nApply handoff.",
        {
            "allowed_paths": ["tiny_service/service.py"],
            "denied_paths": ["tests/test_api.py"],
            "sibling_denied_paths": [],
            "structural_tokens": {"handoff_only": True},
        },
        {"assigned_work_units": ["WU-002"]},
        blueprint={
            "work_units": [
                {"id": "WU-002", "allowed_paths": ["tiny_service/service.py"]},
            ]
        },
        project_root=project,
    )
    assert "HANDOFF INGEST" in prompt
    assert "DONE_STATUS" in prompt


def test_sync_handoff_queue_emits_receipt_for_resolved_ticket(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "repo"
    workers = project / ".gaijinn" / "workers"
    (workers / "worker-001").mkdir(parents=True)
    (workers / "worker-002").mkdir(parents=True)
    (project / ".gaijinn" / "bridge").mkdir(parents=True)
    (project / ".gaijinn" / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "g",
                "assumptions": [],
                "work_units": [
                    {
                        "id": "WU-002",
                        "title": "service",
                        "description": "s",
                        "allowed_paths": ["tiny_service/service.py"],
                        "denied_paths": [],
                        "depends_on": [],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "low",
                    },
                ],
                "dependencies": {},
                "risks": [],
            }
        ),
        encoding="utf-8",
    )

    ticket_log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-002",
  "target_file": "tiny_service/service.py",
  "required_mutation_context": "add DONE_STATUS"
}}
{HANDOFF_TICKET_END}
"""
    (workers / "worker-001" / "output.log").write_text(ticket_log, encoding="utf-8")
    monkeypatch.chdir(project)
    monkeypatch.setattr("aoc_cli.helpers.handoff.ticket_is_resolved", lambda *args, **kwargs: True)

    details = {
        "worker-001": {"assigned_work_units": ["WU-001"]},
        "worker-002": {"assigned_work_units": ["WU-002"]},
    }
    queue = sync_handoff_queue_at_collect(
        project_root=project,
        workers_path=workers,
        manifest_details=details,
        base_ref="HEAD",
    )
    assert (project / HANDOFF_QUEUE_PATH).exists()
    assert queue["handoff_tickets_raised"] == 1
    assert queue["receipts_emitted"] == 1
    messages = load_messages(project)
    assert any(message.message_type == "HANDOFF_TRANSACTION_RECEIPT" for message in messages)


def test_append_handoff_receipt_writes_council_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gaijinn" / "bridge").mkdir(parents=True)
    ticket = HandoffTicket(
        ticket_id="TX-HT-ABC123",
        source_worker_id="worker-001",
        target_work_unit_id="WU-002",
        target_file="tiny_service/service.py",
        required_mutation_context="add DONE_STATUS",
    )
    msg = append_handoff_receipt(ticket, project_root=tmp_path, resolved_by_worker_id="worker-002")
    assert msg.message_type == "HANDOFF_TRANSACTION_RECEIPT"
    loaded = load_messages(tmp_path)
    assert loaded[-1].payload["ticket_id"] == "TX-HT-ABC123"


def test_append_handoff_transaction_writes_council_entry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gaijinn" / "bridge").mkdir(parents=True)
    ticket = HandoffTicket(
        ticket_id="TX-HT-ABC123",
        source_worker_id="worker-001",
        target_work_unit_id="WU-002",
        target_file="tiny_service/service.py",
        required_mutation_context="add DONE_STATUS",
    )
    msg = append_handoff_transaction(ticket, project_root=tmp_path)
    assert msg.message_type == "HANDOFF_TRANSACTION_REQUEST"
    assert msg.payload is not None
    loaded = load_messages(tmp_path)
    assert loaded[-1].payload["ticket_id"] == "TX-HT-ABC123"
