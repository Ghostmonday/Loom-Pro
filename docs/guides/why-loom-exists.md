# Why Loom Exists

Modern AI-assisted software engineering has moved beyond single-file autocomplete toward multi-agent systems executing parallel development plans. While parallel execution holds the promise of faster delivery, it introduces three fundamental engineering problems:

1. **Shared Context Degradation**: As the number of parallel workers increases, the implicit context needed to prevent overlap degrades. Without a unified model, agents make disjoint assumptions about shared state and APIs.
2. **Implicit vs. Explicit Intent**: Standard code representations (ASTs, import DAGs) do not capture high-level architectural intent. They only show how the code is currently wired, not *why* it was designed that way or what constraints must govern changes.
3. **Post-Hoc Verification vs. Runtime Constraints**: Most safety and compliance tools validate outputs *after* generation. When an agent breaks an invariant or writes to unauthorized files, the compute is wasted and manual code review becomes a bottleneck.

Loom provides a structural framework to address these issues by making intent, authority, and validation explicit, machine-readable contracts.

---

## 1. The Context Bottleneck in Parallel Development

When multiple agents work on different modules in a codebase, import references suggest independence. However, files are frequently coupled through hidden data paths (shared schemas, IPC, environment state). 

Loom analyzes graph curvature to identify these bottlenecks. If two subgraphs are functionally coupled below a safety threshold (κ < -0.3), they are welded into a single work unit. This prevents independent agents from working on tightly coupled regions simultaneously, eliminating merge conflicts and contradictory assumptions.

## 2. Enforcing Invariants via Intent Mapping

To scale development, we must enforce path and command boundaries *before* execution. 

Loom compiles natural-language intent into an **Agent Intent Vector (GIV)**. The GIV acts as a runtime contract defining:
- Write permissions (allowed paths)
- Prohibited scopes (denied paths)
- Executable commands (blocking operations like `git push`)
- Behavioral invariants

By injecting these constraints directly into agent environments, we bound the agent's action space at compile time.

## 3. Strict Deterministic Validation

Rather than relying on probabilistic review, Loom implements a deterministic merge-integrity harness. 

After parallel execution, each agent cell is audited against its GIV. If an agent wrote outside its allowed path (trespass) or executed a forbidden command (violation), the transaction is blocked. Only compliant transactions are welded into the main branch. 

This strict boundary checking ensures that the system reports convergence based on verified modifications, keeping the repository state mathematically sound.
