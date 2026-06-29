# COMPOSER: START HERE — Perfect SPEC Interrogation

You are the parent integrator. Do not implement this feature as one undifferentiated coding task. Create the subagents and branches below, enforce file ownership, merge in the specified order, and prove the acceptance gates.

Canonical product contract: `docs/specs/PERFECT-SPEC-INTERROGATION.md`

Control branch: `orchestration/perfect-spec-interrogation-20260619`

Required base ancestry: PR #21 merge commit `807734a310b6b716a84b53e76fd732709c5bbc9f`

## Bootstrap commands

```bash
git fetch --all --prune
git switch orchestration/perfect-spec-interrogation-20260619
git pull --ff-only origin orchestration/perfect-spec-interrogation-20260619
git merge-base --is-ancestor 807734a310b6b716a84b53e76fd732709c5bbc9f HEAD
cat docs/specs/PERFECT-SPEC-INTERROGATION.md
```

Abort if the ancestry check fails.

Do not merge or cherry-pick open P0 branches `fix/ci-baseline-repair`, `pr/1-runtime-containment`, `pr/2-worker-governance`, `pr/3-transactional-billing`, or `pr/4-dogfood-evidence` into this feature stack. They remain a separate stack until deliberately reconciled.

## Concurrency policy

- Maximum simultaneous implementation subagents: **4**.
- Total subagent roles: **6**.
- Composer remains the only integration authority.
- Every subagent starts from the control branch or from the integration tip explicitly named below.
- No subagent may merge its own branch.
- No direct writes to `main`.
- No two active agents may own the same file.
- When an unplanned file is needed, the agent must report it to Composer rather than editing outside scope.

## Branch and worktree setup

Create worktrees or isolated checkouts for each branch.

```bash
git branch agent/spec-evidence-state orchestration/perfect-spec-interrogation-20260619
git branch agent/spec-adaptive-question-engine orchestration/perfect-spec-interrogation-20260619
git branch agent/spec-voice-ergonomics orchestration/perfect-spec-interrogation-20260619
git branch agent/spec-contract-tests orchestration/perfect-spec-interrogation-20260619
```

Run Wave 1 with four subagents in parallel. After Wave 1 passes branch-local tests, create an integration branch from the control branch and cherry-pick/merge Wave 1 in the required order.

```bash
git branch integration/perfect-spec-interrogation orchestration/perfect-spec-interrogation-20260619
```

Then create Wave 2 branches from the updated integration branch:

```bash
git branch agent/spec-service-integration integration/perfect-spec-interrogation
git branch agent/spec-independent-review integration/perfect-spec-interrogation
```

## Shared rules for every subagent

Prepend this block to every prompt:

> Read `docs/specs/PERFECT-SPEC-INTERROGATION.md` in full before editing. The product must not use a static questionnaire, fixed domain traversal, canned question queue, or pre-generated batch. Every answer must trigger a new complete-state analysis and exactly one newly selected question. Preserve existing session persistence, idempotency, revision, conflict, validation, and finalization behavior unless the canonical contract explicitly changes it. Use typed schemas, deterministic test doubles, clear error handling, and no broad test ignores. Do not expose private chain-of-thought; persist concise rationale, provenance, and analysis receipts only. Commit all work to your assigned branch and report changed files, tests, risks, and commit SHA.

---

# WAVE 1 — FOUR PARALLEL SUBAGENTS

## Subagent A — Evidence State and Analysis Snapshot

Branch: `agent/spec-evidence-state`

### Exclusive ownership

May create:

- `aoc_supervisor/aoc_supervisor/evidence_state.py`
- `aoc_supervisor/aoc_supervisor/spec_analysis_types.py`
- `aoc_supervisor/aoc_supervisor/analysis_receipts.py`

May modify:

- `aoc_supervisor/aoc_supervisor/intent_blueprint_state.py`

Must not modify:

- `question_policy.py`
- `intent_forge_service.py`
- `api.py`
- UI files
- test files

### Exact prompt

> Implement the canonical whole-state evidence model and immutable analysis snapshot for Perfect SPEC Interrogation. Start by auditing `intent_blueprint_state.py`, `intent_forge_service.py`, `intent_session_store.py`, `conflict_resolver.py`, and the canonical contract. Add typed structures and validation for evidence items, provenance, confidence, claim classification, unresolved uncertainty, resolution method, readiness, next action, and analysis receipts. Extend new session state compatibly with fields such as evidence revision, analysis revision, analysis receipts, project evidence, research evidence, environment evidence, latest analysis, ergonomics requirements, automation boundaries, accessibility requirements, and voice requirements. Existing serialized sessions must continue loading safely with defaults. Implement a deterministic function that builds a complete analysis snapshot from the entire state, including active and superseded answers, requirements, assumptions, contradictions, decisions, risks, acceptance criteria, graph, and all evidence sources. It must compute a stable digest from canonical JSON. Do not perform model inference and do not select questions. Provide validation helpers that reject malformed analysis output. Do not increment confidence merely because text exists. Keep `REQUIRED_DOMAINS` only as descriptive coverage compatibility; it must not control the conversation. Add docstrings and narrow unit-level self-checks only if they can live outside the central test files; otherwise report test cases for Subagent D.

### Required deliverables

- Complete-state snapshot builder.
- Backward-compatible state initialization/migration defaults.
- Strict analysis output validator.
- Canonical input and output digests.
- Receipt format without hidden reasoning content.
- Clear public interfaces for Subagents B and E.

### Branch-local verification

```bash
python -m compileall aoc_supervisor/aoc_supervisor
ruff check aoc_supervisor/aoc_supervisor/evidence_state.py \
  aoc_supervisor/aoc_supervisor/spec_analysis_types.py \
  aoc_supervisor/aoc_supervisor/analysis_receipts.py \
  aoc_supervisor/aoc_supervisor/intent_blueprint_state.py
```

---

## Subagent B — Adaptive AI Question Engine

Branch: `agent/spec-adaptive-question-engine`

### Exclusive ownership

May create:

- `aoc_supervisor/aoc_supervisor/adaptive_question_engine.py`
- `aoc_supervisor/aoc_supervisor/reasoning_provider.py`
- `aoc_supervisor/aoc_supervisor/reasoning_schema.py`

May modify:

- `aoc_supervisor/aoc_supervisor/question_policy.py`

Must not modify:

- `intent_blueprint_state.py`
- `intent_forge_service.py`
- `api.py`
- UI files
- test files

### Exact prompt

> Replace static-question behavior with an adaptive AI reasoning boundary while maintaining a narrow compatibility wrapper in `question_policy.py`. The production path must analyze a complete evidence snapshot and return one structured next action: DERIVE, RESEARCH, DEFAULT, CONFIRM, ASK, DEFER, NOT_APPLICABLE, CONFLICT_RESOLUTION, or FINALIZE. Implement a provider protocol plus a deterministic fake provider suitable for tests. Define and validate strict structured output containing facts, inferences, assumptions, contradictions, automatic resolutions, unresolved uncertainties, readiness, selected action, and at most one next question. Question selection must maximize expected reduction in implementation risk and rework. It must explicitly consider whether the answer can be derived, researched, defaulted, or marked N/A before ASK. Remove `DOMAIN_PROMPTS`, profile traversal, and fixed domain ordering from the production selection path. Descriptive domain coverage may remain for telemetry and compiled artifacts only. Add policy validation that rejects multiple questions, duplicate/re-asked decision targets, questions whose answers already exist in evidence, empty evidence citations, unsafe defaults, and malformed output. Provider failure must return a typed recoverable error and must never silently substitute canned prompts. Preserve compatibility entry points only where needed, but make them delegate to the new engine. Do not implement network-specific SDK code; provider adapters should be injectable and environment-neutral.

### Required deliverables

- Provider protocol.
- Deterministic fake provider.
- Strict request/response schema.
- Whole-state adaptive selection engine.
- Policy validator.
- Recoverable provider failure type.
- Compatibility wrapper for callers during integration.

### Branch-local verification

```bash
python -m compileall aoc_supervisor/aoc_supervisor
ruff check aoc_supervisor/aoc_supervisor/adaptive_question_engine.py \
  aoc_supervisor/aoc_supervisor/reasoning_provider.py \
  aoc_supervisor/aoc_supervisor/reasoning_schema.py \
  aoc_supervisor/aoc_supervisor/question_policy.py
```

---

## Subagent C — Voice, Accessibility, and Software Ergonomics

Branch: `agent/spec-voice-ergonomics`

### Exclusive ownership

May modify:

- `ui/views/command-engine.js`
- the current Intent Forge HTML/CSS files discovered from the PR #21 implementation
- `ui/gaijinn-ui-intent-map.json`
- UI-only schema or accessibility files when strictly necessary

May create UI-only helper modules under `ui/`.

Must not modify:

- Python backend files
- backend test files
- billing, grid, worker, or merge code

### Exact prompt

> Implement the user-facing Perfect SPEC interrogation experience and microphone integration against the existing PR #21 Intent Forge UI. First identify the actual current UI entry points; do not resurrect obsolete terminal surfaces. The UI must present exactly one current question, a concise reason it matters, a visible editable summary of what GAIJINN currently understands, and clear labels for confirmed, inferred, assumed, contradicted, unresolved, and defaulted information. Add autosave-safe answer composition, revise/undo affordances, progress that communicates readiness rather than checklist completion, and graceful provider/network retry states without losing text. Add microphone input as an equal optional path: push-to-talk by default, visible live transcript, editable transcript before submission, no auto-submit, clear stop/cancel, denied-permission and unsupported-browser fallback, keyboard access, accessible labels/focus/status announcements, and preservation of partial text on recognition errors or disconnects. Add optional question read-aloud using browser capabilities when available; user interruption must stop speech immediately. Do not retain raw audio and do not imply that audio is uploaded unless a later backend explicitly implements and discloses it. Preserve typed workflow fully when voice is unavailable. Update the UI intent map with states, actions, invariants, and confusion signals for analysis-in-progress, one-question presentation, microphone states, transcript editing, retry, and resume. Keep advanced controls progressively disclosed. Do not invent backend endpoints; isolate API assumptions in one adapter section and report the required contract to Composer.

### Required deliverables

- One-question-at-a-time adaptive UI.
- Understanding summary and provenance labels.
- Push-to-talk transcription flow.
- Editable transcript and typed fallback.
- Optional read-aloud and immediate interruption.
- Accessible state announcements and focus behavior.
- No text loss across ordinary error states.
- Updated UI intent map invariants.

### Branch-local verification

Run existing UI smoke tests available in the repository and any existing JavaScript syntax/lint checks. At minimum:

```bash
python -m pytest tests/test_ui_intent_smoke.py tests/test_e2e_golden_path.py -q
```

Report browser APIs used and fallback behavior.

---

## Subagent D — Contract Tests and Evaluation Harness

Branch: `agent/spec-contract-tests`

### Exclusive ownership

May create or modify only:

- `tests/test_adaptive_interrogation.py`
- `tests/test_interrogation_evidence.py`
- `tests/test_interrogation_voice_contract.py`
- `tests/test_intent_forge.py`
- test fixtures under `tests/fixtures/`
- `aoc_supervisor/aoc_supervisor/workflow_evaluator.py` only if evaluation metrics cannot live in tests

Must not implement production behavior elsewhere.

### Exact prompt

> Build deterministic acceptance tests for the canonical Perfect SPEC Interrogation contract. Tests must use an injected fake reasoning provider; never call a live model. Add fixtures that prove the complete state, including all prior answers and evidence, is sent on every turn. Prove that two different answers can produce different next questions; known facts are not re-asked; one and only one question is presented; a contradiction changes the next action; low-risk reversible choices can be defaulted; destructive, expensive, irreversible, safety-sensitive, or identity-dependent choices require ASK or CONFIRM; the engine can stop before every descriptive domain is touched; model/schema failure preserves session state and produces retryable status; revising an earlier answer invalidates dependent analysis and triggers complete reanalysis; superseded answers remain auditable but are not treated as current truth; and static `DOMAIN_PROMPTS` or fixed domain-order traversal no longer drive the production path. Add UI contract tests or static assertions for microphone controls: no auto-submit, transcript remains editable, unsupported/denied/error states preserve typed input, raw audio retention is absent by default, and accessible state labels exist. Extend workflow evaluation with metrics such as unnecessary_question_count, repeated_question_count, whole_state_reanalysis_rate, automatically_resolved_count, provider_recovery_success, and voice_fallback_integrity. Tests may initially fail on the integration branch, but each failure must correspond to a canonical requirement, not an implementation guess.

### Required tests

At minimum, cover all 15 Definition of Done items in the canonical contract.

### Branch-local verification

```bash
python -m pytest tests/test_adaptive_interrogation.py \
  tests/test_interrogation_evidence.py \
  tests/test_interrogation_voice_contract.py \
  tests/test_intent_forge.py -q
```

Expected on the isolated test branch: failures are acceptable only because production branches are not yet merged. Syntax/import collection must still be valid using temporary stubs or guarded imports where necessary; do not weaken assertions.

---

# WAVE 1 INTEGRATION

Composer must integrate in this order:

1. `agent/spec-evidence-state`
2. `agent/spec-adaptive-question-engine`
3. `agent/spec-voice-ergonomics`
4. `agent/spec-contract-tests`

Resolve only integration seams. Do not redesign agent work during merge. Run:

```bash
python -m compileall aoc_supervisor/aoc_supervisor
python -m pytest tests/test_intent_forge.py tests/test_adaptive_interrogation.py \
  tests/test_interrogation_evidence.py tests/test_interrogation_voice_contract.py -q
```

Record failing tests for Wave 2; do not delete or soften them.

---

# WAVE 2 — SERVICE INTEGRATION AND INDEPENDENT REVIEW

## Subagent E — Intent Forge Service/API Integration

Branch: `agent/spec-service-integration`

Base: latest `integration/perfect-spec-interrogation` after Wave 1.

### Exclusive ownership

May modify:

- `aoc_supervisor/aoc_supervisor/intent_forge_service.py`
- `aoc_supervisor/aoc_supervisor/api.py`
- `aoc_supervisor/aoc_supervisor/intent_forge_events.py`
- `aoc_supervisor/aoc_supervisor/intent_session_store.py`
- relevant API/event schemas

May make only minimal compatibility fixes in Wave 1 production modules after reporting them to Composer.

Must not redesign UI or tests.

### Exact prompt

> Integrate the evidence snapshot and adaptive question engine into the current PR #21 Intent Forge lifecycle. On paid session creation, ingest the intake prompt as evidence, build the complete snapshot, run one analysis pass, apply automatic resolutions, persist a receipt, and present at most one generated question. On every answer, skip, revision, conflict resolution, resume, or newly acquired evidence event, rebuild the complete snapshot from the full state and run a fresh analysis before selecting the next action. Do not append the raw answer as a confirmed requirement without semantic extraction from validated analysis output. Do not add a fixed confidence increment for any answer. Do not mark coverage complete merely because a question was answered. Persist state atomically with existing optimistic version/idempotency protections. Add explicit ANALYZING or equivalent recoverable state semantics without breaking persisted sessions. Provider/schema failures must preserve the previous committed state, answer draft where applicable, and expose an actionable retry response. Apply DERIVE/DEFAULT/NOT_APPLICABLE/DEFER actions without unnecessary user questions, with provenance and risk policy. Route contradictions through structured conflict resolution. FINALIZE only when readiness and validation gates pass. Expose concise analysis rationale, evidence references, readiness, current question, and recoverable error fields through the safe public session view; never expose hidden reasoning. Add event types for analysis started/completed/failed, automatic resolution, question selected, and readiness changed. Keep voice and typed answer submission semantically identical; the backend receives text plus optional input provenance only, never raw audio by default. Ensure free-tier behavior remains explicit and honest rather than pretending it completed a paid adaptive session.

### Required lifecycle assertions

- Initial prompt triggers analysis before first question.
- Every answer triggers a new analysis revision.
- Revision invalidates dependent facts and analysis receipts appropriately.
- Current question is replaced only after committed analysis.
- Retry is idempotent.
- Session resume reconstructs the same committed current state.
- No static fallback question appears on provider failure.

### Branch-local verification

```bash
python -m pytest tests/test_intent_forge.py \
  tests/test_adaptive_interrogation.py \
  tests/test_interrogation_evidence.py -q
ruff check aoc_supervisor/aoc_supervisor/intent_forge_service.py \
  aoc_supervisor/aoc_supervisor/api.py \
  aoc_supervisor/aoc_supervisor/intent_forge_events.py \
  aoc_supervisor/aoc_supervisor/intent_session_store.py
```

---

## Subagent F — Independent Adversarial Review

Branch: `agent/spec-independent-review`

Base: latest integration branch after Subagent E is merged.

### Exclusive ownership

May create:

- `docs/reviews/PERFECT-SPEC-INTERROGATION-REVIEW.md`

No production edits unless Composer assigns a narrowly scoped remediation after the review.

### Exact prompt

> Perform an adversarial architecture, product, safety, privacy, accessibility, and test review of the completed Perfect SPEC Interrogation stack against `docs/specs/PERFECT-SPEC-INTERROGATION.md`. Trace the real code path from session creation through every answer, revision, conflict, provider failure, resume, finalization, typed submission, and microphone submission. Attempt to prove any of the following failures: static prompts still influence production questioning; the next question was pre-generated; latest answer is analyzed without full history; known facts can be re-asked; domain completion masquerades as SPEC readiness; confidence rises mechanically; raw answers become requirements without extraction; multiple questions can be presented; provider failure silently falls back; state can be lost or double-applied; raw audio can be retained; voice can auto-submit; unsupported voice can break typing; accessibility status is missing; or tests only prove mocks rather than lifecycle behavior. Run the targeted suite and full suite. Produce a severity-ranked review with exact files/lines, reproduction steps, and required remediation. State PASS only if no P0/P1 finding remains and all canonical Definition of Done items have direct evidence.

### Review verification

```bash
python -m pytest tests/test_intent_forge.py \
  tests/test_adaptive_interrogation.py \
  tests/test_interrogation_evidence.py \
  tests/test_interrogation_voice_contract.py \
  tests/test_ui_intent_smoke.py \
  tests/test_e2e_golden_path.py -q
python -m pytest -q
```

---

# FINAL INTEGRATION PROTOCOL

Composer performs final integration. Do not ask a subagent to self-certify.

## Required merge order

1. Wave 1 branches in the stated order.
2. Subagent E service integration.
3. Remediation branches for any P0/P1 review findings.
4. Subagent F review document after rerun and final disposition.

## Required checks

```bash
python -m compileall aoc-cli/aoc_cli aoc_supervisor/aoc_supervisor
ruff check aoc-cli aoc_supervisor tests
python -m pytest tests/test_intent_forge.py \
  tests/test_adaptive_interrogation.py \
  tests/test_interrogation_evidence.py \
  tests/test_interrogation_voice_contract.py \
  tests/test_ui_intent_smoke.py \
  tests/test_e2e_golden_path.py -q
python -m pytest -q
```

Do not use `--ignore`, broad skips, xfail to hide unfinished behavior, or test deletion.

## Required manual smoke sequence

1. Start a paid Intent Forge session with a detailed prompt containing several known facts.
2. Confirm the first question does not repeat those facts.
3. Answer by typing; confirm analysis revision increments and exactly one new question appears.
4. Revise the first answer; confirm dependent understanding is invalidated and the new next question is recomputed.
5. Introduce a contradiction; confirm conflict resolution supersedes normal questioning.
6. Simulate provider failure; confirm no canned question appears and typed text/state survive retry.
7. Use microphone push-to-talk; edit transcript before submitting.
8. Deny microphone permission; confirm typing remains intact.
9. Interrupt read-aloud; confirm it stops immediately.
10. Resume the session after server/UI restart; confirm current question and understanding are restored.
11. Continue until readiness finalizes before a fixed domain checklist is exhausted.
12. Inspect the final rich artifact and executable projection for provenance, assumptions, risks, ergonomics, automation boundaries, voice/accessibility requirements, and acceptance evidence.

## Completion report

Composer must produce `docs/reviews/PERFECT-SPEC-INTERROGATION-COMPLETION.md` containing:

- branch and commit graph;
- subagent roster;
- changed files by owner;
- provider and schema architecture;
- evidence that every answer triggers complete-state reanalysis;
- evidence that static prompt traversal is gone from production;
- targeted and full test results;
- manual smoke results;
- remaining P2/P3 risks;
- explicit PASS/FAIL for every Definition of Done item;
- exact integration commit SHA;
- proposed PR title and body.

## Stop rules

Stop and report rather than improvising when:

- a required base commit is absent;
- the control branch has unexpected divergence;
- two agents require the same file;
- an agent attempts to reintroduce static questionnaires;
- provider integration would require undocumented credentials or a vendor lock-in decision;
- tests reveal a P0/P1 state-loss, privacy, security, billing, or execution-containment regression;
- the open P0 stack must be reconciled before safe final merge.

The objective is not maximum code volume. The objective is a provably adaptive, low-burden, voice-capable interrogation engine that produces an execution-ready SPEC without forcing the user to become the system analyst.
