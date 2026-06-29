# Gaijinn Innovation & Interface-Contract Mapping

This document provides complete traceability for the proprietary innovations implemented in the Gaijinn multi-agent orchestration engine.

## 1. Aggregate SSE Transaction Manifold
- **Requirement:** High-bandwidth, zero-leak multiplexed streaming of concurrent worker logs and council events into a single terminal dashboard.
- **Implementing Module:** `aoc_supervisor/aoc_supervisor/api.py`
- **Key Function:** `sprint_aggregate_stream`, `SprintBroadcaster`, `_read_stream`
- **Input Contract:** `sprint_id` (path), `Last-Event-ID` (header).
- **Output Contract:** SSE stream emitting JSON-encoded worker logs and promoted council transactions.
- **Emitted Event:** `event: log`, `event: council_transaction`
- **Test Proving Behavior:** `tests/test_innovation_verification.py::test_ring_buffer_pruning_and_replay`
- **Acceptance Evidence:** Terminal UI routes multiplexed logs to correct worker cells via `connectAggregateStream`.
- **Failure Behavior:** Missing/pruned `Last-Event-ID` triggers automatic fallback to streaming the entire active ring buffer.

## 2. Bounded Event Retention (Ring Buffer)
- **Requirement:** Buffer management to support UI reconnection while bounding heap allocation during high-velocity log bursts.
- **Implementing Module:** `aoc_supervisor/aoc_supervisor/api.py`
- **Key Class:** `SprintBroadcaster`
- **Contract:** `capacity=1000` (default), `ring_buffer` (sliding list).
- **Associated Test:** `tests/test_innovation_verification.py::test_high_velocity_burst_resilience`
- **Invariant:** Heap allocation for log events is bounded by `capacity`; oldest events are discarded first.

## 3. SCC-Aware Geometric Partitioning
- **Requirement:** Prevent "Cascading Convex Hull Over-Welding" by capping parallel group sizes while preserving unbreakable circular dependencies.
- **Implementing Module:** `aoc-cli/aoc_cli/blueprint.py`
- **Key Function:** `_refine_grouped_blocks`
- **Algorithm:** Strongly Connected Component (SCC) detection via `networkx`.
- **Contract:** `GAIJINN_CONVEX_HULL_THRESHOLD` (default 12). Cycles are never sliced across workers.
- **Associated Test:** `tests/test_innovation_verification.py::test_scc_deterministic_containment`
- **Failure Behavior:** If an SCC exceeds the threshold, it is kept unified rather than sliced, preserving deterministic containment.

## 4. Council-Transaction Promotion
- **Requirement:** Automatic promotion of structured handoff transactions from raw text streams to first-class orchestration events.
- **Implementing Module:** `aoc_supervisor/aoc_supervisor/api.py`
- **Key Function:** `_read_stream`
- **Contract:** Any line containing `TX-HT-` is emitted as `event: council_transaction`.
- **Associated Test:** `tests/test_innovation_verification.py::test_sprint_council_event_promotion`
- **Acceptance Evidence:** Terminal UI flashes the layout chip and logs a system message on transaction detection.

## 5. Async Subprocess Transaction Piping
- **Requirement:** Zero-latency streaming from real git worktree subprocesses into the async broadcaster.
- **Implementing Module:** `aoc_supervisor/aoc_supervisor/api.py`
- **Key Function:** `grid_spawn` refactor to `asyncio.create_subprocess_exec`.
- **Contract:** `stdout/stderr` redirected to `asyncio.subprocess.PIPE`.
- **Associated Test:** `tests/test_e2e_golden_path.py` (verified via manual CLI acceptance).
