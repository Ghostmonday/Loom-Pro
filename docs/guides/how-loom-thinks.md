# How Loom Thinks

Loom processes codebase changes systematically, transforming natural-language intent and static files into isolated execution boundaries. This guide walks through how Loom reasons about a software project from start to finish.

---

## The End-to-End Execution Flow

```
Open Project
     ↓
Extract AST
     ↓
Build FRG
     ↓
Infer Topology
     ↓
Generate Intent
     ↓
Measure Curvature
     ↓
Generate Contracts
     ↓
Spawn Work
     ↓
Validate
     ↓
Ratify
```

---

### Step 1: Open Project
Loom is initialized inside a target repository (greenfield or brownfield). It identifies the repository roots, Git configurations, and checks for existing files.

### Step 2: Extract AST (Abstract Syntax Tree)
Loom parses the codebase statically using Python AST parsing (Abstract Syntax Tree). It extracts files, classes, methods, and their import paths without executing any code.

### Step 3: Build FRG (Function-Realization Graph)
The extracted AST components are mapped to a Function-Realization Graph (FRG). Nodes represent files or execution entry points, and edges represent direct imports, method references, and function calls.

### Step 4: Infer Topology
Loom analyzes the structure of the FRG to infer the overall architecture. It identifies high-degree hub nodes, execution boundaries, and domain boundaries (e.g. distinguishing backend paths from tests).

### Step 5: Generate Intent
Loom takes the high-level intent vector (Layer 0, provided via prompt or onboarding intake) and parses it to extract domain rules, required file scopes, and command permissions.

### Step 6: Measure Curvature
Loom computes Ollivier-Ricci curvature on every edge of the topology using optimal transport. It calculates edge curvature (κ):
- Edges with κ < -0.3 indicate critical bottlenecks (**Dark Bridges**).
- Edges with κ ≥ 0 indicate safe parallel boundaries.

### Step 7: Generate Contracts
Based on curvature welds, Loom generates isolated work units. It produces the **Agent Intent Vector (GIV)** for each unit, setting allowed write paths, prohibited paths, and command filters.

### Step 8: Spawn Work
Lrok/Grok agent cells are spawned in isolated directories (Git worktrees or codebase copies) with their respective GIV contracts injected. Agents run in parallel to execute their assigned scopes.

### Step 9: Validate
Once execution completes, the merge integrity harness checks all modified files. It deterministically checks if any worker violated its GIV (e.g., writing to denied paths or executing blocked commands).

### Step 10: Ratify
The validated results are merged into the repository. The final convergence score and validation metrics are logged, and the changes are ratified in the project history.
