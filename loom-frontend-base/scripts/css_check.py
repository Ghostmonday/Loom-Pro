#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import tinycss2

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
errors = []
files = sorted(root.rglob("*.css"))
for path in files:
    rules = tinycss2.parse_stylesheet(path.read_text(encoding="utf-8"), skip_whitespace=False, skip_comments=False)
    for rule in rules:
        if getattr(rule, "type", None) == "error":
            errors.append(
                {
                    "file": str(path.relative_to(root)),
                    "line": getattr(rule, "source_line", None),
                    "column": getattr(rule, "source_column", None),
                    "message": getattr(rule, "message", "CSS parse error"),
                }
            )
result = {"passed": not errors, "checked_files": len(files), "errors": errors}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["passed"] else 1)
