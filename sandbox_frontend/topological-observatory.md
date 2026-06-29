<!-- Loom Blueprint Workbench - Topological Observatory -->
<!DOCTYPE html>
<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Loom Blueprint Workbench | Topological Observatory</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
      tailwind.config = {
        darkMode: "class",
        theme: {
          extend: {
            "colors": {
                    "inverse-surface": "#e4e2e4",
                    "tertiary": "#ffb868",
                    "inverse-on-surface": "#303032",
                    "on-secondary-fixed-variant": "#00531a",
                    "on-error": "#690005",
                    "surface-dim": "#131315",
                    "surface-container-low": "rgba(27, 27, 29, 0.7)",
                    "surface-tint": "#aac7ff",
                    "on-surface-variant": "#c0c6d6",
                    "on-secondary-fixed": "#002106",
                    "outline": "rgba(139, 145, 160, 0.3)",
                    "tertiary-fixed": "#ffddbb",
                    "secondary-fixed": "#6cff82",
                    "secondary-fixed-dim": "#47e266",
                    "on-primary-fixed": "#001b3e",
                    "on-tertiary-container": "#3f2300",
                    "error-container": "#93000a",
                    "on-tertiary-fixed": "#2b1700",
                    "on-tertiary": "#482900",
                    "surface-variant": "#353437",
                    "on-background": "#e4e2e4",
                    "tertiary-fixed-dim": "#ffb868",
                    "surface-bright": "#39393b",
                    "background": "#0b0b0d",
                    "primary-container": "#005db8",
                    "on-primary": "#003064",
                    "outline-variant": "rgba(65, 71, 84, 0.4)",
                    "secondary": "#47e266",
                    "primary-fixed": "#d6e3ff",
                    "surface-container-lowest": "#0b0b0d",
                    "on-error-container": "#ffdad6",
                    "on-secondary-container": "#004615",
                    "surface-container": "rgba(31, 31, 33, 0.6)",
                    "on-primary-container": "#d6e3ff",
                    "surface": "#131315",
                    "primary": "#aac7ff",
                    "surface-container-high": "rgba(42, 42, 44, 0.8)",
                    "on-surface": "#f2f2f7",
                    "secondary-container": "#09bf49",
                    "on-primary-fixed-variant": "#00468d",
                    "error": "#ffb4ab",
                    "tertiary-container": "#ce7f00",
                    "inverse-primary": "#005db8",
                    "surface-container-highest": "rgba(53, 52, 55, 0.9)",
                    "primary-fixed-dim": "#aac7ff",
                    "on-tertiary-fixed-variant": "#673d00",
                    "on-secondary": "#003910"
            },
            "borderRadius": {
                    "DEFAULT": "0.25rem",
                    "lg": "0.5rem",
                    "xl": "0.75rem",
                    "2xl": "12px",
                    "full": "9999px"
            },
            "spacing": {
                    "sidebar-width": "48px",
                    "inspector-width": "320px",
                    "gutter": "16px",
                    "stack-md": "8px",
                    "stack-lg": "16px",
                    "stack-sm": "4px",
                    "container-margin": "24px",
                    "panel-padding": "12px",
                    "unit": "8px",
                    "toolbar-height": "48px"
            },
            "fontFamily": {
                    "sans": ["Geist", "Inter", "system-ui", "sans-serif"],
                    "mono": ["JetBrains Mono", "monospace"]
            }
          },
        },
      }
    </script>
<style>
        body {
            background-color: #0b0b0d;
            color: #f2f2f7;
            margin: 0;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
            font-family: 'Geist', sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 20;
            font-size: 20px;
            transition: font-variation-settings 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-panel {
            background: rgba(31, 31, 33, 0.5);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glass-surface {
            background: rgba(19, 19, 21, 0.7);
            backdrop-filter: blur(30px) saturate(160%);
            -webkit-backdrop-filter: blur(30px) saturate(160%);
        }
        .custom-scrollbar::-webkit-scrollbar {
            width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        .node-pulse {
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 0 0 rgba(170, 199, 255, 0); }
            50% { opacity: .6; transform: scale(1.15); box-shadow: 0 0 15px 2px rgba(170, 199, 255, 0.4); }
        }
        .spring-transition {
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .hover-lift:hover {
            transform: translateY(-1px);
            background: rgba(255, 255, 255, 0.08);
        }
        .scanline {
            width: 100%;
            height: 1px;
            z-index: 10;
            background: linear-gradient(90deg, transparent 0%, rgba(170, 199, 255, 0.15) 50%, transparent 100%);
            position: absolute;
            top: -1px;
            pointer-events: none;
            animation: scan 6s linear infinite;
        }
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
    </style>
</head>
<body class="flex flex-col">
<!-- Global TopNavBar -->
<header class="fixed top-0 w-full h-[48px] glass-surface border-b border-outline-variant z-50 flex justify-between items-center px-4">
<div class="flex items-center gap-6">
<span class="font-bold text-[15px] tracking-tight text-on-surface flex items-center gap-2">
<span class="w-2.5 h-2.5 bg-primary rounded-[2px]"></span>
            LOOM BLUEPRINT
        </span>
<nav class="hidden md:flex items-center gap-1">
<a class="text-[13px] text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-lg px-3 py-1 spring-transition" href="#">Ingest</a>
<a class="text-[13px] text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-lg px-3 py-1 spring-transition" href="#">Forge</a>
<div class="relative">
<a class="text-[13px] text-on-surface font-semibold bg-white/10 rounded-lg px-3 py-1 spring-transition" href="#">Observatory</a>
<div class="absolute -bottom-[8px] left-1/2 -translate-x-1/2 w-1 h-1 bg-primary rounded-full"></div>
</div>
<a class="text-[13px] text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-lg px-3 py-1 spring-transition" href="#">Engine</a>
<a class="text-[13px] text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-lg px-3 py-1 spring-transition" href="#">Sanctuary</a>
<a class="text-[13px] text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-lg px-3 py-1 spring-transition" href="#">Cockpit</a>
</nav>
</div>
<div class="flex items-center gap-3">
<div class="relative hidden sm:block">
<span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[14px] text-on-surface-variant opacity-50">search</span>
<input class="bg-white/5 border border-white/10 rounded-lg text-[12px] pl-8 pr-3 py-1.5 w-44 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all placeholder:opacity-30" placeholder="Search nodes..." type="text"/>
</div>
<button class="material-symbols-outlined text-on-surface-variant hover:text-on-surface hover:bg-white/10 p-1.5 rounded-lg spring-transition">settings</button>
<button class="material-symbols-outlined text-on-surface-variant hover:text-on-surface hover:bg-white/10 p-1.5 rounded-lg spring-transition">help</button>
<div class="h-6 w-[1px] bg-white/10 mx-1"></div>
<button class="flex items-center gap-2 hover:bg-white/10 p-1 rounded-lg spring-transition pr-2">
<div class="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-secondary-fixed opacity-80"></div>
<span class="text-[12px] text-on-surface font-medium hidden lg:block">System Admin</span>
</button>
</div>
</header>
<div class="flex flex-1 mt-[48px] mb-10 overflow-hidden">
<!-- SideNavBar (Left Rail - Fixed 48px) -->
<aside class="w-[48px] bg-surface-container-lowest border-r border-outline-variant flex flex-col items-center py-4 z-40">
<nav class="flex-1 flex flex-col items-center gap-4">
<div class="p-2 text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-xl cursor-pointer spring-transition group" title="Ingest">
<span class="material-symbols-outlined">input</span>
</div>
<div class="p-2 text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-xl cursor-pointer spring-transition" title="Forge">
<span class="material-symbols-outlined">terminal</span>
</div>
<div class="p-2 bg-primary/10 text-primary rounded-xl cursor-pointer spring-transition" title="Observatory">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">visibility</span>
</div>
<div class="p-2 text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-xl cursor-pointer spring-transition" title="Engine">
<span class="material-symbols-outlined">engineering</span>
</div>
<div class="p-2 text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-xl cursor-pointer spring-transition" title="Sanctuary">
<span class="material-symbols-outlined">security</span>
</div>
<div class="p-2 text-on-surface-variant hover:text-on-surface hover:bg-white/5 rounded-xl cursor-pointer spring-transition" title="Cockpit">
<span class="material-symbols-outlined">settings_input_component</span>
</div>
</nav>
<div class="flex flex-col gap-4 mb-2">
<div class="p-2 text-on-surface-variant hover:text-on-surface cursor-pointer spring-transition">
<span class="material-symbols-outlined">list_alt</span>
</div>
<div class="p-2 text-on-surface-variant hover:text-on-surface cursor-pointer spring-transition">
<span class="material-symbols-outlined">code</span>
</div>
</div>
</aside>
<!-- Main Workspace (Center Graph - Manifold Visualization) -->
<main class="flex-1 relative bg-[#0b0b0d] overflow-hidden">
<div class="scanline"></div>
<!-- Breadcrumb Path Overlay -->
<div class="absolute top-4 left-6 z-30 flex items-center gap-2 pointer-events-none">
<span class="text-[11px] font-medium tracking-widest text-on-surface-variant uppercase opacity-50">System</span>
<span class="material-symbols-outlined text-[12px] text-on-surface-variant opacity-30">chevron_right</span>
<span class="text-[11px] font-medium tracking-widest text-on-surface uppercase">Topological Observatory</span>
</div>
<!-- Topological Node Overlay -->
<svg class="absolute inset-0 w-full h-full pointer-events-none" preserveaspectratio="none" viewbox="0 0 1000 1000">
<defs>
<lineargradient id="blueGrad" x1="0%" x2="100%" y1="0%" y2="100%">
<stop offset="0%" stop-color="#3b82f6" stop-opacity="0.6"></stop>
<stop offset="100%" stop-color="#3b82f6" stop-opacity="0.1"></stop>
</lineargradient>
</defs>
<line opacity="0.3" stroke="#3b82f6" stroke-width="0.5" x1="200" x2="450" y1="300" y2="150"></line>
<line opacity="0.3" stroke="#10b981" stroke-width="0.5" x1="450" x2="700" y1="150" y2="400"></line>
<line opacity="0.3" stroke="#f97316" stroke-width="0.5" x1="700" x2="300" y1="400" y2="600"></line>
<line opacity="0.3" stroke="#3b82f6" stroke-width="0.5" x1="300" x2="200" y1="600" y2="300"></line>
<line opacity="0.2" stroke="#ffffff" stroke-width="0.3" x1="450" x2="300" y1="150" y2="600"></line>
<line opacity="0.2" stroke="#f97316" stroke-width="0.5" x1="700" x2="850" y1="400" y2="200"></line>
</svg>
<!-- Interactive Nodes -->
<div class="absolute inset-0 pointer-events-none">
<!-- Blue Node -->
<div class="absolute top-[30%] left-[20%] pointer-events-auto group">
<div class="w-2.5 h-2.5 bg-blue-500 rounded-full node-pulse shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
<div class="opacity-0 group-hover:opacity-100 absolute top-4 left-4 glass-panel rounded-lg p-2 whitespace-nowrap z-50 spring-transition translate-y-1 group-hover:translate-y-0 shadow-2xl">
<p class="text-[11px] font-bold text-primary">FRG_ID: 0x44A2</p>
<p class="text-[10px] text-on-surface-variant mt-1">Tension: 0.244</p>
</div>
</div>
<!-- Green Node -->
<div class="absolute top-[15%] left-[45%] pointer-events-auto group">
<div class="w-2.5 h-2.5 bg-emerald-500 rounded-full node-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
<div class="opacity-0 group-hover:opacity-100 absolute top-4 left-4 glass-panel rounded-lg p-2 whitespace-nowrap z-50 spring-transition translate-y-1 group-hover:translate-y-0 shadow-2xl">
<p class="text-[11px] font-bold text-secondary">FRG_ID: 0x99B1</p>
<p class="text-[10px] text-on-surface-variant mt-1">Tension: 0.812</p>
</div>
</div>
<!-- Orange Node -->
<div class="absolute top-[40%] left-[70%] pointer-events-auto group">
<div class="w-2.5 h-2.5 bg-orange-500 rounded-full node-pulse shadow-[0_0_10px_rgba(249,115,22,0.5)]"></div>
<div class="opacity-0 group-hover:opacity-100 absolute top-4 left-4 glass-panel rounded-lg p-2 whitespace-nowrap z-50 spring-transition translate-y-1 group-hover:translate-y-0 shadow-2xl">
<p class="text-[11px] font-bold text-tertiary">FRG_ID: 0xF2E4</p>
<p class="text-[10px] text-on-surface-variant mt-1">Tension: 1.045</p>
</div>
</div>
<!-- Large Central Node -->
<div class="absolute top-[60%] left-[30%] pointer-events-auto group">
<div class="w-4 h-4 rounded-full border-2 border-primary bg-primary/20 node-pulse flex items-center justify-center">
<div class="w-1.5 h-1.5 bg-white rounded-full"></div>
</div>
<div class="opacity-0 group-hover:opacity-100 absolute top-6 left-6 glass-panel rounded-lg p-2.5 whitespace-nowrap z-50 spring-transition translate-y-1 group-hover:translate-y-0 shadow-2xl">
<p class="text-[12px] font-bold text-white">CORE_SYNC_POINT</p>
<p class="text-[10px] text-on-surface-variant mt-1">Ricci Scalar: 14.22</p>
</div>
</div>
</div>
<!-- UI Overlays: Top Left Legend -->
<div class="absolute top-16 left-6 flex flex-col gap-4">
<div class="glass-panel rounded-2xl p-4 flex flex-col gap-3 min-w-[200px] shadow-lg">
<h3 class="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant/70 mb-1">Manifold Filter</h3>
<div class="flex items-center gap-3 cursor-pointer group">
<div class="w-4 h-4 rounded-[4px] border border-white/20 bg-primary flex items-center justify-center spring-transition group-hover:border-primary">
<span class="material-symbols-outlined text-[12px] text-on-primary">check</span>
</div>
<span class="text-[12px] text-on-surface font-medium group-hover:text-primary transition-colors">Algorithm Binding</span>
</div>
<div class="flex items-center gap-3 cursor-pointer group">
<div class="w-4 h-4 rounded-[4px] border border-white/20 bg-primary flex items-center justify-center spring-transition group-hover:border-primary">
<span class="material-symbols-outlined text-[12px] text-on-primary">check</span>
</div>
<span class="text-[12px] text-on-surface font-medium group-hover:text-primary transition-colors">Data Dependency</span>
</div>
<div class="flex items-center gap-3 cursor-pointer group">
<div class="w-4 h-4 rounded-[4px] border border-white/20 bg-transparent spring-transition group-hover:border-primary"></div>
<span class="text-[12px] text-on-surface-variant group-hover:text-primary transition-colors">Tensor Curvature</span>
</div>
<div class="flex items-center gap-3 cursor-pointer group">
<div class="w-4 h-4 rounded-[4px] border border-white/20 bg-primary flex items-center justify-center spring-transition group-hover:border-primary">
<span class="material-symbols-outlined text-[12px] text-on-primary">check</span>
</div>
<span class="text-[12px] text-on-surface font-medium group-hover:text-primary transition-colors">Ricci Flow Opt</span>
</div>
</div>
<button class="bg-primary hover:bg-primary/90 text-on-primary-container px-6 py-2.5 rounded-2xl font-bold text-[13px] spring-transition shadow-xl shadow-primary/10 active:scale-[0.97]">
                Execute Global Mapping
            </button>
</div>
<!-- HUD Elements -->
<div class="absolute top-16 right-6 flex flex-col gap-2 items-end">
<div class="bg-primary/10 px-3 py-1.5 rounded-xl border border-primary/20 backdrop-blur-md">
<p class="text-[10px] font-mono font-semibold text-primary tracking-tight">SCAN_PHASE: ACTIVE</p>
</div>
<div class="bg-secondary/10 px-3 py-1.5 rounded-xl border border-secondary/20 backdrop-blur-md">
<p class="text-[10px] font-mono font-semibold text-secondary tracking-tight">LATENCY: 12ms</p>
</div>
</div>
</main>
<!-- Right Inspector (Fixed 320px) -->
<aside class="w-[320px] glass-panel border-l border-outline-variant flex flex-col h-full overflow-hidden shadow-2xl z-40">
<div class="p-6 border-b border-white/5">
<h3 class="text-[17px] font-bold text-on-surface tracking-tight">Manifold Inspector</h3>
<p class="text-[11px] font-mono text-on-surface-variant mt-1.5 uppercase opacity-60">Node ID: 0xF2E4_CALIB</p>
</div>
<div class="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col gap-8">
<!-- Section: Coordinates -->
<div class="flex flex-col gap-4">
<div class="flex justify-between items-center">
<span class="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant/70">Spatial Positioning</span>
<span class="material-symbols-outlined text-[16px] text-on-surface-variant">grid_view</span>
</div>
<div class="grid grid-cols-2 gap-3">
<div class="bg-white/5 p-3 rounded-2xl border border-white/5 hover:bg-white/[0.08] transition-colors group">
<p class="text-[9px] font-bold text-on-surface-variant mb-1 group-hover:text-primary transition-colors">LATITUDE</p>
<p class="text-[14px] font-mono font-semibold text-on-surface">42.88122-N</p>
</div>
<div class="bg-white/5 p-3 rounded-2xl border border-white/5 hover:bg-white/[0.08] transition-colors group">
<p class="text-[9px] font-bold text-on-surface-variant mb-1 group-hover:text-primary transition-colors">LONGITUDE</p>
<p class="text-[14px] font-mono font-semibold text-on-surface">11.00234-E</p>
</div>
<div class="bg-white/5 p-3 rounded-2xl border border-white/5 col-span-2 hover:bg-white/[0.08] transition-colors group">
<p class="text-[9px] font-bold text-on-surface-variant mb-1 group-hover:text-primary transition-colors">EUCLIDEAN_Z_OFFSET</p>
<p class="text-[14px] font-mono font-semibold text-on-surface">+1,442.091 AU</p>
</div>
</div>
</div>
<!-- Section: Curvature Metrics -->
<div class="flex flex-col gap-4">
<div class="flex justify-between items-center">
<span class="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant/70">Manifold Metrics</span>
<span class="material-symbols-outlined text-[16px] text-on-surface-variant">monitoring</span>
</div>
<div class="flex flex-col gap-5">
<div>
<div class="flex justify-between text-[12px] mb-2">
<span class="text-on-surface-variant">Ricci Scalar</span>
<span class="font-mono text-primary font-bold">14.2209</span>
</div>
<div class="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
<div class="bg-primary h-full rounded-full" style="width: 72%"></div>
</div>
</div>
<div>
<div class="flex justify-between text-[12px] mb-2">
<span class="text-on-surface-variant">Gaussian Curvature</span>
<span class="font-mono text-secondary font-bold">0.0041</span>
</div>
<div class="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
<div class="bg-secondary h-full rounded-full" style="width: 14%"></div>
</div>
</div>
<div>
<div class="flex justify-between text-[12px] mb-2">
<span class="text-on-surface-variant">Manifold Tension</span>
<span class="font-mono text-tertiary font-bold">0.8992</span>
</div>
<div class="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
<div class="bg-tertiary h-full rounded-full" style="width: 89%"></div>
</div>
</div>
</div>
</div>
<!-- Section: Citations -->
<div class="flex flex-col gap-4">
<div class="flex justify-between items-center">
<span class="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant/70">System Citations</span>
<span class="material-symbols-outlined text-[16px] text-on-surface-variant">auto_stories</span>
</div>
<div class="flex flex-col gap-2">
<div class="bg-white/5 p-3 rounded-2xl border border-white/5 hover:bg-white/[0.08] hover:border-primary/20 cursor-pointer spring-transition">
<p class="text-[13px] font-bold text-on-surface">PRJ_FRG_2023.01</p>
<p class="text-[10px] text-on-surface-variant mt-1">Holomorphic Manifold Mapping</p>
</div>
<div class="bg-white/5 p-3 rounded-2xl border border-white/5 hover:bg-white/[0.08] hover:border-primary/20 cursor-pointer spring-transition">
<p class="text-[13px] font-bold text-on-surface">arXiv:2401.0092</p>
<p class="text-[10px] text-on-surface-variant mt-1">Differential Geometry of Loom</p>
</div>
</div>
</div>
</div>
<!-- Panel Footer Stats -->
<div class="p-6 bg-black/20 border-t border-white/5 grid grid-cols-2 gap-4">
<div class="flex flex-col">
<span class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider opacity-60">System Uptime</span>
<span class="text-[14px] font-mono font-bold mt-1">114h 22m</span>
</div>
<div class="flex flex-col text-right">
<span class="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider opacity-60">Active Nodes</span>
<span class="text-[14px] font-mono font-bold text-secondary mt-1">4,129 / 8k</span>
</div>
</div>
</aside>
</div>
<!-- Bottom Console / Status Bar -->
<footer class="fixed bottom-0 w-full h-10 glass-surface border-t border-outline-variant z-50 flex items-center justify-between px-6 overflow-hidden">
<div class="flex items-center gap-6">
<div class="flex items-center gap-3">
<button class="material-symbols-outlined text-secondary hover:text-white transition-colors">play_arrow</button>
<button class="material-symbols-outlined text-on-surface-variant hover:text-white transition-colors">pause</button>
<button class="material-symbols-outlined text-on-surface-variant hover:text-white transition-colors">stop</button>
</div>
<div class="flex items-center gap-4 border-l border-white/10 pl-6">
<span class="text-[10px] font-mono text-secondary font-bold tracking-tight">RICCI_FLOW: 14/20</span>
<div class="w-32 bg-white/10 h-1.5 rounded-full overflow-hidden">
<div class="h-full bg-secondary rounded-full" style="width: 70%"></div>
</div>
</div>
</div>
<div class="flex-1 px-8 overflow-hidden">
<div class="flex gap-6 font-mono text-[10px] text-on-surface-variant whitespace-nowrap">
<span class="animate-pulse flex items-center gap-1.5">
<span class="w-1 h-1 bg-secondary rounded-full"></span>
                [LOG] TENSOR_INIT_SUCCESS
            </span>
<span class="opacity-30">|</span>
<span class="hover:text-on-surface transition-colors cursor-default">[SYS] FRAGMENT_MAP_MOUNTED_AT_0x44A2</span>
<span class="opacity-30">|</span>
<span class="text-secondary/80">STDOUT: STABLE</span>
</div>
</div>
<div class="flex items-center gap-4">
<span class="font-mono text-[10px] uppercase tracking-widest text-on-surface-variant opacity-60">LOOM BLUEPRINT v1.0.4</span>
<div class="flex gap-1">
<div class="w-1.5 h-1.5 rounded-full bg-secondary"></div>
<div class="w-1.5 h-1.5 rounded-full bg-white/10"></div>
<div class="w-1.5 h-1.5 rounded-full bg-secondary opacity-40"></div>
</div>
</div>
</footer>
<script>
    // Simulate real-time tracking updates
    setInterval(() => {
        const stats = document.querySelectorAll('.font-mono.font-semibold');
        if (stats[0]) {
            const current = stats[0].innerText.split('-')[0];
            const direction = Math.random() > 0.5 ? 'N' : 'S';
            stats[0].innerText = `${current}-${direction}`;
        }
    }, 4000);

    // Simple interaction log
    document.querySelectorAll('.group').forEach(node => {
        node.addEventListener('click', () => {
            console.log('Node inspection active');
        });
    });
</script>
<button class="fixed bottom-12 right-6 z-50 w-10 h-10 rounded-full glass-panel flex items-center justify-center text-primary shadow-2xl hover:bg-white/10 transition-all active:scale-95 border border-white/20" id="dashboard-toggle"><span class="material-symbols-outlined">dashboard</span></button><aside class="fixed top-0 right-0 h-full w-[380px] z-[60] glass-surface border-l border-white/10 translate-x-full transition-transform duration-500 ease-in-out flex flex-col shadow-2xl" id="floating-dashboard" style="backdrop-filter: blur(24px); background: rgba(255, 255, 255, 0.06);">
<div class="p-6 flex justify-between items-center border-b border-white/10">
<div>
<h2 class="text-[17px] font-bold text-white tracking-tight">Architectural Pulse</h2>
<div class="flex items-center gap-1.5 mt-1">
<span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
<span class="text-[10px] font-mono text-secondary uppercase tracking-widest">System Nominal</span>
</div>
</div>
<button class="p-2 hover:bg-white/10 rounded-lg transition-colors" id="dashboard-close">
<span class="material-symbols-outlined text-on-surface-variant">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col gap-8">
<!-- Critical Drift -->
<section>
<h3 class="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant/70 mb-4">Critical Drift</h3>
<div class="bg-white/5 p-4 rounded-2xl border border-white/5">
<div class="flex items-baseline gap-2">
<span class="text-[32px] font-bold text-error">1.24%</span>
<span class="text-[11px] text-error/80">+0.05% today</span>
</div>
<div class="mt-3 h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
<div class="h-full bg-error rounded-full" style="width: 65%"></div>
</div>
</div>
</section>
<!-- Awaiting Ratification -->
<section>
<h3 class="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant/70 mb-4">Awaiting Ratification</h3>
<div class="flex flex-col gap-3">
<div class="bg-white/5 p-3 rounded-xl border border-white/5 hover:border-primary/30 cursor-pointer transition-colors">
<p class="text-[12px] font-bold text-white">LOOM_MAINFRAME_B2</p>
<p class="text-[10px] text-on-surface-variant mt-1">Structural Integrity Check</p>
</div>
<div class="bg-white/5 p-3 rounded-xl border border-white/5 hover:border-primary/30 cursor-pointer transition-colors">
<p class="text-[12px] font-bold text-white">CORE_EXPANSION_P7</p>
<p class="text-[10px] text-on-surface-variant mt-1">Resource Allocation Drift</p>
</div>
</div>
</section>
<!-- Contextual Activity -->
<section>
<h3 class="text-[11px] font-bold uppercase tracking-widest text-on-surface-variant/70 mb-4">Recent Activity</h3>
<div class="space-y-4">
<div class="flex gap-3">
<div class="w-1.5 h-1.5 rounded-full bg-secondary mt-1.5"></div>
<div>
<p class="text-[12px] text-on-surface">Forge Module optimized Hyperion_V4</p>
<p class="text-[10px] text-on-surface-variant mt-0.5">12m ago</p>
</div>
</div>
<div class="flex gap-3">
<div class="w-1.5 h-1.5 rounded-full bg-primary mt-1.5"></div>
<div>
<p class="text-[12px] text-on-surface">Engine Core corrected sector 7G</p>
<p class="text-[10px] text-on-surface-variant mt-0.5">45m ago</p>
</div>
</div>
</div>
</section>
</div>
</aside><script>
    const toggleBtn = document.getElementById('dashboard-toggle');
    const closeBtn = document.getElementById('dashboard-close');
    const dashboard = document.getElementById('floating-dashboard');

    toggleBtn.addEventListener('click', () => {
        dashboard.classList.remove('translate-x-full');
    });

    closeBtn.addEventListener('click', () => {
        dashboard.classList.add('translate-x-full');
    });
</script></body></html>