"""activate command implementation."""

from __future__ import annotations

import hashlib

import typer

from ..helpers import LICENSE_PATH, _ensure_gaijinn_dir, _preview_license_key, _write_json


def activate_cmd(license_key: str) -> None:
    """Store local activation metadata in .gaijinn/license.json."""
    license_key = license_key.strip()
    if not license_key:
        raise typer.BadParameter("LICENSE_KEY must not be empty")

    _ensure_gaijinn_dir()
    payload = {
        "schema_version": 1,
        "status": "active",
        "license_key_hash": hashlib.sha256(license_key.encode("utf-8")).hexdigest(),
        "license_key_preview": _preview_license_key(license_key),
    }
    _write_json(LICENSE_PATH, payload)
    typer.echo(f"Activation metadata written to {LICENSE_PATH}")
