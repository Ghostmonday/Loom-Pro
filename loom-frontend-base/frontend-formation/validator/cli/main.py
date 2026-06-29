"""Frontend-Formation validator command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validator.core import ValidationResult
from validator.engine import io_violation, schema_violations, validate_project, validate_screen
from validator.parser.manifest_loader import (
    SchemaValidationError,
    load_action_registry,
    load_knowledge_registry,
)

DEFAULT_SPEC_DIR = Path(__file__).resolve().parents[2] / "specification"


def _render_text(result: ValidationResult) -> str:
    if result.passed:
        return (
            f"PASS — {result.checked_screens} screen(s) checked\n"
            "0 violations. Rules 1–7 satisfied within the static-analysis boundary.\n"
        )
    body = "\n".join(v.format().rstrip() for v in result.violations)
    return (
        f"{body}\n\n--- {result.error_count} error(s), "
        f"{result.warning_count} warning(s); {result.checked_screens} screen(s) checked ---\n"
    )


def _single_screen(args, spec_dir: Path) -> ValidationResult:
    result = ValidationResult()
    try:
        actions = load_action_registry(args.actions, spec_dir)
        knowledge = load_knowledge_registry(args.knowledge, spec_dir)
    except SchemaValidationError as error:
        result.extend(schema_violations(error))
        return result
    except OSError as error:
        result.violations.append(io_violation("registry", error))
        return result
    return validate_screen(args.manifest, args.html, actions, knowledge, spec_dir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Loom Frontend-Formation compiler validator")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--project", help="Path to frontend-formation.yaml")
    mode.add_argument("--manifest", help="Path to one screen.manifest.yaml")
    parser.add_argument("--html", help="HTML path for single-screen mode")
    parser.add_argument("--actions", help="Action registry for single-screen mode")
    parser.add_argument("--knowledge", help="Knowledge registry for single-screen mode")
    parser.add_argument("--spec-dir", default=str(DEFAULT_SPEC_DIR))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    spec_dir = Path(args.spec_dir)

    if args.project:
        result = validate_project(args.project, spec_dir)
    else:
        missing = [name for name in ("html", "actions", "knowledge") if not getattr(args, name)]
        if missing:
            parser.error("single-screen mode requires --html, --actions, and --knowledge")
        result = _single_screen(args, spec_dir)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(_render_text(result), end="")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
