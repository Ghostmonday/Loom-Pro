# Onboarding & Progressive Disclosure Map

To reduce cognitive load and avoid glossary-first patterns, Loom uses a progressive disclosure onboarding flow. This map defines a single, unified communication-first entry surface that accepts natural-language user intent first, progressively unfolding the deeper layers of teleology, curvature, maps, and execution.

---

## 1. Onboarding Phase Sequence

The onboarding flow transitions a user from a blank input to a configured worker grid in four distinct phases:

```
[ Phase 1: Intake ] ──(Natural Language Intent)──> [ Phase 2: Teleology ]
                                                           │
                                                  (Decomposed Goals)
                                                           │
                                                           ▼
[ Phase 4: Execution ] <──(GIV Safety Envelopes)── [ Phase 3: Topology ]
```

---

## 2. Progressive Disclosure Specification

### Phase 1: Natural Language Intake (The Entry Surface)
- **Visuals**: A clean, center-focused input field (the Vision Canvas / Intent Input) with zero architectural jargon.
- **Cognitive Job**: Accept the user's software goals (e.g. "I want to build a backend Python API with Postgres and JWT auth").
- **System Action**: Ingest the raw natural-language intent and initialize a new Layer 0 session. Reference documentation and topological structures remain hidden.

### Phase 2: Teleology (progressive revelation of objectives)
- **Visuals**: The input collapses into a top summary bar, and the system reveals a structured checklist of **Inferred Goals** and **Requirements**.
- **Cognitive Job**: Let the user edit, confirm, or add new high-level objectives.
- **System Action**: Decompose Layer 0 intent into a structured teleology tree (inferred features, database schemas, authentication scopes).

### Phase 3: Topology (progressive revelation of structure)
- **Visuals**: The workbench expands to show the repository visualization (Function-Realization Graph) and detected edge weights.
- **Cognitive Job**: Let the user verify files to be touched and see where coupling exists.
- **System Action**: Run static AST extraction (Layer 1) and calculate Ollivier-Ricci curvature to detect **Dark Bridges** (κ < -0.3). Highlight structural bottlenecks to explain why specific files must be welded.

### Phase 4: Grid Execution (progressive revelation of action)
- **Visuals**: Show individual worker cards showing allowed/denied paths, command boundaries, and running logs (PULSE/Console).
- **Cognitive Job**: Let the user trigger parallel execution with clear scope limits.
- **System Action**: Generate GIV contracts, configure Git worktrees/copies (Layer 2), and spawn execution cells (Grok sprint).

---

## 3. Decoupling Documentation from Onboarding

Onboarding maps and references are explicitly separated:
- **Intake Channel**: Only handles active user communication and workspace state generation. No definitions, glossary tables, or academic explanations of curvature/ Wasserstein distance are presented.
- **Documentation Channel**: Accessible via a persistent `Help` button, linking directly to the logical guides (`Why Loom Exists` → `How Loom Thinks` → `deterministic-authority.md`). Jargon is deferred until the user asks for conceptual reference.
