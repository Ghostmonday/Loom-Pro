"""Hermes CLI argv for Gaijinn orchestrator and DeepSeek grid workers."""

from __future__ import annotations

import os
from pathlib import Path

from .constants import DEEPSEEK_DEFAULT_PROVIDER, HERMES_BINARY
from .project_profile import load_executor_profile


def _hermes_configured_provider() -> str:
    """Read the actual provider configured in ~/.hermes/config.yaml.

    Falls back to empty string if the config can't be parsed or has no provider.
    Used so grid workers don't silently fail when DEEPSEEK_DEFAULT_PROVIDER isn't
    registered in the user's hermes home (e.g. sandbox with only MiniMax-M3).
    """
    cfg_path = Path(os.path.expanduser("~/.hermes/config.yaml"))
    if not cfg_path.exists():
        return ""
    try:
        import yaml  # PyYAML is already a hermes dep, safe to import.
    except ImportError:
        return ""
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except (OSError, Exception):
        return ""
    if not isinstance(cfg, dict):
        return ""
    model_block = cfg.get("model", {}) if isinstance(cfg.get("model"), dict) else {}
    provider = str(model_block.get("provider", "") or "").strip()
    return provider


def deepseek_provider(project_root: Path | None = None) -> str:
    """Resolve which --provider value to pass to `hermes`.

    Priority: env var > project.json deepseek_provider > configured hermes home
    provider > DEEPSEEK_DEFAULT_PROVIDER constant. Reading the user's actual
    hermes home keeps grid workers working on machines where the constant
    ("deepseek") isn't a registered provider.
    """
    return (
        os.environ.get("GAIJINN_DEEPSEEK_PROVIDER", "").strip()
        or load_executor_profile(project_root).get("deepseek_provider", "").strip()
        or _hermes_configured_provider()
        or DEEPSEEK_DEFAULT_PROVIDER
    )


def hermes_model(project_root: Path | None = None, override: str = "") -> str:
    if override.strip():
        return override.strip()
    return load_executor_profile(project_root).get("hermes_model", "").strip()


def build_hermes_argv(
    prompt: str,
    *,
    project_root: Path | None = None,
    model: str = "",
    provider: str | None = None,
    yolo: bool = False,
    cwd: Path | None = None,
) -> list[str]:
    resolved_model = hermes_model(project_root, model)
    resolved_provider = (provider if provider is not None else deepseek_provider(project_root)).strip()
    argv = [HERMES_BINARY]
    if resolved_model:
        argv.extend(["-m", resolved_model])
    if resolved_provider:
        argv.extend(["--provider", resolved_provider])
    if cwd is not None:
        argv.extend(["--cwd", str(cwd.resolve())])
    argv.extend(["-z", prompt])
    if yolo:
        argv.append("--yolo")
    return argv
