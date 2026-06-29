"""Deterministic frontend scaffold generator CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validator.parser.manifest_loader import SchemaValidationError

from generator.core import GenerationError, generate_scaffold

DEFAULT_SPEC_DIR = Path(__file__).resolve().parents[2] / "specification"


def build_parser():
    parser = argparse.ArgumentParser(description="Generate a frontend scaffold that passes Frontend Formation")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--actions", required=True)
    parser.add_argument("--knowledge", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--spec-dir", default=str(DEFAULT_SPEC_DIR))
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = generate_scaffold(
            args.manifest,
            args.actions,
            args.knowledge,
            args.output,
            args.spec_dir,
            force=args.force,
        )
    except (GenerationError, SchemaValidationError, OSError) as error:
        print(f"GENERATION FAILED\n{error}", file=sys.stderr)
        return 1
    print(f"GENERATED — {Path(args.output).resolve()}")
    print(f"VALIDATED — {result.checked_screens} screen(s), 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
