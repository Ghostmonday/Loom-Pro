"""plan command implementation."""

from __future__ import annotations

import typer

from ..blueprint import Blueprint, BlueprintValidationError, generate_blueprint, stable_work_unit_id
from ..helpers import (
    BLUEPRINT_JSON_PATH,
    BLUEPRINT_TEMPLATE_PATH,
    GIV_PATH,
    _ensure_gaijinn_dir,
    _load_giv,
    _load_graph,
    _load_metrics,
    _render_plan_summary,
    _require_project_state,
    _risk_rank,
)
from ..helpers.merge import completion_ledger_entries_by_wu, ledger_entry_matches_current_root
from ..helpers.project_profile import project_kind


def _filter_completed_work_units(project_root, blueprint: Blueprint) -> Blueprint:
    ledger = completion_ledger_entries_by_wu(project_root)
    if not ledger:
        return blueprint
    remaining = []
    for unit in blueprint.work_units:
        entry = ledger.get(unit.id) or ledger.get(stable_work_unit_id(unit.allowed_paths, unit.acceptance_checks))
        if entry and ledger_entry_matches_current_root(project_root, entry, unit.allowed_paths):
            continue
        remaining.append(unit)
    if len(remaining) == len(blueprint.work_units):
        return blueprint
    remaining_ids = {unit.id for unit in remaining}
    units = tuple(
        type(unit)(
            id=unit.id,
            title=unit.title,
            description=unit.description,
            allowed_paths=unit.allowed_paths,
            denied_paths=unit.denied_paths,
            depends_on=tuple(dep for dep in unit.depends_on if dep in remaining_ids),
            acceptance_checks=unit.acceptance_checks,
            estimated_risk=unit.estimated_risk,
            domain=unit.domain,
        )
        for unit in remaining
    )
    return Blueprint(
        schema_version=blueprint.schema_version,
        project_goal=blueprint.project_goal,
        assumptions=(*blueprint.assumptions, "Completed work units were filtered by completion-ledger.json."),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=blueprint.risks,
    )


def plan_cmd(workers: int, max_risk: str, json_output: bool) -> None:
    """Generate .gaijinn/blueprint.json and .gaijinn/blueprint.md."""
    if workers < 1:
        raise typer.BadParameter("--workers must be at least 1")
    max_risk = max_risk.strip().lower()
    if max_risk not in {"low", "medium", "high"}:
        raise typer.BadParameter("--max-risk must be one of: low, medium, high")

    state = _require_project_state()
    kind = project_kind(state.project_root)
    graph = _load_graph(state.graph_path)
    metrics = _load_metrics(state.metrics_path)
    giv = _load_giv(GIV_PATH)
    try:
        blueprint = generate_blueprint(graph, metrics, giv)
    except BlueprintValidationError as exc:
        raise typer.BadParameter(f"cannot generate blueprint: {exc}") from exc
    blueprint = Blueprint(
        schema_version=blueprint.schema_version,
        project_goal=blueprint.project_goal,
        assumptions=(*blueprint.assumptions, f"Plan route: project_kind={kind}."),
        work_units=blueprint.work_units,
        dependencies=blueprint.dependencies,
        risks=blueprint.risks,
    )
    blueprint = _filter_completed_work_units(state.project_root, blueprint)

    over_limit = [unit for unit in blueprint.work_units if _risk_rank(unit.estimated_risk) > _risk_rank(max_risk)]
    if over_limit:
        summary = ", ".join(f"{unit.id}:{unit.estimated_risk}" for unit in over_limit)
        raise typer.BadParameter(f"plan exceeds --max-risk {max_risk}: {summary}")

    _ensure_gaijinn_dir()
    BLUEPRINT_JSON_PATH.write_text(blueprint.to_json(), encoding="utf-8")
    BLUEPRINT_TEMPLATE_PATH.write_text(blueprint.to_markdown(), encoding="utf-8")

    if json_output:
        typer.echo(blueprint.to_json().rstrip())
    else:
        _render_plan_summary(blueprint, workers)
