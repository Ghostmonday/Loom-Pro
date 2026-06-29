# Patent figures — Mermaid (canonical numerals)

**Inventor:** Amir Khodabakhsh · California, US  
**Terminology:** GIV = Agent Intent Vector (not "Grit")  
**Supersedes:** `~/Desktop/patentvisuals.jpeg` (Grit typo)

Reference numerals match `USPTO-PATENT-APPLICATION-DRAFT.md`.

---

## FIG. 1 — Deployment loop (100–124)

```mermaid
flowchart TB
  subgraph SYS100["System 100"]
    TC100["Target Codebase 100"]
    IS102["Intake Scanner 102"]
    IG104["Interaction Graph G=(V,E) 104"]
    L1105["Layer-1 Intent Nodes 105"]
    CE106["Geometric Curvature Engine 106"]
    BP108["Blueprint Planner 108"]
    GIV112["GIV Permission Envelope 112"]
    GW114["Git Worktree Sandbox 114"]
    FS116["Filesystem Copy Sandbox 116"]
    OLP118["Output Log Parsing 118"]
    MIH122["Merge Integrity Harness 122"]
    PG124["Upstream Preflight Gate 124"]
  end
  TC100 --> IS102 --> IG104
  IG104 --> CE106
  IG104 --> L1105
  CE106 --> BP108 --> GIV112
  GIV112 --> GW114
  GIV112 --> FS116
  GW114 --> OLP118
  FS116 --> OLP118
  OLP118 --> MIH122 --> PG124
```

---

## FIG. 2 — Curvature pipeline (200–213)

```mermaid
flowchart LR
  E200["Edge u→v Selector 200"] --> ND202["Neighborhood Distributions 202"]
  ND202 --> CM204["Cost Matrix 204"]
  CM204 --> BG206["Bidirectional Gravity 206"]
  BG206 --> W208["Wasserstein EMD 208"]
  W208 --> CV210["Curvature κ Evaluator 210"]
  CV210 --> RJ212["Risk-Jump Classifier 212"]
  CV210 --> HF213["Gravity Hard Floor 213"]
  CV210 --> BP106["→ Blueprint Planner 106"]
```

---

## FIG. 3 — Legacy weld vs gateway mode (300–312)

```mermaid
flowchart TB
  subgraph LEG["Legacy Mode 300"]
    UF301["Union-Find Cluster 301"]
    AW304["Atomic Single-Worker Block 304"]
    UF301 --> AW304
  end
  subgraph GW["Gateway Mode 306"]
    HO308["HANDOFF_ONLY Gateway Edge 308"]
    NOW306["Non-Overlapping Work Units 306"]
    PEM312["Parallel Efficiency Matrix 312"]
    HO308 --> NOW306 --> PEM312
  end
  DB302["Dark Bridge κ≤−0.30 302"] --> LEG
  DB302 --> GW
```

---

## FIG. 4 — GIV permission envelope (400–416)

```mermaid
flowchart LR
  subgraph GIV112["GIV Permission Envelope 112"]
    W400["worker_id 400"]
    AP402["allowed_paths 402"]
    DP403["denied_paths 403"]
    SDP405["sibling_denied_paths 405"]
    DC406["denied_commands 406"]
    ST408["structural_tokens 408"]
    INV410["invariants 410"]
  end
  GIV112 --> ISO414["Isolation Substrate 414"]
  ISO414 --> TC602["Trespass Classifier 602"]
```

---

## FIG. 5 — Transaction bus (500–510)

```mermaid
flowchart LR
  AG500["Agent Workspace 500"] --> TK502["Handoff Ticket 502"]
  TK502 --> SH504["Scaffold Hardening Filter 504"]
  SH504 --> CR506["Council Ledger 506"]
  CR506 --> RC508["Transaction Receipt 508"]
  RC508 --> SY510["Bus Sync Check 510"]
```

---

## FIG. 6 — Merge pipeline (600–610)

```mermaid
flowchart LR
  WD600["Worker Deltas 600"] --> TC602["GIV Trespass Classifier 602"]
  TC602 --> VW604["Validate-Worker Gates 604"]
  VW604 --> MG606["Merge-Grid Topological Sort 606"]
  MG606 --> AM608["Already-Merged 608"]
  AM608 --> HC610["Honest Convergence 610"]
```

---

## FIGS. 7–13 (summary)

| Fig | Mermaid anchor | Key numerals |
|-----|----------------|--------------|
| 7 | Supervisor | 700 metrics → 704 GIV gate → 708 circuit breaker |
| 8 | Extraction | 800 repo → 802 modality → 810 graph state |
| 9 | Topology | 900 typed node → 906 overlap → 908 reject |
| 10 | Gravity | 1000 score → 1002 floor → 1008 preflight GIV block |
| 11 | Federated | 1100 vault A/B → 1108 cross-system TX → 1110 validator |
| 12 | ORI | 1200 resource → 1204 read tracker → 1208 commit reject |
| 13 | Constraints | 1300 invariants → 1304 envelope → 1310 preflight reject |

Full SVG filing visuals: `figures/fig01-deployment-loop.svg`, `figures/fig04-giv-envelope.svg`, `figures/patent-figures-sheet.svg`.