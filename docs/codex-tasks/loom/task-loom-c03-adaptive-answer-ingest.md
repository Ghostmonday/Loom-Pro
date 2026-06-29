# Loom C03 — Adaptive Answer Ingestion (LOOM-202)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Intent:** `ui/loom-pipeline-intent-map.json` → `actions.question.submit_answer.algorithm_binding.gap`

## Objective

On `POST /answers`, run evidence reanalysis via `AdaptiveQuestionEngine` / `build_next_question` **before** selecting next question. Remove raw-append-only path in `_apply_answer_to_state`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/intent_forge_service.py`
- `aoc_supervisor/aoc_supervisor/question_policy.py`
- `tests/test_intent_forge.py` or `tests/test_loom_mirror_forge.py`

## MUST NOT edit

- UI files

## Steps

1. After answer persisted, call `build_analysis_snapshot` + provider analyze path.
2. Merge extracted claims into `confirmed_requirements` from analysis output, not blind append.
3. Add `ANALYZING` to public session view during reanalysis (match contract).
4. Test: paid session answer changes `readiness` or `understanding` deterministically with `GAIJINN_FAKE_REASONING=1`.

## Verify

```bash
.venv/bin/python -m pytest tests/test_intent_forge.py tests/test_loom_mirror_forge.py -q --no-cov -k "adaptive or answer"
```