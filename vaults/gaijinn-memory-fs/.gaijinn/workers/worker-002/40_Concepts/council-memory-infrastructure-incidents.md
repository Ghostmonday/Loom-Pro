---
id: "CONCEPT-COUNCIL-MEMORY-INFRA-INCIDENTS"
type: "Concept"
status: "active"
tags: [Domain/Operations, Incidents]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-operational-hazards]]"
council_ref: "monorepo [1–38], vault [12–13]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Infrastructure incidents (distilled)

## 1. Dual-directory desync

**Symptom:** Competing manifests; cron on Desktop, scripts on workspace.  
**Fix:** All paths → `/home/ghost-monday/Desktop/Gaijinn`. `project.json` `project_root` must match.  
**Council:** monorepo [35], vault [37].

## 2. Spawn spiral / phantom spawn

**Symptom:** `phase=spawn`, dead PID, dev-loop throttles forever.  
**Causes:** manifest missing `status=completed`; `grid_spawn_ready=False`; stale 14-worker dirs.  
**Fixes:** Mark failed/completed; remove PID; reset state idle; convergence gate in dev-loop [57].

## 3. Codex + DeepSeek model mismatch

**Symptom:** `codex exec -m deepseek-v4-flash` → HTTP 400.  
**Fix:** executor=**hermes** for deepseek-v4-flash [31][34].

## 4. Executor profile schema drift

**Symptom:** dev-loop read `grid_executor` key absent in v5.  
**Fix:** Read `profiles[default_profile].executor` [34].

## 5. Linter infinite trap

**Symptom:** linter fail → can't cleanup → can't reach convergence 1.0.  
**Fix:** Cleanup at ≥0.875 simulated; converged early-exit [28][57].

## 6. council.jsonl corruption

**Symptom:** Line prefixes break `gaijinn council say`.  
**Fix:** Rebuild from council.md [56–57].

## 7. Stray WORK_UNIT.md at vault root

**Symptom:** Linter FAIL §6.1 frontmatter [132][58].  
**Fix:** Remove or add YAML frontmatter.