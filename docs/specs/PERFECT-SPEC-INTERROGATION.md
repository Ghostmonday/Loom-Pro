# Perfect SPEC Interrogation — Canonical Product Contract

Status: **normative implementation contract**

Base: `main` containing PR #21 merge commit `807734a310b6b716a84b53e76fd732709c5bbc9f`

## Product truth

GAIJINN's first product is not generated code. Its first product is a sufficiently complete, internally consistent, evidence-grounded, executable SPEC.

The user supplies vision and truly user-dependent decisions. GAIJINN carries the cognitive burden of gathering context, organizing facts, researching or deriving what it can, detecting contradictions, selecting defaults, and asking only the questions that remain necessary.

## Non-negotiable interrogation loop

GAIJINN MUST NOT run a static questionnaire, fixed domain sequence, canned checklist, or batch interview.

Every turn follows this loop:

1. Ingest the newest answer without treating it as isolated text.
2. Rebuild the analysis input from the complete session state and every currently available evidence source.
3. Reclassify all relevant claims as confirmed, inferred, assumed, contradicted, unresolved, deferred, non-goal, constraint, decision, risk, or acceptance criterion.
4. Recompute dependencies, confidence, contradictions, information gaps, and SPEC readiness.
5. Resolve any gap that can safely be derived, researched, defaulted, or marked not applicable without burdening the user.
6. Identify only the remaining user-dependent uncertainties.
7. Rank them by expected reduction of implementation risk and downstream rework.
8. Ask exactly one natural-language question: the highest-value question that cannot safely be answered another way.
9. After the answer, repeat the entire analysis from step 1.
10. Stop questioning when no blocking or high-value user-dependent uncertainty remains.

The next question MUST be generated from the new whole-state analysis, not selected from a predetermined list and not generated from only the latest answer.

## Ask/derive/research/default policy

Before asking the user, the engine MUST choose among:

- `DERIVE`: logically implied by accepted evidence.
- `RESEARCH`: obtainable from authorized tools, repository data, documents, environment metadata, or reliable external sources.
- `DEFAULT`: reversible, low-risk choice with a strong ergonomic default.
- `CONFIRM`: inferred with meaningful consequence and requiring concise confirmation.
- `ASK`: genuinely subjective, identity-dependent, business-dependent, destructive, expensive, irreversible, safety-sensitive, or otherwise unavailable.
- `DEFER`: intentionally postponed without blocking the current SPEC.
- `NOT_APPLICABLE`: proven irrelevant to this product.

`ASK` is the last resort, not the default.

## Question quality contract

A presented question MUST:

- ask one decision at a time;
- explain why the answer matters when that is not obvious;
- reflect already-known facts so the user can see that GAIJINN listened;
- avoid asking for information already present anywhere in evidence;
- avoid demanding implementation details when the user is expressing product intent;
- offer a recommended default when a reversible default exists;
- provide options only when they help rather than constrain the user's answer;
- permit natural free-form speech or text;
- preserve domain vocabulary, names, and prior decisions;
- never expose internal chain-of-thought; provide concise decision rationale and provenance instead.

## Whole-state analysis input

Each analysis pass receives a deterministic snapshot containing at least:

- original intent;
- all active and superseded answers;
- confirmed and inferred requirements;
- assumptions and confidence;
- constraints and non-goals;
- decisions and rationale;
- contradictions and resolutions;
- unresolved and deferred items;
- risks;
- acceptance criteria;
- blueprint dependency graph;
- domain coverage as descriptive telemetry, not a questionnaire order;
- repository and project evidence;
- uploaded/authorized document evidence;
- authorized tool or research evidence;
- environment and deployment evidence;
- prior analysis receipts;
- user experience, automation, accessibility, and voice requirements;
- model/provider metadata needed for reproducibility.

## Analysis output contract

The reasoning engine returns structured data that can be validated before mutating session state:

```json
{
  "analysis_revision": 1,
  "evidence_revision": 1,
  "state_digest": "sha256:...",
  "facts": [],
  "inferences": [],
  "assumptions": [],
  "contradictions": [],
  "resolved_without_user": [],
  "unresolved": [],
  "readiness": {
    "score": 0.0,
    "blocking_count": 0,
    "high_value_unknown_count": 0,
    "ready_to_finalize": false,
    "reason": ""
  },
  "next_action": "ASK",
  "next_question": {
    "question_id": "q_...",
    "text": "",
    "decision_target": "",
    "why_it_matters": "",
    "evidence_used": [],
    "alternatives_considered": [],
    "recommended_default": null,
    "risk_if_wrong": "low",
    "answer_mode": "freeform"
  }
}
```

The engine may return `next_question: null` only when it returns a valid non-ASK action or the SPEC is ready to finalize.

## Determinism and provider design

Production questioning is AI-generated, but the system must remain testable and auditable.

- Put model access behind a provider interface.
- Validate every model response against a strict schema.
- Use a deterministic fake provider in tests.
- Persist an analysis receipt containing input digest, output digest, provider/model ID, policy version, and timestamp.
- Reject malformed, multi-question, evidence-free, or policy-violating outputs.
- On provider failure, preserve the session and offer retry; do not silently fall back to the old static questionnaire.
- A conservative deterministic fallback may identify that more analysis is unavailable, but it must not pretend canned questions are adaptive AI reasoning.

## Quality of life and software ergonomics

These are first-class SPEC dimensions, not optional polish:

- minimal cognitive load;
- progressive disclosure;
- sensible reversible defaults;
- one obvious next action;
- autosave and crash-safe resume;
- undo/revise answer;
- visible summary of what GAIJINN currently understands;
- clear distinction between confirmed, inferred, assumed, and unresolved information;
- concise explanations of why a question is being asked;
- no repeated questions;
- no loss of typed or dictated text;
- keyboard-only operation;
- accessible labels, focus behavior, and status announcements;
- graceful offline/network/provider failure handling;
- no unnecessary setup steps;
- automation that is safe by default and interruptible by the user.

## Microphone and voice contract

Voice is an equal input path, not a novelty button.

Required behavior:

- push-to-talk is the default;
- live transcription is visible;
- transcript remains editable before submission;
- voice never auto-submits by default;
- stop/cancel controls are obvious;
- unsupported browser and denied-permission states fall back cleanly to typing;
- partial transcripts survive recognition errors, disconnects, and UI state changes;
- project names and technical vocabulary can be corrected without fighting autocorrection;
- optional read-aloud of the current question and concise understanding summary;
- user interruption stops read-aloud immediately;
- microphone state is visibly and accessibly announced;
- raw audio is not retained unless the user explicitly opts in;
- transcription provenance is recorded as voice-derived text without storing audio by default;
- microphone integration must not block the core typed workflow.

## Mandatory requirement dimensions

The engine must analyze these dimensions, but MUST NOT ask one question for every dimension merely because the dimension exists:

- product outcome and non-goals;
- users and critical journeys;
- functional behavior;
- business and safety invariants;
- data and lifecycle;
- interfaces and error behavior;
- security, privacy, and authorization;
- reliability, performance, deployment, and observability;
- acceptance evidence;
- software ergonomics and cognitive load;
- automation opportunities and approval boundaries;
- accessibility;
- microphone/voice interaction;
- recovery, revision, and continuity.

## Stop condition

Questioning stops when all of the following are true:

- no unresolved contradiction blocks execution;
- no unresolved item with material implementation risk requires the user's judgment;
- acceptance criteria can prove the critical requirements;
- assumptions above the allowed risk threshold have been confirmed or reduced;
- architecture and work decomposition can proceed without agents inventing product decisions;
- remaining unknowns are explicitly low-risk defaults, deferred items, or non-applicable.

Completing a checklist of domains is not a valid stop condition. Exhausting a list of prompts is not a valid stop condition.

## Explicitly forbidden implementation

- `DOMAIN_PROMPTS` as the primary source of presented questions;
- a fixed `REQUIRED_DOMAINS` traversal controlling conversation order;
- asking all questions in a batch;
- generating several questions and revealing them one by one without reanalysis;
- treating each answer as a requirement verbatim without semantic extraction;
- increasing confidence by a fixed amount merely because any answer was supplied;
- marking a domain complete solely because it was asked;
- quietly substituting canned prompts when the AI provider fails;
- voice auto-submit;
- storing raw microphone audio by default;
- requiring the user to repeat facts already available to the system.

## Definition of done

The implementation is done only when automated evidence proves:

1. Every submitted answer triggers a fresh complete-state analysis call.
2. The analysis input includes prior answers and current evidence, not just the latest answer.
3. The next question is generated from structured unresolved uncertainty.
4. Known facts are not re-asked.
5. Two different answers to the same question can produce different next questions.
6. A new contradiction changes the next action to conflict resolution.
7. Reversible low-risk choices can be defaulted without asking.
8. High-impact subjective or irreversible choices are asked or confirmed.
9. Exactly one question is presented at a time.
10. The engine can stop early when the SPEC is ready, regardless of untouched descriptive domains.
11. Provider/schema failure preserves state and produces an actionable recovery path.
12. Typed and voice input produce the same answer-submission semantics.
13. Voice denial/unsupported/error states preserve the typed workflow and user text.
14. Resume, revise, and undo behavior remains correct.
15. The complete relevant test suite passes without broad ignores.
