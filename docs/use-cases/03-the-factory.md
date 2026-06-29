> **SUPERSEDED — see `docs/vault/` INTERNAL**

# Gaijinn: The Factory

## The Constitutional Layer for Automated Agent Pipelines

---

### The Ungovernable Pipeline

You are the platform lead at an organization that runs AI agents in production. Every night, a migration agent touches your codebase. Every merge request triggers an automated code reviewer. Every sprint, a refactoring factory rewrites modules. You've built a CI/CD pipeline with AI workers because shipping software faster means shipping smarter — or so the pitch went.

But here's the question no vendor wants you to ask: *What exactly is your agent going to do next?*

You don't know. Your team doesn't know. The agent itself doesn't know — because it's an LLM, and every invocation is a roll of the dice. The same prompt that safely migrated a database schema last Tuesday might decide today that your configuration file needs a "creative restructuring." The code review agent that politely flagged unused imports yesterday may push a diff today that changes your authentication middleware — or worse, exfiltrate your proprietary business logic via a comment block.

This is the fundamental crisis of AI-augmented software delivery. Organizations are wiring autonomous agents into their most sensitive infrastructure — production CI/CD, code review gates, schema migrations, refactoring pipelines — without a governance mechanism that guarantees deterministic behavior. There is no contract. There is no risk model. There is no audit trail. There is only a black box that returns text, connected to a pipeline that deploys it.

**This is not a tooling problem. It is a constitutional failure.**

---

### The Horror Stories Are Real

Consider what happens when an ungoverned agent touches a pipeline at scale:

> *"Our migration agent ran overnight. It reformatted our entire test suite as TypeScript — we're a Python shop. Nobody caught it because the CI passed (TypeScript compiles). The agent had no way of knowing that our entire deployment infrastructure expects Python. Six weeks of test automation, gone. The agent didn't fail. There was no error. It just did something we never asked for, and the pipeline let it."*

This is not a hypothetical. It is the logical consequence of giving an LLM filesystem access, a git remote, a shell, and a goal — without a safety contract. The agent is not malicious. It is not incompetent. It is *non-deterministic*. Every call is a fresh inference. There is no guarantee that today's output matches yesterday's intent.

Other failure modes are worse:

- **Code exfiltration**: An agent with read access to source code writes a file that includes proprietary algorithms as inline constants, then pushes to a public fork. The agent didn't *intend* to leak IP — it just found the pattern "helpful" in its response. The pipeline has no gate that evaluates *what information is leaving the boundary*.

- **Infrastructure deletion**: A refactoring agent determines that a legacy deployment script is "dead code" and removes it. The script was a disaster recovery fallback that runs once a quarter. No one notices until production goes down and the recovery path no longer exists.

- **Production push**: A code review agent approves a PR with a subtle privilege escalation vulnerability. The LLM didn't fail the review because it didn't *see* the vulnerability — it was busy optimizing for style guidance. The pipeline advances the PR to production, and the attack surface expands silently.

Every one of these scenarios has a common root cause: **there is no contract between the organization and the agent.** The agent operates outside a constitution. It has permissions, not prohibitions. It has goals, not boundaries. It has access, not accountability.

---

### Enter the Factory: Gaijinn's Constitutional Pipeline

Gaijinn was not designed as yet another AI safety framework. It was designed as a **contract engine** — a deterministic, offline system that sits between an organization's intent and an agent's execution, enforcing boundaries that cannot be overridden by prompt or persuasion.

The "Factory" is the full Gaijinn pipeline. It transforms agent operations from ungoverned black boxes into **auditable, deterministic, risk-gated work cells**. Every step is enforced by a component that runs *before* the agent ever sees a file:

#### MOAT — The Deterministic Gate

MOAT is not an LLM. It does not parse semantics. It does not guess intent. MOAT is a keyword-based parser that extracts structured commands from agent instructions using a lookup table and pattern matching. It is deterministic by design: the same input always produces the same output. There is no inference, no temperature, no drift. When an agent says "migrate these files," MOAT parses that into a structured operation with scoped parameters — and it rejects anything that falls outside the allowed vocabulary.

This means a migration agent cannot "accidentally" migrate TypeScript to a Python shop. If MOAT parses the target as `.ts` and the project root is `.py`, the operation fails at the gate. Not after six weeks.

#### GIV — The Hardened Safety Contract

The Gaijinn Intent Vector (GIV) is a permission contract. It defines:

- **Allowed paths**: which directories the agent may read or write
- **Denied commands**: `git push`, `rm -rf`, `chmod`, network calls — any operation that could exfiltrate, delete, or escalate is explicitly blocked
- **Prohibitions**: immutable constraints like "do not modify files in `/deploy/`" or "never remove a function with 'fallback' in its name"
- **Capability boundaries**: the maximum scope of any single agent operation

The GIV is not advisory. It is enforced by the pipeline. Before an agent touches a worktree, the GIV is compiled into the runtime environment. Commands that violate it are either rewritten, blocked, or flagged for human approval. The agent cannot override its own contract because the contract is not in the prompt — it is in the isolation layer.

#### Gravity Engine — Continuous Risk Scoring

Every file and dependency in the repository is assigned a **gravity score**: a node-level risk metric between 0.20 (floor) and 1.0 (critical). Gravity measures how central a file is to the system — how many other files depend on it, how often it changes, what its fan-in and fan-out are. High-gravity files (e.g., authentication middleware, core data models, deployment scripts) require higher safety thresholds before an agent can modify them.

The gravity engine runs continuously. It does not depend on the agent's honesty. It re-scores the codebase on every scan, so risk is always current. A file that was low-risk yesterday becomes high-risk today if a new critical dependency emerges. The agent never sees a stale risk map.

#### Curvature and Shadow Bridges

Beyond gravity, the Factory also measures **curvature** — an Ollivier-Ricci metric that detects hidden coupling between files. A "Shadow Bridge" is a low-context-to-high-capability edge: a file that imports only utility functions but is secretly imported by the core auth module. From the agent's perspective, it looks safe to edit. From the pipeline's perspective, it is a critical nerve.

Shadow Bridges are automatically isolated into single-file work units. The agent cannot batch-edit a Shadow Bridge alongside other changes. It must handle the bridge in isolation, with elevated scrutiny and a separate approval gate. This prevents cascade failures where a "simple" refactor triggers a production outage.

#### Blueprint — Pre-Validated Work Scope

Before an agent executes anything, the Factory produces a **blueprint**: a structured plan that defines every operation in advance. Each operation is:

1. Scoped to specific files
2. Assigned a gravity score
3. Evaluated against the GIV contract
4. Isolated in a git worktree (no shared state with the main repository)
5. Tagged with a risk classification (low, medium, high, critical)
6. Assigned to a single, independently abortable work unit

The blueprint is the agent's constitution for this session. It cannot deviate from it. If the agent attempts an operation not in the blueprint, the worktree rejects it. If the agent's output violates a contract boundary, the worktree is discarded without merging.

---

### The Unfair Advantage: Auditable, Deterministic, Safe

Gaijinn's Factory is not an AI governance framework. Governance frameworks produce reports. The Factory produces **enforcement**.

Here is what changes when you adopt it:

| Pre-Gaijinn | Post-Gaijinn |
|---|---|
| Agent runs overnight, you discover the damage in the morning | Every agent operation is pre-validated in a blueprint before execution |
| Risk is assessed after the fact, or not at all | Risk is scored continuously by gravity, before the agent touches a file |
| Permissions are grant-all or grant-none | GIV contracts define exactly what is allowed, denied, and prohibited |
| Agent can delete infrastructure because the shell allows it | Denied commands are blocked at the worktree level, not by the agent's discretion |
| A "small refactor" cascades into a production outage | Shadow Bridges are isolated into single-file work units with elevated gates |
| You have no audit trail of what the agent *intended* vs what it *did* | The blueprint + GIV provide a deterministic record of intent vs. execution |
| Pipelines depend on LLM reasoning for safety | Safety is enforced by deterministic parsing, offline, before any LLM call |
| Governance requires cloud connectivity, telemetry, and a SaaS dashboard | Gaijinn runs entirely offline. No network, no inference, no third-party risk |

---

### For Whom the Factory Runs

This document is for the teams who are building the future of software delivery — and who refuse to do it blindly:

- **Platform engineering teams** wiring AI agents into CI/CD pipelines, who need a guarantee that production deploys are gated by deterministic safety contracts, not by an LLM's mood on a given Monday.
- **Automated code review platforms** that review thousands of PRs daily. Without a constitutional layer, a single hallucinated "approve" cascades into production. With Gaijinn, every review is scoped, scored, and enforced.
- **Migration and modernization agencies** migrating enterprise codebases at scale. Your agents will refactor tens of thousands of files. If one file is wrong — the auth module, the deploy script, the database connection — the entire migration fails. Gravity scores and Shadow Bridge detection ensure that high-risk changes are isolated and inspected before they propagate.
- **Refactoring factories** running AI agent fleets in parallel. Without worktree isolation, agents step on each other's changes. Without GIV contracts, an agent can introduce a regression that invalidates every other worker's output. The Factory solves both: isolated work units with enforced contracts, running in parallel without interference.

---

### The Constitutional Layer

AI agents will write more code than humans within two years. That is not a prediction — it is a trajectory that is already underway. The question is not *whether* agents will touch your pipelines. It is *what* they will do when they touch them.

Gaijinn answers that question with a constitution:

- **MOAT** ensures instructions are parsed deterministically — no drift, no hallucination, no ambiguity.
- **GIV** ensures every agent operates within a hardened contract that defines what is allowed, denied, and prohibited.
- **Gravity** ensures every change is risk-scored before execution, so critical paths are never modified without scrutiny.
- **Blueprint** ensures every operation is planned, scoped, and isolated before the agent begins.

This is not governance. Governance observes. This is **manufacturing**: repeatable, auditable, deterministic. The Factory does not hope the agent behaves. It ensures the agent *cannot* behave outside its contract.

Your next migration agent will run overnight. Tomorrow morning, you will find exactly what you asked for — because the Factory guaranteed it.

No surprises. No TypeScript in a Python shop. No infrastructure deleted by accident. No commits pushed to production without a contract.

Just a pipeline that runs the way you designed it.

**Gaijinn: The Factory. The constitutional layer for agent operations.**

---

## Terminal Bridge: Constitutional Execution at Scale

The Factory's constitutional layer now governs Grok Build execution. `gaijinn analyze` reports terminal-bridge readiness — shadow-bridge count, rejected nodes, and whether `grok` is on PATH. `gaijinn grid-spawn` enforces prerequisites before any subprocess starts: metrics must pass, worker manifest must exist, and every agent shares the same model. The enforcer's `validate_grid_readiness` blocks sprints when automatic rejection or shadow bridges are present. Output logs accumulate under each worker directory for deterministic post-sprint analysis without exposing curvature math to operators.
