# PR 38 Remediations: Seal semantic authority, reflect dark curvature edges, and session-bind overrides

This PR addresses all three security review comments for PR 38 regarding P3 Semantic Authority Enforcement:

1. **Omitted proposal nodes validation**: Ensures that any canonical graph nodes omitted from the LLM proposal are generated as blocked `node_identity` violations, causing the verification pipeline to fail closed instead of silently granting full scope.
2. **Reflective dark-bridge edges evaluation**: Feeds `metrics["curvature_meta"]["edges"]` (produced by Ollivier-Ricci curvature evaluation) into the interaction graph's nodes so `_dark_edges()` can evaluate and correctly block curvature violations.
3. **Session-bound authority overrides**: Generates a unique 12-char session ID (`uuid.uuid4().hex[:12]`) per `analyze_cmd` run to prevent override token reuse/leakage across different analysis runs.

### Verification Run
- **Semantic Moat Tests**: Ran `python3 -m pytest tests/test_semantic_moat.py -q --no-cov` using the system Python 3.12 interpreter. All 40 test cases passed.
- **Import Smoke Test**: Verified that `aoc_cli.commands.analyze_.analyze_cmd` and `aoc_cli.commands.run_grid.run_grid_cmd` import cleanly without issues.
- **Linting & Formatting**: Checked with `ruff check` and `ruff format --check` on the modified files (all passed).
