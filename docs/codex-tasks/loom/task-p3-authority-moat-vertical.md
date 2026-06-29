# P3 Authority-Moat Vertical Slice

**Status:** Implemented  
**Verify:** `tests/test_semantic_moat.py`  
**Branch:** `integration/algorithm-wiring-remediation`  
**NO UI files.**  

## Summary

Convert the D3 authority-model blueprint into a tested vertical slice through `semantic_moat`, graph verification, scope compilation, audit persistence, and blocked-run handling.

## Files

| File | Action |
|------|--------|
| `aoc-cli/aoc_cli/semantic_moat.py` | Rewrite — fix `_llm_enrich()`, add `ProvisionalTag`, add permitted-tag vocabulary |
| `aoc-cli/aoc_cli/moat_authority.py` | **New** — `verify_semantic_boundary()` chokepoint |
| `aoc-cli/aoc_cli/moat.py` | Add `compose_allowed_paths()` narrow-only composition |
| `tests/test_semantic_moat.py` | Add 10 adversarial + 1 integration test; preserve all 6 existing |

## Design

### 1. Semantic Taxonomy

Permitted tags and their restriction meanings:

- `"security"` → restrict to `aoc-cli/aoc_cli/`, `tests/`, `docs/`
- `"payments"` → restrict to `aoc_supervisor/aoc_supervisor/billing.py`, `tests/`, `docs/`
- `"orchestration"` → restrict to `aoc-cli/aoc_cli/`, `aoc_supervisor/aoc_supervisor/`, `tests/`
- `"configuration"` → restrict to `templates/`, `config/`, `tests/`, `docs/`
- `"destructive"` → restrict to `tests/`, `docs/`
- `"general"` → full project scope

### 2. ProvisionalTag (never replaces canonical graph)

LLM output parsed into typed records:

```python
@dataclass
class ProvisionalTag:
    node_key: str
    tag: str
    confidence: float
    provenance: str  # "llm" | "deterministic"
```

Stored parallel to the canonical interaction graph. The canonical graph is never mutated by LLM output.

### 3. verify_semantic_boundary() — single chokepoint

Six checks in order:

1. **Vocabulary** — tag must be in permitted set
2. **Confidence** — ≥ 0.6 or rejected
3. **Mutation reachability** — destructive tag must not reach `source_file` outside tests/docs
4. **Dataflow puncture** — puncture_risk flagged nodes must have verified tag
5. **Dark bridge** — shadow bridge edges require ≥ 0.75 confidence
6. **Node identity** — node_key must correspond to a real graph node

Output: `list[ViolationRecord]`

### 4. Narrow-only composition

```python
def compose_allowed_paths(
    steps: Sequence[str],
    node_by_intent: Mapping[str, Mapping[str, Any]],
    verified_tags: dict[str, ProvisionalTag] | None = None,
) -> list[str]:
```

Static analysis establishes max scope (parent directories of `source_file`). Verified tags may only **remove** paths, never add them.

### 5. Observable containment

```python
@dataclass
class ViolationRecord:
    check: str          # which of the 6 checks
    node_key: str
    tag_attempted: str | None
    message: str
    severity: str       # "blocked" | "warning"
```

BLOCKED_PENDING_REVIEW semantics: when severity is "blocked", the run is not authorized. Human override stub at `moat_authority.human_override()`.

## Verify

```bash
cd ~/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
.venv/bin/python -m pytest tests/test_semantic_moat.py -q --no-cov
```
