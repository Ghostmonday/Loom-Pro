# Loom full dev automation — work queue

**Last reconciled:** 2026-06-26  
**For:** Director (gate) · Claw X-OPS + Codex (execution after green light)  
**Session start:** `docs/operations/clawx-session-start.md` ← **read every time**

## Stack order (NEVER flip)

```
1. TELEOLOGY  → teleology.json
2. CURVATURE  → topology + graph
3. LOOM MAPS  → ui/loom-*.json
4. CODEX      → Python/API
5. UI         → last
```

---

## Status board

| ID | Slice | Status | Notes |
|----|-------|--------|-------|
| C01–C23 | backend waves | ✅ on main | see git log |
| FIX | SNAP/venv + loom tests | ✅ verify | branch `fix/snap-venv-and-session-start` / PR #36 |
| **CRIT** | documentation + product critique mission | **NOW** | **blocks UI** — Amir green light per item |
| C12–C17 | UI wave | blocked | until CRIT mission addressed per Director gate |
| LOOM-210 | continuation+launch code | blocked | until C20 stable on main |
| SQ | skill sanity side quest | ⏳ | optional report |

---

# MISSION: Documentation & product critique (problems only)

**Authority:** Amir green-lights each critique item before maps, docs, or Codex work land.  
**Scope:** Every problem below must be **explicitly closed** — not paraphrased, not summarized away.  
**This section states problems only.** It does not prescribe fixes.

**Source sessions:**
- Podcast/documentation critique transcript (2026-06-26) — Gaijinn parallelization engine, differential geometry, agent orchestration docs
- Amir-approved product critique #1 (communication-first intake) — separate but blocking same gate

**Completion rule:** A critique item is done only when Director records Amir **green light** for that item ID in a GATE BRIEF. Until then, item stays open.

---

## CRIT-P1 — Product intake (Amir-approved #1)

**Domain:** Product / UI / teleology intake — not glossary-first documentation.

| ID | Problem |
|----|---------|
| P1-01 | The product presents architecture and glossary **before** the user can act or communicate intent in-flow. |
| P1-02 | Intake is not **communication-first** — users hit definitional or glossary material instead of a conversational teleology entry point. |
| P1-03 | Operational layers (teleology, curvature, maps, execution) are **revealed in wrong order for a human** — abstract structure precedes lived workflow. |
| P1-04 | There is no single contracted surface whose sole job is: receive natural-language intent first, then expose depth progressively. |
| P1-05 | Onboarding and teleology intake are conflated with reference documentation — same channel, wrong cognitive job. |

**Gate:** No `loom-communication-intent-map` (or equivalent onboarding map) on main without Amir green light on outline.

---

## CRIT-D1 — Layer 0 / 1 / 2 documentation structure

**Domain:** Gaijinn documentation — three operational layers, two-stage compiler, deployment context.

| ID | Problem |
|----|---------|
| D1-01 | Layer 0, Layer 1, and Layer 2 are documented **in complete isolation** — each defined at length before any reader sees how they are produced or consumed together. |
| D1-02 | The documentation treats the three layers as **academic abstractions** detached from runnable workflows. |
| D1-03 | **Greenfield** deployment context (entirely new project) appears only **after** the abstract layer definitions — not as the organizing frame. |
| D1-04 | **Brownfield** deployment context (existing codebase) appears only **after** the abstract layer definitions — not as the organizing frame. |
| D1-05 | The reader must hold highly abstract layer concepts **without an anchor** through multiple paragraphs before learning how layers are actually formed. |
| D1-06 | Cognitive load is excessive: the **two-stage compiler** concept is harder to grasp because formation order and deployment mode are separated from definitions. |
| D1-07 | The manual is written **top-down** (architecture-first) while the pragmatic engineer reads **bottom-up** (what happens when I run a command). |
| D1-08 | After reading the layer section, a reader still may not know **what the initialization instruction looks like** in the terminal — practical grounding is missing early. |
| D1-09 | Layer definitions read like a **dictionary memorization exercise** before the reader is shown how to "speak the language" of the system. |
| D1-10 | The documentation does not state early **how layer creation order differs** between greenfield and brownfield — order reversal (prompt→infer→generate vs extract→deduce) is late or implicit. |
| D1-11 | Brownfield path: the doc fails to tie **Pipeline 1** early to "statically extract Layer 1 from existing code, then deduce Layer 2" as the reader's entry story. |
| D1-12 | Greenfield path: the doc fails to tie early to "user prompts Layer 0 → system infers Layer 2 → generates Layer 1" as the reader's entry story. |
| D1-13 | A **start → created** state-transition example exists in the material but is **buried** deep in the topological inference section — readers hit theory before this operational illustration. |
| D1-14 | Readers are asked to absorb **graph theory and layer theory** before seeing how a brownfield scan operates in practice. |
| D1-15 | The doc answers "what is this academically?" **before** "how do I use this?" — wrong priority for the stated audience. |
| D1-16 | Merely reordering paragraphs without embedding definitions inside live workflows would leave the same isolation problem — the critique is about **structural coupling of definition to action**, not copy-edit alone. |

**Gate:** No wholesale rewrite of layer documentation signed off until D1-01 through D1-16 are mapped to explicit doc sections and Amir green lights.

---

## CRIT-D2 — Convergence score & honest accounting narrative

**Domain:** Phase 2 results, convergence metric, enterprise positioning, merge integrity story.

| ID | Problem |
|----|---------|
| D2-01 | The documentation reports a **0.8889** convergence score in real results (Phase 2) but frames the number in a way that triggers **failure reflex** in skimming readers. |
| D2-02 | A heading equivalent to **"Why 0.889 is success, not failure"** preemptively **defends** the score — which **introduces doubt** rather than confidence. |
| D2-03 | **Honest accounting** (workers with no fresh filesystem deltas flagged **pre-flight blocked** instead of recorded as successful work) is treated as something to apologize for, not as the headline integrity story. |
| D2-04 | The text explains that idle or delta-less workers are not merged as fake successes — but buries this under **defensive tone** instead of competitive positioning. |
| D2-05 | **Strict integrity checking** (refusing to merge air) is mechanically a major advantage but **reads like an excuse** for imperfection. |
| D2-06 | Enterprise readers who skim see **&lt; 1.0** and reflexively assume the tool is **flawed or incomplete**. |
| D2-07 | The documentation does not clearly separate, at a glance: **validation pass rate** (every agent obeyed its intent vector) vs **convergence** (actual filesystem delta / merge truth) — readers conflate them. |
| D2-08 | The material **actively questions whether sub-unity convergence is failure** — making Gaijinn look broken to casual readers despite strict behavior being correct. |
| D2-09 | **Skim factor** is ignored: bold defensive headings undermine trust before the body text can explain mechanics. |
| D2-10 | **Ghost merges** (legacy pattern: agent changes nothing, system still records successful merge to keep metrics at 100%) are not named and contrasted — reader has no language for why competitors' 1.0 may be misleading. |
| D2-11 | Gaijinn's sub-unity score is not positioned as **mathematically pure** reporting when redundant workers are blocked — the number's meaning is left fragile. |
| D2-12 | Phase 2 results section **under-sells** a disruptive paradigm: measuring truth instead of theater. |
| D2-13 | The narrative does not state offensively that **1.0 in competing systems can be a lie** — defensive posture only. |
| D2-14 | Every instance the system **refuses sketchy or empty work** is not highlighted as a reliability event the reader should want — missed trust-building. |

**Gate:** No public-facing results/convergence copy update without D2-01 through D2-14 addressed in outline and Amir green light.

---

## CRIT-D3 — Semantic synthesis LLM vs deterministic trust story

**Domain:** Pipeline 3, local LLM, semantic tagging, topology safety, mathematical guarantees.

| ID | Problem |
|----|---------|
| D3-01 | The documentation establishes trust through **pure mathematics** (curvature, reachability, deterministic pipelines) across most of the system. |
| D3-02 | **Pipeline 3 (semantic synthesis)** delegates **classification of ambiguous endpoints** to a **local LLM** — a probabilistic step. |
| D3-03 | The doc does not resolve the **conceptual friction**: system marketed as deterministic while a core pipeline step is non-deterministic. |
| D3-04 | The text claims replacement of human reasoning with **non-sension engineering pipelines**, then introduces an LLM that **reasons probabilistically** — apparent contradiction. |
| D3-05 | It is **unclear how LLM outputs are bounded** before they affect topology, permissions, or execution. |
| D3-06 | **Hallucination risk** is unaddressed: incorrect semantic tag → wrong **allowed_paths** → agent authorized on wrong subgraph. |
| D3-07 | **Shadow bridge** risk: misclassified node could bypass strict flow analysis if LLM guess is treated as ground truth. |
| D3-08 | Example failure mode documented in critique but not in product docs: security-sensitive function (e.g. database mutation / drop) mis-tagged as benign (e.g. frontend configuration) → wrong worker scope. |
| D3-09 | Reader cannot tell whether **Layer 0 domain rules schema** constrains LLM tags before graph mutation — boundary unstated. |
| D3-10 | Reader cannot tell whether tags are **locked into the static mathematical graph** before any agent runs — timing of enforcement unstated. |
| D3-11 | Reader does not know if **audit surfaces** LLM-classified nodes with **confidence scores** — observability gap. |
| D3-12 | No **end-to-end walkthrough** in docs showing misclassification detected by merge-integrity / reachability harness because actual data flow contradicts semantic tag. |
| D3-13 | The doc does not show a **violation fired** when LLM guess disagrees with provable topology — trust repair missing. |
| D3-14 | Heavy jargon (Ollivier–Ricci curvature, dark bridges at κ &lt; −0.3, texture reachability) builds credibility, then Pipeline 3 **undermines** that credibility without a clear **math-overrules-LLM** boundary story. |
| D3-15 | Reader left unsure whether LLM is advisory-only or authoritative for graph structure — **authority model unspecified**. |
| D3-16 | Fear of collisions is not fully dispelled because **uncertainty containment** in Pipeline 3 is undocumented. |

**Gate:** No semantic-synthesis / Pipeline 3 public documentation refresh without D3-01 through D3-16 addressed in outline and Amir green light.

---

## CRIT cross-cutting — Residual risks if items are "partially" closed

| ID | Problem |
|----|---------|
| X-01 | Addressing only three high-level themes without closing **every ID above** leaves psychological doubt (broken tool, untrusted math, unusable manual). |
| X-02 | Cosmetic edits (heading reword, paragraph move) do not close items D1-16, D2-14, D3-16 — structural and narrative gaps remain. |
| X-03 | **CRIT-P1** (product intake) and **CRIT-D1–D3** (documentation) overlap in spirit (context before glossary) but are **separate gates** — closing docs without product intake leaves onboarding broken. |
| X-04 | UI wave C12–C17 before critique gates risks encoding the criticized patterns into intent maps and UI. |
| X-05 | This mission does not cover any critique items **outside** the transcript and approved P1 — if Amir holds additional criticisms (2–16 elsewhere), they must be appended as new CRIT-* sections before declared complete. |

---

## Critique execution order (Director gates — not implementation spec)

| Order | Block | Amir action required |
|-------|-------|----------------------|
| 1 | CRIT-P1 outline | Green light before any onboarding/communication map |
| 2 | CRIT-D1 problem→doc mapping | Green light before layer-doc restructure |
| 3 | CRIT-D2 problem→doc mapping | Green light before convergence/results copy |
| 4 | CRIT-D3 problem→doc mapping | Green light before Pipeline 3 / LLM boundary copy |
| 5 | X-01–X-05 | Director confirms no open IDs remain |

**Claw X-OPS:** Do not run Codex on UI C12–C17 until Director records critique gates clear.  
**Director:** Produce GATE BRIEF per block; no solutions in brief without Amir asking — problems tracked by ID.

---

## Blockers (engineering — separate from CRIT)

PR #36 / `fix/snap-venv-and-session-start`: StrEnum Python 3.10 CI may still fail — OPS owns verify; Director recommends merge only after green CI and Amir says merge.

```bash
cd ~/Desktop/gaijinn
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
.venv/bin/python -m pytest tests/test_loom_mirror_forge.py::test_full_pipeline_mock \
  tests/test_loom_teleology.py -q --no-cov
```

---

## Execution waves

| Wave | Action | Status |
|------|--------|--------|
| Backend C01–C23 + FIX | integration | ✅ verify on branch |
| **CRIT** | P1 + D1 + D2 + D3 + X | **NOW** |
| 6 UI C12–C17 | blocked | until CRIT gates |
| 7 LOOM-210 | blocked | until C20 on main |

---

## Session paste

**Director (WebChat `loom-project-manager`):**
```
GATE SESSION: read automation-work-queue.md CRIT mission
Track open problems by ID (P1-*, D1-*, D2-*, D3-*, X-*)
Next: outline for Amir green light — no Codex until cleared
```

**Claw X-OPS:**
```
SESSION START per docs/operations/clawx-session-start.md
Load: loom-codex-delegate, loom-intent-mapping-v2
CRIT mission blocks UI — do not start C12 until Director clears
Reconcile queue to git; scoped pytest only
```