<!-- Loom Blueprint Workbench - Claims Ledger -->
<!DOCTYPE html>
<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Claims Ledger | Loom Blueprint Workbench</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/geist@1.3.0/dist/fonts/geist-sans/style.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/css/jetbrains-mono.min.css" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;display=swap" rel="stylesheet"/>
<style>
        :root {
            --glass-bg: rgba(28, 28, 30, 0.8);
            --glass-border: rgba(255, 255, 255, 0.1);
            --glass-blur: 20px;
        }
        body {
            background-color: #09090b;
            color: #e4e2e4;
            overflow: hidden;
            font-family: 'Geist', sans-serif;
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
        }
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(var(--glass-blur));
            border: 0.5px solid var(--glass-border);
        }
        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        .glow-blue {
            box-shadow: 0 0 15px rgba(170, 199, 255, 0.2);
        }
        .spring-transition {
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
    </style>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "on-secondary-fixed-variant": "#00531a",
                        "surface-container-highest": "#353437",
                        "tertiary": "#ffb868",
                        "on-tertiary-fixed-variant": "#673d00",
                        "error": "#ffb4ab",
                        "tertiary-fixed-dim": "#ffb868",
                        "tertiary-fixed": "#ffddbb",
                        "outline-variant": "#414754",
                        "on-secondary-container": "#004615",
                        "background": "#09090b",
                        "secondary": "#47e266",
                        "on-tertiary": "#482900",
                        "tertiary-container": "#ce7f00",
                        "surface-variant": "#353437",
                        "surface": "#131315",
                        "on-error-container": "#ffdad6",
                        "inverse-primary": "#005db8",
                        "on-surface-variant": "#c0c6d6",
                        "on-secondary-fixed": "#002106",
                        "surface-container": "#1f1f21",
                        "on-primary": "#003064",
                        "on-primary-fixed": "#001b3e",
                        "on-primary-fixed-variant": "#00468d",
                        "inverse-surface": "#e4e2e4",
                        "primary-fixed": "#d6e3ff",
                        "surface-bright": "#39393b",
                        "surface-container-lowest": "#0e0e10",
                        "surface-container-low": "#1b1b1d",
                        "on-tertiary-container": "#3f2300",
                        "secondary-fixed-dim": "#47e266",
                        "error-container": "#93000a",
                        "outline": "#8b91a0",
                        "surface-container-high": "#2a2a2c",
                        "on-surface": "#e4e2e4",
                        "surface-tint": "#aac7ff",
                        "primary-container": "#3e90ff",
                        "inverse-on-surface": "#303032",
                        "on-primary-container": "#002957",
                        "secondary-fixed": "#6cff82",
                        "primary": "#aac7ff",
                        "on-background": "#e4e2e4",
                        "primary-fixed-dim": "#aac7ff",
                        "on-tertiary-fixed": "#2b1700",
                        "on-error": "#690005",
                        "surface-dim": "#131315",
                        "secondary-container": "#09bf49",
                        "on-secondary": "#003910"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.25rem",
                        "lg": "12px",
                        "xl": "16px",
                        "full": "9999px"
                    },
                    "spacing": {
                        "stack-sm": "4px",
                        "unit": "8px",
                        "panel-padding": "12px",
                        "stack-md": "8px",
                        "container-margin": "24px",
                        "stack-lg": "16px",
                        "gutter": "16px"
                    },
                    "fontFamily": {
                        "label-caps": ["Geist"],
                        "headline-lg": ["Geist"],
                        "body-sm": ["Geist"],
                        "display-lg": ["Geist"],
                        "body-lg": ["Geist"],
                        "title-md": ["Geist"],
                        "mono-precision": ["JetBrains Mono"],
                        "headline-lg-mobile": ["Geist"]
                    },
                    "fontSize": {
                        "label-caps": ["12px", {"lineHeight": "1.2", "letterSpacing": "0.05em", "fontWeight": "600"}],
                        "headline-lg": ["32px", {"lineHeight": "1.2", "letterSpacing": "-0.02em", "fontWeight": "600"}],
                        "body-sm": ["14px", {"lineHeight": "1.5", "letterSpacing": "0em", "fontWeight": "400"}],
                        "display-lg": ["48px", {"lineHeight": "1.1", "letterSpacing": "-0.03em", "fontWeight": "700"}],
                        "body-lg": ["16px", {"lineHeight": "1.5", "letterSpacing": "-0.01em", "fontWeight": "400"}],
                        "title-md": ["20px", {"lineHeight": "1.4", "letterSpacing": "-0.01em", "fontWeight": "600"}],
                        "mono-precision": ["13px", {"lineHeight": "1", "letterSpacing": "0em", "fontWeight": "500"}],
                        "headline-lg-mobile": ["24px", {"lineHeight": "1.2", "letterSpacing": "-0.02em", "fontWeight": "600"}]
                    }
                }
            }
        }
    </script>
</head>
<body class="flex flex-col h-screen overflow-hidden">
<!-- TopNavBar -->
<header class="flex justify-between items-center px-container-margin w-full h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 shadow-sm z-50">
<div class="flex items-center space-x-6">
<span class="font-display-lg text-title-md font-bold text-primary tracking-tight">Loom Blueprint Workbench</span>
<nav class="flex items-center space-x-gutter">
<a class="text-on-surface-variant font-medium font-body-lg text-body-lg hover:text-primary transition-colors" href="#">Models</a>
<a class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg" href="#">Drafts</a>
<a class="text-on-surface-variant font-medium font-body-lg text-body-lg hover:text-primary transition-colors" href="#">Archive</a>
</nav>
</div>
<div class="flex items-center space-x-stack-lg">
<div class="flex items-center space-x-2 text-on-surface-variant/60 font-label-caps text-label-caps uppercase tracking-widest">
<span>Ingest</span>
<span class="material-symbols-outlined text-[14px]">chevron_right</span>
<span class="text-primary">Claims Ledger</span>
</div>
<div class="h-6 w-[1px] bg-outline-variant/30"></div>
<div class="flex space-x-stack-md">
<button class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors active:scale-95">help</button>
<button class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors active:scale-95">settings</button>
</div>
</div>
</header>
<div class="flex flex-1 overflow-hidden relative">
<!-- SideNavBar (Left Tool Dock) -->
<aside class="flex flex-col items-center py-stack-lg space-y-stack-md bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 w-[64px] h-full z-40">
<div class="mb-stack-lg opacity-40">
<span class="material-symbols-outlined">manufacturing</span>
</div>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">near_me</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">straighten</span>
</button>
<button class="w-10 h-10 flex items-center justify-center bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)] transition-all">
<span class="material-symbols-outlined">architecture</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">layers</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">visibility</span>
</button>
</aside>
<!-- Main Content Area -->
<main class="flex-1 relative flex flex-col p-stack-lg overflow-hidden">
<!-- Matrix Header & Forge Controls -->
<div class="flex justify-between items-end mb-6">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface tracking-tight">Claims Ledger</h1>
<p class="text-on-surface-variant font-body-sm text-body-sm mt-1">Processing atomic architectural evidence into verified structural claims.</p>
</div>
<div class="flex space-x-stack-md">
<button class="px-6 py-2 bg-surface-container-highest/50 border border-outline-variant/30 rounded-lg text-on-surface font-label-caps text-label-caps hover:bg-surface-container-highest transition-all flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">history</span> REVERT
                    </button>
<button class="px-6 py-2 bg-primary text-on-primary rounded-lg font-label-caps text-label-caps glow-blue hover:brightness-110 active:scale-95 transition-all flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">auto_fix</span> AUTO-RECONCILE
                    </button>
</div>
</div>
<!-- Warning Bar (Contradiction Indicator) -->
<div class="mb-stack-lg glass-panel bg-error-container/10 border-error/20 p-stack-md rounded-lg flex items-center justify-between">
<div class="flex items-center gap-3">
<div class="w-2 h-2 rounded-full bg-error animate-pulse shadow-[0_0_8px_#ffb4ab]"></div>
<span class="text-error font-label-caps text-label-caps uppercase tracking-widest">3 Architectural Discrepancies Detected</span>
<span class="text-on-surface-variant/60 text-body-sm">— Conflict in 'Dependency Alignment' between Source-A and Source-F</span>
</div>
<button class="text-error font-label-caps text-label-caps hover:underline">VIEW CONFLICTS</button>
</div>
<!-- Normalization Table (The Matrix) -->
<div class="flex-1 glass-panel rounded-xl overflow-hidden flex flex-col shadow-2xl">
<!-- Frosted Header -->
<div class="grid grid-cols-6 bg-surface-container-high/60 backdrop-blur-md border-b border-outline-variant/30 py-3 px-6 text-on-surface-variant font-label-caps text-label-caps tracking-widest uppercase">
<div class="col-span-2">Attribute Identifier</div>
<div>Source Delta</div>
<div>Confidence Score</div>
<div>Verification Status</div>
<div class="text-right">Actions</div>
</div>
<!-- Scrollable Body -->
<div class="flex-1 overflow-y-auto custom-scrollbar p-1">
<!-- Row 1: Active Conflict -->
<div class="grid grid-cols-6 items-center py-4 px-6 mb-1 rounded-lg bg-error-container/5 border-l-4 border-error hover:bg-surface-container-low transition-colors group">
<div class="col-span-2 flex flex-col">
<span class="text-on-surface font-title-md text-body-lg font-semibold">Torsion Mount Alpha</span>
<span class="text-on-surface-variant/60 font-mono-precision text-[11px]">UUID: 882-901-XF</span>
</div>
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-error text-[18px]">warning</span>
<span class="text-error font-mono-precision text-mono-precision">+2.45mm Variance</span>
</div>
<div>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="w-[42%] h-full bg-error"></div>
</div>
<span class="text-[10px] text-on-surface-variant/40 mt-1 block">42.8% Confidence</span>
</div>
<div class="flex items-center">
<span class="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-mono-precision text-[10px]">INFERRED</span>
</div>
<div class="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">edit</span></button>
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">more_vert</span></button>
</div>
</div>
<!-- Row 2: Resolved -->
<div class="grid grid-cols-6 items-center py-4 px-6 mb-1 rounded-lg hover:bg-surface-container-low transition-colors group">
<div class="col-span-2 flex flex-col">
<span class="text-on-surface font-title-md text-body-lg font-semibold">Lateral Strut Support</span>
<span class="text-on-surface-variant/60 font-mono-precision text-[11px]">UUID: 441-220-KL</span>
</div>
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-secondary text-[18px]">check_circle</span>
<span class="text-secondary font-mono-precision text-mono-precision">Nominal</span>
</div>
<div>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="w-[98%] h-full bg-secondary"></div>
</div>
<span class="text-[10px] text-on-surface-variant/40 mt-1 block">99.2% Confidence</span>
</div>
<div class="flex items-center">
<span class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary font-mono-precision text-[10px]">OBSERVED</span>
</div>
<div class="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">visibility</span></button>
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">more_vert</span></button>
</div>
</div>
<!-- Row 3: Minor Conflict -->
<div class="grid grid-cols-6 items-center py-4 px-6 mb-1 rounded-lg bg-tertiary/5 border-l-4 border-tertiary hover:bg-surface-container-low transition-colors group">
<div class="col-span-2 flex flex-col">
<span class="text-on-surface font-title-md text-body-lg font-semibold">Coolant Manifold Mesh</span>
<span class="text-on-surface-variant/60 font-mono-precision text-[11px]">UUID: 009-331-ZT</span>
</div>
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-tertiary text-[18px]">priority_high</span>
<span class="text-tertiary font-mono-precision text-mono-precision">Meta-tag Drift</span>
</div>
<div>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="w-[74%] h-full bg-tertiary"></div>
</div>
<span class="text-[10px] text-on-surface-variant/40 mt-1 block">74.1% Confidence</span>
</div>
<div class="flex items-center">
<span class="px-2 py-0.5 rounded-full bg-tertiary/10 text-tertiary font-mono-precision text-[10px]">DECLARED</span>
</div>
<div class="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">edit</span></button>
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">more_vert</span></button>
</div>
</div>
<!-- Additional Rows for high-capacity look -->
<div class="grid grid-cols-6 items-center py-4 px-6 mb-1 rounded-lg hover:bg-surface-container-low transition-colors group opacity-60">
<div class="col-span-2 flex flex-col">
<span class="text-on-surface font-title-md text-body-lg font-semibold">Sensor Array Base</span>
<span class="text-on-surface-variant/60 font-mono-precision text-[11px]">UUID: 101-299-BC</span>
</div>
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-secondary text-[18px]">check_circle</span>
<span class="text-secondary font-mono-precision text-mono-precision">Nominal</span>
</div>
<div>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="w-[92%] h-full bg-secondary"></div>
</div>
<span class="text-[10px] text-on-surface-variant/40 mt-1 block">92.4% Confidence</span>
</div>
<div class="flex items-center">
<span class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary font-mono-precision text-[10px]">OBSERVED</span>
</div>
<div class="flex justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="p-1 hover:bg-surface-container-highest rounded"><span class="material-symbols-outlined text-[20px]">visibility</span></button>
</div>
</div>
</div>
</div>
<!-- Bottom Floating Action -->
<div class="mt-6 flex justify-center">
<button class="group relative px-10 py-4 bg-primary/20 backdrop-blur-xl border border-primary/50 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(170,199,255,0.15)] active:scale-95 transition-all">
<div class="absolute inset-0 bg-gradient-to-tr from-primary/10 to-transparent pointer-events-none"></div>
<div class="flex items-center gap-4 relative z-10">
<span class="material-symbols-outlined text-primary text-[24px]">verified</span>
<span class="text-on-surface font-display-lg text-title-md uppercase tracking-[0.2em]">Confirm Consolidated Topology</span>
</div>
<div class="absolute bottom-0 left-0 h-[2px] w-full bg-primary transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-center"></div>
</button>
</div>
</main>
<!-- Right Inspector Panel -->
<aside class="w-[320px] h-full bg-surface-container-low/80 backdrop-blur-xl border-l border-outline-variant/30 p-container-margin flex flex-col z-40">
<div class="mb-stack-lg">
<h3 class="text-on-surface font-label-caps text-label-caps tracking-widest uppercase mb-4">Attribute Inspector</h3>
<div class="glass-panel rounded-lg p-stack-md mb-6">
<div class="flex justify-between items-center mb-2">
<span class="text-on-surface-variant font-body-sm text-body-sm">Global Precision</span>
<span class="text-primary font-mono-precision text-mono-precision">0.001μm</span>
</div>
<div class="flex justify-between items-center">
<span class="text-on-surface-variant font-body-sm text-body-sm">Active Layers</span>
<span class="text-secondary font-mono-precision text-mono-precision">12</span>
</div>
</div>
</div>
<div class="flex-1">
<h3 class="text-on-surface font-label-caps text-label-caps tracking-widest uppercase mb-4">Source Contributions</h3>
<div class="space-y-stack-md">
<div class="flex items-center gap-3 p-stack-md bg-surface-container-high rounded-lg border border-outline-variant/10">
<div class="w-8 h-8 rounded bg-primary/20 flex items-center justify-center text-primary font-bold">A</div>
<div class="flex-1 overflow-hidden">
<p class="text-on-surface font-body-sm text-body-sm truncate">Architecture_Final_V4.cad</p>
<p class="text-on-surface-variant/40 text-[10px]">Modified: 2h ago</p>
</div>
<span class="material-symbols-outlined text-on-surface-variant/30">drag_indicator</span>
</div>
<div class="flex items-center gap-3 p-stack-md bg-surface-container-high rounded-lg border border-outline-variant/10">
<div class="w-8 h-8 rounded bg-tertiary/20 flex items-center justify-center text-tertiary font-bold">F</div>
<div class="flex-1 overflow-hidden">
<p class="text-on-surface font-body-sm text-body-sm truncate">Fluid_Dynamics_Schema.yaml</p>
<p class="text-on-surface-variant/40 text-[10px]">Modified: 5m ago</p>
</div>
<span class="material-symbols-outlined text-on-surface-variant/30">drag_indicator</span>
</div>
</div>
</div>
<div class="mt-auto">
<div class="p-stack-md bg-surface-container-highest rounded-xl border border-outline-variant/20 mb-stack-lg">
<p class="text-[11px] text-on-surface-variant font-medium leading-relaxed">
                        Loom AI suggests merging <span class="text-primary font-bold">Source-F</span> data into the primary mesh to resolve Z-Axis drift.
                    </p>
<button class="mt-3 w-full py-1.5 bg-surface-container-low text-primary font-label-caps text-[10px] rounded hover:bg-surface transition-colors uppercase tracking-widest border border-primary/20">Apply Suggestion</button>
</div>
<div class="flex items-center gap-2 px-2 opacity-50">
<span class="material-symbols-outlined text-[14px]">terminal</span>
<span class="text-[10px] font-mono-precision">LEDGER_ENGINE_ACTIVE :: PORT_9091</span>
</div>
</div>
</aside>
</div>
<!-- Bottom Console (Status Bar Style) -->
<footer class="fixed bottom-0 left-0 w-full h-12 z-50 flex justify-between items-center px-container-margin bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30">
<div class="flex items-center space-x-gutter">
<button class="flex flex-col items-center text-on-surface-variant/70 hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">terminal</span>
<span class="font-mono-precision text-[10px] uppercase">Logs</span>
</button>
<button class="flex flex-col items-center text-on-surface-variant/70 hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">play_circle</span>
<span class="font-mono-precision text-[10px] uppercase">Timeline</span>
</button>
<button class="flex flex-col items-center text-tertiary-fixed font-bold flex flex-col items-center active:scale-98">
<span class="material-symbols-outlined text-[18px]">description</span>
<span class="font-mono-precision text-[10px] uppercase">Output</span>
</button>
<button class="flex flex-col items-center text-on-surface-variant/70 hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">bug_report</span>
<span class="font-mono-precision text-[10px] uppercase">Debug</span>
</button>
</div>
<div class="flex items-center space-x-6">
<div class="flex items-center space-x-2">
<span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
<span class="text-on-surface-variant font-mono-precision text-[11px]">System Nominal</span>
</div>
<div class="flex items-center space-x-2">
<span class="text-on-surface-variant/50 font-mono-precision text-[11px]">V1.2.0-PRO</span>
</div>
</div>
<button class="flex items-center gap-2 px-3 py-1 bg-primary/10 border border-primary/30 rounded-full hover:bg-primary/20 transition-all active:scale-95 ml-4" id="dashboard-toggle"><span class="material-symbols-outlined text-[18px] text-primary">dashboard</span><span class="font-label-caps text-[10px] text-primary uppercase tracking-widest">Pulse</span></button></footer>
<script>
        // Micro-interactions for table rows
        document.querySelectorAll('.grid.hover\\:bg-surface-container-low').forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.transform = 'translateX(4px)';
            });
            row.addEventListener('mouseleave', () => {
                row.style.transform = 'translateX(0)';
            });
        });

        // Toggle console buttons active state
        const footerButtons = document.querySelectorAll('footer button');
        footerButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                footerButtons.forEach(b => {
                    b.classList.remove('text-tertiary-fixed', 'font-bold');
                    b.classList.add('text-on-surface-variant/70');
                });
                btn.classList.add('text-tertiary-fixed', 'font-bold');
                btn.classList.remove('text-on-surface-variant/70');
            });
        });
    </script>
<div class="fixed top-0 right-0 h-full w-[380px] z-[100] translate-x-full transition-transform duration-500 ease-in-out flex flex-col bg-white/10 backdrop-blur-[24px] border-l border-white/10 shadow-2xl font-['Geist']" id="floating-dashboard"><div class="p-6 flex justify-between items-center border-b border-white/10"><div class="flex flex-col"><h2 class="text-on-surface font-headline-lg text-[20px] tracking-tight">Architectural Pulse</h2><div class="flex items-center gap-2 mt-1"><span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span><span class="text-[10px] font-mono-precision text-secondary uppercase">System Nominal</span></div></div><button class="p-2 hover:bg-white/10 rounded-full transition-colors" id="dashboard-close"><span class="material-symbols-outlined">close</span></button></div><div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8"><section><div><h3 class="text-on-surface-variant font-label-caps text-[11px] uppercase tracking-widest mb-4">Critical Drift</h3><div class="flex items-baseline gap-2"><span class="text-[48px] font-bold text-error leading-none">1.24%</span><span class="text-error text-[12px] font-medium">+0.05% today</span></div><div class="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden"><div class="h-full bg-error w-[65%] rounded-full shadow-[0_0_12px_rgba(255,180,171,0.4)]"></div></div><p class="mt-2 text-[11px] text-on-surface-variant/60 italic">Threshold: 1.50%</p></div></section><section><h3 class="text-on-surface-variant font-label-caps text-[11px] uppercase tracking-widest mb-4">Awaiting Ratification</h3><div class="space-y-3"><div class="p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"><div class="flex justify-between mb-1"><span class="text-primary font-mono-precision text-[10px]">LOOM_MAINFRAME_B2</span><span class="text-on-surface-variant/40 text-[10px]">4h left</span></div><p class="text-on-surface text-body-sm font-medium">Structural Integrity Check</p></div></div></section></div></div></div>
<script>
    const dashboard = document.getElementById('floating-dashboard');
    const toggleBtn = document.getElementById('dashboard-toggle');
    const closeBtn = document.getElementById('dashboard-close');

    toggleBtn.addEventListener('click', () => {
        dashboard.classList.remove('translate-x-full');
    });

    closeBtn.addEventListener('click', () => {
        dashboard.classList.add('translate-x-full');
    });
</script>
</body></html>