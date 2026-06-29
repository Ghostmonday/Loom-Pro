---
id: "WU-004-deploy-path-validation"
type: "Concept"
status: "active"
scope: "deploy-path"
tags:
  - Deploy-Path
  - Validation
  - Resilience
  - Disaster-Recovery
  - Domain/Operations
links:
  - "[[ui/vault-ui-intent-map]]"
  - "[[10_Operations/agents/promoter/promote.sh]]"
  - "[[10_Operations/agents/promoter/validate_promotion.py]]"
  - "[[project.executor-profile]]"
  - "[[.agents/vault]]"
  - "[[_multi-agent/events]]"
  - "[[.gaijinn/bridge/council]]"
  - "[[raw/constitution-v0-section-xiii]]"
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
---

# WU-004: Deploy Path Validation

> Schema v4 — Three-gate deploy pipeline with resilience, circuit breaker,
> retry backoff, and disaster recovery.

**Source binding:** `[[ui/vault-ui-intent-map]]` — deploy_path,
resilience, and disaster_recovery sections define the
intent map that this document validates against.

**Promotion executor:** `[[10_Operations/agents/promoter/promote.sh]]`
**Validation engine:** `[[10_Operations/agents/promoter/validate_promotion.py]]`

---

## 1. Pipeline Overview

```
  [discover] → [write_manifest] → [gate_mirror] → [gate_perf] → [gate_human] → [promote]
     ↓               ↓                  ↓              ↓              ↓
  name, size,   manifest_path,    confusion_     perf-bench-    human-       promotion
  file_count,   checksum          count == 0     results.json  signoff.md   execute
  wiki_links                                      passed        approved
```

All three gates must pass sequentially. No gate may be skipped.
Promotion requires: `mirror_passed AND perf_passed AND human_approved`.

---

## 2. Resilience Framework (Schema v4)

### 2.1 Circuit Breaker

| Property | Value |
|----------|-------|
| enabled | true |
| failure_threshold | 3 consecutive failures |
| recovery_timeout_s | 60 seconds |
| half_open_max_requests | 1 |
| states | closed → open → half_open → closed |

**Behavior:**
- **CLOSED** — normal operation, all requests pass through
- **OPEN** — after `failure_threshold` consecutive failures; all requests fail-fast
- **HALF_OPEN** — after `recovery_timeout_s`; one probe request allowed
  - Success → CLOSED
  - Failure → OPEN (counter resets)

### 2.2 Retry Backoff

| Property | Value |
|----------|-------|
| enabled | true |
| initial_delay_s | 1 |
| max_delay_s | 30 |
| multiplier | 2.0 (exponential) |
| max_retries | 3 |

**Formula:** `delay = min(initial_delay_s * multiplier^attempt, max_delay_s)`
**Jitter:** ±10% applied to each delay.

### 2.3 Gate-Specific Failure Handling

| Gate | Action | Max Retries | Timeout |
|------|--------|------------|---------|
| Mirror | retry | 2 | 60s |
| Perf | rebench | 1 | — |
| Human | notify_amir | 0 (no retry) | — |

### 2.4 Graceful Degradation

| Property | Value |
|----------|-------|
| enabled | true |
| fallback_mode | reduce_workers |
| reduction_factor | 0.5 |

When circuit breaker trips, executor worker count is halved. Dual-ledger
update is performed at every degradation step.

---

## 3. Disaster Recovery Procedures

### 3.1 Worker Crash

- **Trigger:** worker status == crashed OR worker timeout > max_wait
- **Procedure:**
  1. Mark worker as FAILED in metrics manifest
  2. Reassign orphaned work units to remaining workers
  3. Restart worker pool with remaining workers
  4. Log material change to `[[_multi-agent/events]]` and `[[.gaijinn/bridge/council]]`

### 3.2 Merge Failure

- **Trigger:** merge_pipeline.blocked > 0 OR merge_pipeline.conflicted > 0
- **Procedure:**
  1. Identify conflicts from merge output
  2. Attempt auto-resolve via OCC replay
  3. If unresolved: mark for human review
  4. Log material change to both ledgers

### 3.3 Vault Linter Violation

- **Trigger:** linter exit code != 0
- **Procedure:**
  1. Capture full linter output
  2. Auto-fix trivial violations (orphan wikilinks with existing target files, frontmatter field ordering)
  3. If non-trivial: block promotion, do not bypass
  4. Log material change to both ledgers

### 3.4 Dual-Ledger Desync

- **Trigger:** ledger checksum mismatch between semantic `[[_multi-agent/events]]` and operational `[[.gaijinn/bridge/council]]`
- **Procedure:**
  1. Snapshot current state of both ledgers
  2. Reconcile from events log (chronological replay)
  3. Verify checksums match after reconciliation
  4. Log material change to both ledgers

### 3.5 Circuit Breaker Trip

- **Trigger:** circuit_breaker.state == open
- **Procedure:**
  1. Enter graceful degradation mode
  2. Backoff all executor calls to circuit
  3. Schedule health check at recovery_timeout_s
  4. If half_open probe succeeds: close circuit
  5. Log material change to both ledgers

---

## 4. Deploy Path

### 4.1 Discovery
- **Action:** `vault.discover`
- **API:** `POST /api/v1/vault/discover`
- **Returns:** name, file_count, total_size, wiki_links

### 4.2 Write Manifest
- **Action:** `vault.write_manifest`
- **API:** `POST /api/v1/vault/manifest`
- **Returns:** manifest_path, checksum

### 4.3 Gate Mirror (Smoke)
- **Action:** `gate.mirror.run`
- **API:** `POST /api/v1/gate/mirror`
- **Returns:** confusion_count, passed
- **Retry policy:** max_retries=2, backoff_s=5

### 4.4 Gate Perf (Benchmark)
- **Action:** `gate.perf.run`
- **API:** `POST /api/v1/gate/perf`
- **Returns:** passed, baseline_scores
- **Retry policy:** max_retries=1, backoff_s=10

### 4.5 Gate Human (Signoff)
- **Action:** `gate.human.sign`
- **API:** `POST /api/v1/gate/human`
- **Returns:** status, signed_by, signed_at
- **No retry:** human action required

### 4.6 Promotion
- **Action:** `promote.execute`
- **Entry:** `[[10_Operations/agents/promoter/promote.sh]]`
- **Validator:** `[[10_Operations/agents/promoter/validate_promotion.py]]`

---

## 5. Validation Invariants

| ID | Condition | Requirement |
|----|-----------|-------------|
| deploy.vault | subphase == writing_manifest | deploy_manifest.json exists AND valid |
| gate.mirror | subphase == mirror_smoke | confusion_count == 0 |
| gate.perf | subphase == perf_bench | perf-bench-results.json passed |
| gate.human | subphase == awaiting_signoff | human-signoff.md status == approved |
| gate.three | subphase == promoting_candidate | mirror AND perf AND human all passed |
| deploy.full | phase == completed | all three gate artifacts present AND promote.success |
| circuit | subphase == circuit_open | retry_backoff.active AND graceful_degradation.active |
| recovery | subphase == rolling_back | ledger_backup.exists AND events_log.consistent |
| promotion | promoting_candidate | rejected_nodes == 0 AND shadow_bridges == 0 |

---

## 6. Confusion Signals

- Vault deployed but deploy_manifest.json missing
- gate.mirror passed but gate.perf not triggered
- gate.human signed off before gate.perf run
- Circuit breaker stuck in open without recovery
- Retry loop exceeds max_retries without escalation
- Graceful degradation active but fallback_mode undefined
- Worker crash reassignment orphans work units
- Dual-ledger snapshot shows checksum mismatch after recovery
- Promote executes before three gates pass
- Linter violation blocks but auto_fix not attempted

---

## 7. Dependencies

This document depends on:
- **WU-011** (`[[ui/vault-ui-intent-map]]`) — provides the deploy_path, resilience, and disaster_recovery sections that this document validates against
- **WU-013** (governance files) — provides the convergence thresholds and ADR-002 binding that gate validation checks

Cross-references updated per handoff TX-HT-8A5C0E.
Wikilink targets verified: `[[ui/vault-ui-intent-map]]` resolves to `ui/vault-ui-intent-map.json`,
`[[10_Operations/agents/promoter/promote.sh]]` resolves to `promote.sh`,
`[[10_Operations/agents/promoter/validate_promotion.py]]` resolves to `validate_promotion.py`.
