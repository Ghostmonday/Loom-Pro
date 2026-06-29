# Sandbox Frontend — Engineering Reference

> **Context:** The `ui/` directory (legacy brutalism-style implementation) has been deleted and replaced by `sandbox_frontend/` (glass-morphism Tailwind CSS implementation). This document captures valuable architectural patterns from both for future reference.

---

## 1. Layout Architecture (Sandbox Frontend)

Every page follows a consistent three-zone layout:

```
┌──────────────────────────────────────────────────┐
│  TopNavBar (fixed, h-16, z-50)                   │
│  [Brand] [Nav Links]        [Search] [Settings]  │
├──────┬───────────────────────────────────────────┤
│Side  │  Main Content Area                        │
│Nav   │  (overflow-y-auto, custom-scrollbar)      │
│Bar   │                                           │
│64px  │                                           │
│      │                                           │
└──────┴───────────────────────────────────────────┘
```

**Pattern:**
- `header` fixed top, `h-16`, `z-50`, `bg-surface/80 backdrop-blur-xl border-b`
- `aside` left rail, `w-[64px]`, `flex flex-col items-center`, `bg-surface-container-low/80 backdrop-blur-xl border-r`
- `main` flex-1, `overflow-y-auto`, custom thin scrollbar
- Wrapper `div.flex.flex-1.pt-16.overflow-hidden` accounts for fixed header

---

## 2. Design System (Sandbox Frontend)

### 2.1 Stack
| Technology | Usage |
|---|---|
| **Tailwind CSS** (CDN) | Utility classes with `plugins=forms,container-queries` |
| **Geist** (Google Fonts) | Primary sans-serif font (100–900 weight) |
| **JetBrains Mono** (CDN) | Monospace code font |
| **Material Symbols** (Google) | Icon set via `material-symbols-outlined` class |

### 2.2 Glass-morphism Pattern
```css
.glass-panel {
    background: rgba(28, 28, 30, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 0.5px solid rgba(255, 255, 255, 0.1);
}
.glass-card {
    background: rgba(44, 44, 46, 0.4);
    backdrop-filter: blur(30px);
    border: 0.5px solid rgba(255, 255, 255, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-card:hover {
    background: rgba(44, 44, 46, 0.6);
    border-color: rgba(170, 199, 255, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}
```

### 2.3 Design Tokens (Tailwind Config Inline)
Each page embeds a `<script id="tailwind-config">` with:
- **Colors:** Material Design 3-inspired dark theme palette (surface, primary=#aac7ff, secondary=#47e266, tertiary=#ffb868, error=#ffb4ab, background=#131315)
- **Spacing:** semantic tokens — `stack-sm: 4px`, `stack-md: 8px`, `stack-lg: 16px`, `gutter: 16px`, `container-margin: 24px`, `panel-padding: 12px`
- **Font sizes with line-height/letter-spacing/weight:** `display-lg: [48px, ...]`, `headline-lg: [32px, ...]`, `title-md: [20px, ...]`, `body-lg: [16px, ...]`, `body-sm: [14px, ...]`, `label-caps: [12px, ...]`, `mono-precision: [13px, ...]`
- **Font families:** `label-caps`, `headline-lg`, `body-sm`, `display-lg`, `body-lg`, `title-md`, `mono-precision`
- **Border radius:** `lg: 12px`, `xl: 16px`, `full: 9999px`

### 2.4 Scrollbar Customization
```css
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
```

### 2.5 Interaction Patterns
- `active:scale-95` / `active:scale-90` on buttons for press feedback
- `hover:bg-surface-container-high` for item hover states
- `.spring-transition` with `cubic-bezier(0.175, 0.885, 0.32, 1.275)` for bouncy animations
- `.hover-lift:hover { transform: translateY(-1px); background: rgba(255,255,255,0.08); }`
- `group-hover:` patterns for reveal-on-hover elements (e.g., chevron arrows)

---

## 3. Navigation Patterns

### 3.1 TopNavBar (fixed)
```
[Brand Name] [Nav Link 1] [Nav Link 2] [Active Link]  |  [Search] [Settings] [Avatar]
```
- Active link: `text-primary font-bold border-b-2 border-primary`
- Inactive: `text-on-surface-variant font-medium hover:text-primary`
- Breadcrumb trail: `Ingest > Models > Curvature Analysis` with `chevron_right` separators

### 3.2 SideNavBar (left rail, 64px)
Vertical stack of icon buttons. Active tool gets `bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)]`.

Icons used across pages: `near_me`, `straighten`, `architecture`, `layers`, `visibility`, `terminal`, `input`

### 3.3 No Router — All Pages are Standalone HTML
Each `.html` file is fully self-contained. Navigation uses `<a href="#">` or direct links between pages. No SPA framework.

---

## 4. Page Inventory (sandbox_frontend/)

| Page | File | Purpose |
|---|---|---|
| Hub | `index.html` | Project dashboard, recent projects, quick actions |
| Blueprint Ratification | `blueprint-ratification.html` | Modularity optimization, Q plateau, ratification thresholds |
| Claims Ledger | `claims-ledger.html` | Atomic architectural evidence → verified structural claims |
| Curvature Analysis | `curvature-analysis.html` | Bimodal curvature distribution, Ollivier-Ricci metrics |
| Drift Monitor | `drift-monitor.html` | Delta-Kappa drift tracking, SVG animation |
| Packet Export | `packet-export.html` | Work unit export, data packet controls |
| Topological Observatory | `topological-observatory.html` | Full graph visualization, node inspection |

### 4.1 Markdown Specs
Each `.html` has a sibling `.md` with identical content — these serve as documentation/specification mirrors.

---

## 5. Legacy `ui/` Patterns (Preserved for Reference)

### 5.1 Brutalist Design Language
```css
body { font-family: "SF Mono","Fira Code","Cascadia Code",Consolas,monospace;
       background: #000; color: #fff; }
.panel { border: 2px solid #222; background: #000; }
button { border: 2px solid #222; background: #000; color: #fff; 
         text-transform: uppercase; letter-spacing: 0.03em; }
button:hover { background: #fff; color: #000; }
```
- No border-radius, no shadows, pure monochrome
- `border-left: 6px solid #66bb6a` for status indicators
- Data attributes for state: `[data-active="true"]`, `[data-can-handoff="true"]`

### 5.2 State Management Pattern (intent-forge.js)
Single global state object:
```javascript
const state = {
    sessionId: "",
    blueprintVersion: 0,
    currentQuestionId: "",
    userId: "",
    readinessScore: 0,
    readinessCanHandoff: false,
    handoffConfirmed: false,
    sessionStatus: "",
};
```
State mutations directly update DOM via `byId()` getter pattern.

### 5.3 API Wiring Pattern
```javascript
const API_PREFIX = "/api/v1/intent-forge";
function headers() {
    return { "Content-Type": "application/json", "X-User-Id": state.userId || DEFAULT_USER_ID };
}
function sessionUrl(sid) { return API_PREFIX + "/sessions/" + encodeURIComponent(sid); }
function idempotencyKey(action) {
    return action + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}
async function requestJson(url, options) {
    const r = await fetch(url, options);
    const d = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error(d.detail || d.error || r.status + " " + r.statusText);
    return d;
}
```

### 5.4 WebSocket Telemetry Client (command-engine.js)
```javascript
function TelemetryClient() {
    this.ws = null;
    this.reconnectAttempt = 0;
    this.reconnectTimer = null;
    this.intentionalClose = false;
    this.handlers = {};
}
TelemetryClient.prototype.connect = function (sessionId, mode) { /* ... */ };
TelemetryClient.prototype._open = function () { /* WebSocket + reconnect */ };
TelemetryClient.prototype._handleMessage = function (raw) { /* JSON parse + event dispatch */ };
TelemetryClient.prototype._scheduleReconnect = function () {
    const delay = Math.min(RECONNECT_BASE_MS * Math.pow(2, this.reconnectAttempt), RECONNECT_MAX_MS);
};
```
- Exponential backoff reconnect (1s → 30s)
- Event type routing: `session.snapshot`, `topology.*`, `work_unit.*`, `handoff.*`, `phase.*`
- Handoff ticket marker detection: `++++ GAIJINN_HANDOFF_TICKET_START ++++`

### 5.5 Dynamic CSS Injection
```javascript
(function injectBrutalistStyles() {
    if (document.getElementById("loom-if-brutalist")) return;
    var s = document.createElement("style");
    s.id = "loom-if-brutalist";
    s.textContent = ["body{...}", ...].join("\n");
    document.head.appendChild(s);
})();
```
Pattern: inject stylesheet only once, check by ID. Used to override external CSS.

### 5.6 Intent Map Contract System
The most architecturally valuable pattern from `ui/`:
- **Intent maps** are JSON files that define the complete UI contract: elements (DOM IDs, types), flows (actions → API), states, invariants
- **Surface hierarchy:** `loom-system-intent-map.json` → child maps per surface
- Each action has: `api` endpoint, `algorithm_binding` (module + entrypoint), `postconditions`
- Elements specify: `dom_id`, `type` (textarea, button, panel, region, metric, gate), `triggers`
- Enables headless mirror tests via `UiIntentDriver`

### 5.7 Terminal Log Viewer (terminal.js)
- Ring buffer (MAX_BUFFER = 2000, MAX_DOM_LINES = 500)
- DOM-based rendering with color-coded levels (info=white, warn=yellow, error=red, debug=gray)
- Auto-scroll with scroll-to-bottom button
- Handoff ticket parsing from log lines
- `window.dispatchEvent(new CustomEvent("loom:handoff-ticket", { detail: ticket }))` for event bus

### 5.8 SVG Topology Rendering (command-engine.js)
- Force-directed layout with configurable constants (REST_LENGTH=160, REPULSION=8000, SPRING=0.04, DAMPING=0.6)
- Dark bridge edges: dashed red `stroke-dasharray: 4,3`
- Active lanes: pulsing white stroke with CSS animation
- Weld blocks: thick dashed outlines
- Hover tooltips with absolute positioning

### 5.9 Stage Rail Workflow Progression
Converts session state into visual stage indicators:
```javascript
const STAGES = [
    { key: "scanning",     label: "Scanning" },
    { key: "preflight",    label: "Preflight Geometry" },
    { key: "spawning",     label: "Grid Spawning" },
    { key: "verification", label: "Integration Verification" },
];
```
- Past stages: `.completed` (green)
- Current stage: `.active` (white/highlighted)
- Future stages: default dim
- Status mapping: `questioning`/`scanning` → index 0, `preflight_geometry` → 1, etc.

---

## 6. Build & Dev Configuration

### 6.1 No Build Step (Both Implementations)
Both old and new frontends are zero-build — pure HTML/CSS/JS served directly. No bundler, no npm.

### 6.2 CDN Dependencies (Sandbox Frontend)
```html
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:...&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap" rel="stylesheet"/>
```

### 6.3 Dev Server
```bash
.venv/bin/uvicorn aoc_supervisor.api:app --reload --port 8080
# Frontend served from sandbox_frontend/ via static mount
```

---

## 7. Migration Notes (ui/ → sandbox_frontend/)

| Pattern | Old (`ui/`) | New (`sandbox_frontend/`) |
|---|---|---|
| Design | Brutalist monochrome, pure CSS | Glass-morphism, Tailwind CSS |
| Icons | Text/Unicode | Material Symbols |
| Font | SF Mono / monospace | Geist + JetBrains Mono |
| State | Global JS object | Not yet implemented |
| API calls | Centralized `requestJson()` helper | Not yet implemented |
| WebSocket | Full `TelemetryClient` class | Not yet implemented |
| Layout | Full-screen grid | Fixed header + sidebar |
| Files | `.html` + `.js` + `.css` per view | Single `.html` per view (all inline) |
| Contracts | JSON intent maps | Not yet implemented |

The new sandbox_frontend has the visual design but is missing: API wiring, WebSocket telemetry, state management, intent map contract compliance, and dynamic content rendering. These need to be ported from the `ui/` implementation patterns (Sections 5.2–5.9).
