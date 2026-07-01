import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from aoc_supervisor.repo_paths import (
    BLUEPRINT_UI_PATH,
    COMMAND_ENGINE_HTML_PATH,
    COMMAND_ENGINE_INTENT_MAP_PATH,
    COMMAND_ENGINE_JS_PATH,
    EXPERIENCE_POLICY_PATH,
    INTENT_FORGE_CSS_PATH,
    INTENT_FORGE_HTML_PATH,
    INTENT_FORGE_JS_PATH,
    INTENT_MAP_PATH,
    LOOM_INTENT_FORGE_INTENT_MAP_PATH,
    LOOM_PIPELINE_INTENT_MAP_PATH,
    LOOM_SYSTEM_INTENT_MAP_PATH,
    ORCHESTRATION_EVENT_SCHEMA_PATH,
    ORCHESTRATION_SNAPSHOT_SCHEMA_PATH,
    ORCHESTRATION_VISUAL_GRAMMAR_PATH,
    PLACEHOLDER_HTML_PATH,
    PROCESS_STAGE_UX_MAP_PATH,
    SANDBOX_PAGES,
    SANDBOX_SHARED_FILES,
    SANDBOX_WORKSPACE_FRAGMENTS,
    TERMINAL_JS_PATH,
)

router = APIRouter()

_CONTRACT_PATHS = {
    "loom-ui-intent-map.json": INTENT_MAP_PATH,
    "loom-system-intent-map.json": LOOM_SYSTEM_INTENT_MAP_PATH,
    "loom-pipeline-intent-map.json": LOOM_PIPELINE_INTENT_MAP_PATH,
    "loom-intent-forge-intent-map.json": LOOM_INTENT_FORGE_INTENT_MAP_PATH,
    "command-engine-ui-intent-map.json": COMMAND_ENGINE_INTENT_MAP_PATH,
    "process-stage-ux-map.json": PROCESS_STAGE_UX_MAP_PATH,
    "blueprint-ui.json": BLUEPRINT_UI_PATH,
    "experience-policy.json": EXPERIENCE_POLICY_PATH,
    "orchestration-event.schema.json": ORCHESTRATION_EVENT_SCHEMA_PATH,
    "orchestration-snapshot.schema.json": ORCHESTRATION_SNAPSHOT_SCHEMA_PATH,
    "orchestration-visual-grammar.json": ORCHESTRATION_VISUAL_GRAMMAR_PATH,
}


def _ui_file(path, media_type: str) -> FileResponse:
    if not path.exists():
        raise HTTPException(status_code=503, detail="UI page not found; check sandbox_frontend/ deployment")
    return FileResponse(path, media_type=media_type)


@router.get("/")
async def root_ui() -> FileResponse:
    return _ui_file(INTENT_FORGE_HTML_PATH, "text/html")


@router.get("/terminal")
async def terminal_ui() -> FileResponse:
    return _ui_file(PLACEHOLDER_HTML_PATH, "text/html")


@router.get("/command-engine")
async def command_engine_ui() -> FileResponse:
    return _ui_file(COMMAND_ENGINE_HTML_PATH, "text/html")


@router.get("/structural-canvas")
async def structural_canvas_alias() -> FileResponse:
    return _ui_file(SANDBOX_PAGES["topological-observatory"], "text/html")


@router.get("/internal")
async def neural_draft_ui() -> FileResponse:
    return _ui_file(SANDBOX_PAGES["hub"], "text/html")


@router.get("/ui/intent-forge.css")
async def intent_forge_css() -> FileResponse:
    return _ui_file(INTENT_FORGE_CSS_PATH, "text/html")


@router.get("/ui/intent-forge.js")
async def intent_forge_js() -> FileResponse:
    return _ui_file(INTENT_FORGE_JS_PATH, "text/html")


@router.get("/ui/command-engine.js")
async def command_engine_js() -> FileResponse:
    return _ui_file(COMMAND_ENGINE_JS_PATH, "text/html")


@router.get("/ui/terminal.js")
async def terminal_js() -> FileResponse:
    return _ui_file(TERMINAL_JS_PATH, "text/html")


@router.get("/ui/contracts/{contract_name}")
async def ui_contract(contract_name: str) -> JSONResponse:
    path = _CONTRACT_PATHS.get(contract_name)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown UI contract: {contract_name}")
    return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))


# ── Sandbox Frontend page routes ──
@router.get("/sandbox/{page_name}")
async def sandbox_page(page_name: str) -> FileResponse:
    path = SANDBOX_PAGES.get(page_name)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown sandbox page: {page_name}")
    return FileResponse(path, media_type="text/html")


@router.get("/shared/{asset_name}")
async def sandbox_shared_asset(asset_name: str) -> FileResponse:
    path = SANDBOX_SHARED_FILES.get(asset_name)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown sandbox shared asset: {asset_name}")
    media_type = "text/css" if asset_name.endswith(".css") else "application/javascript"
    return FileResponse(path, media_type=media_type)


@router.get("/workspaces/{fragment_name}")
async def sandbox_workspace_fragment(fragment_name: str) -> FileResponse:
    path = SANDBOX_WORKSPACE_FRAGMENTS.get(fragment_name)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown sandbox workspace fragment: {fragment_name}")
    return FileResponse(path, media_type="text/html")
