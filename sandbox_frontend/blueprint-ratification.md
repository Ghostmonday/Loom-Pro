<!-- Loom Blueprint Workbench - Blueprint Ratification -->
<!DOCTYPE html>
<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Blueprint Ratification | Loom Blueprint Workbench</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/geist@1.3.0/dist/fonts/geist.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/jetbrains-mono@1.0.6/css/jetbrains-mono.min.css" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;display=swap" rel="stylesheet"/>
<style>
        :root {
            --glass-bg: rgba(28, 28, 30, 0.8);
            --glass-border: rgba(255, 255, 255, 0.05);
            --electric-blue: #3e90ff;
        }
        body {
            background-color: #000000;
            color: #e4e2e4;
            overflow: hidden;
            font-family: 'Geist', sans-serif;
        }
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 0.5px solid var(--glass-border);
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
        }
        .chart-gradient {
            background: linear-gradient(to top, rgba(170, 199, 255, 0.1), transparent);
        }
        .frosted-overlay {
            background: rgba(170, 199, 255, 0.05);
            backdrop-filter: blur(4px);
            border-left: 1px dashed rgba(170, 199, 255, 0.3);
            border-right: 1px dashed rgba(170, 199, 255, 0.3);
        }
        .spring-transition {
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
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
                        "background": "#131315",
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
                        "lg": "0.5rem",
                        "xl": "12px",
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
                        "mono-precision": ["jetbrainsMono"],
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
                },
            },
        }
    </script>
</head>
<body class="h-screen flex flex-col">
<!-- TopNavBar -->
<header class="flex justify-between items-center px-container-margin w-full h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 z-50">
<div class="flex items-center space-x-gutter">
<span class="font-display-lg text-display-lg font-bold text-primary">Loom Blueprint Workbench</span>
<nav class="hidden md:flex space-x-6 ml-8">
<span class="text-on-surface-variant font-medium hover:text-primary transition-colors cursor-pointer font-body-lg text-body-lg">Ingest</span>
<span class="text-on-surface-variant font-medium hover:text-primary transition-colors cursor-pointer font-body-lg text-body-lg">Processing</span>
<span class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg">Blueprint Ratification</span>
</nav>
</div>
<div class="flex items-center space-x-4">
<div class="relative">
<input class="bg-surface-container-high border-none rounded-xl px-4 py-1.5 text-body-sm w-64 focus:ring-1 focus:ring-primary" placeholder="Search parameters..." type="text"/>
<span class="material-symbols-outlined absolute right-3 top-2 text-on-surface-variant text-sm">search</span>
</div>
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer active:scale-95 transition-transform">settings</span>
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer active:scale-95 transition-transform">help</span>
</div>
</header>
<div class="flex flex-1 overflow-hidden relative">
<!-- SideNavBar (Left Rail) -->
<aside class="flex flex-col items-center py-stack-lg space-y-stack-md bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 h-full w-[64px] z-40">
<div class="group flex flex-col items-center space-y-4">
<div class="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-xl cursor-pointer active:scale-90 transition-all">
<span class="material-symbols-outlined">near_me</span>
</div>
<div class="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-xl cursor-pointer active:scale-90 transition-all">
<span class="material-symbols-outlined">straighten</span>
</div>
<div class="p-2 bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)] cursor-pointer active:scale-90 transition-all">
<span class="material-symbols-outlined">architecture</span>
</div>
<div class="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-xl cursor-pointer active:scale-90 transition-all">
<span class="material-symbols-outlined">layers</span>
</div>
<div class="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-xl cursor-pointer active:scale-90 transition-all">
<span class="material-symbols-outlined">visibility</span>
</div>
</div>
</aside>
<!-- Main Content Area -->
<main class="flex-1 p-container-margin overflow-y-auto relative">
<div class="max-w-6xl mx-auto space-y-stack-lg">
<!-- Header Stats -->
<div class="flex justify-between items-end mb-8">
<div>
<h1 class="font-headline-lg text-headline-lg text-on-surface">Modularity Optimization Reporting</h1>
<p class="text-on-surface-variant font-body-lg text-body-lg">Structural Modularity (Q) Plateau &amp; Ratification Thresholds</p>
</div>
<div class="flex space-x-6 text-right">
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant">CURRENT Q</p>
<p class="font-mono-precision text-mono-precision text-primary text-2xl">0.842</p>
</div>
<div>
<p class="font-label-caps text-label-caps text-on-surface-variant">OPTIMAL THRESHOLD</p>
<p class="font-mono-precision text-mono-precision text-secondary text-2xl">0.68 - 0.74</p>
</div>
</div>
</div>
<!-- Bento Grid Chart Section -->
<div class="grid grid-cols-12 gap-gutter">
<!-- Main Plateau Chart -->
<div class="col-span-12 glass-panel rounded-xl p-6 h-[420px] relative overflow-hidden group">
<div class="absolute inset-0 chart-gradient"></div>
<!-- Y Axis -->
<div class="absolute left-6 top-10 bottom-12 flex flex-col justify-between text-on-surface-variant font-mono-precision text-[10px]">
<span>1.0</span><span>0.8</span><span>0.6</span><span>0.4</span><span>0.2</span><span>0.0</span>
</div>
<!-- Chart Canvas Placeholder Logic (CSS based) -->
<div class="absolute inset-0 ml-16 mr-6 mb-12 mt-10">
<!-- Frosted Overlay / Optimal Zone -->
<div class="absolute left-[65%] right-[20%] top-0 bottom-0 frosted-overlay z-10 flex items-start justify-center pt-4">
<span class="font-label-caps text-label-caps text-primary opacity-60">Target Modularity Plateau (Q<sub>packet</sub>)</span>
</div>
<!-- SVG Chart Path -->
<svg class="w-full h-full overflow-visible" viewbox="0 0 800 300">
<defs>
<lineargradient id="line-grad" x1="0%" x2="100%" y1="0%" y2="0%">
<stop offset="0%" style="stop-color:rgba(170, 199, 255, 0.2)"></stop>
<stop offset="50%" style="stop-color:rgba(170, 199, 255, 1)"></stop>
<stop offset="100%" style="stop-color:rgba(71, 226, 102, 1)"></stop>
</lineargradient>
<filter id="glow">
<fegaussianblur result="coloredBlur" stddeviation="3"></fegaussianblur>
<femerge>
<femergenode in="coloredBlur"></femergenode><femergenode in="SourceGraphic"></femergenode>
</femerge>
</filter>
</defs>
<!-- The Line -->
<path d="M 0 280 Q 100 260 200 200 T 400 120 T 600 80 L 800 70" fill="none" filter="url(#glow)" stroke="url(#line-grad)" stroke-width="3"></path>
<!-- Points -->
<circle cx="200" cy="200" fill="#3e90ff" r="4"></circle>
<circle cx="400" cy="120" fill="#3e90ff" r="4"></circle>
<circle cx="550" cy="85" fill="#47e266" r="6"></circle>
</svg>
</div>
<!-- X Axis -->
<div class="absolute bottom-6 left-16 right-6 flex justify-between text-on-surface-variant font-mono-precision text-[10px]">
<span>0.1</span><span>0.3</span><span>0.5</span><span>0.7</span><span>0.9</span>
</div>
</div>
<!-- Secondary Insights -->
<div class="col-span-4 glass-panel rounded-xl p-4 flex flex-col justify-between">
<div>
<h3 class="font-title-md text-title-md text-on-surface mb-2">Node Density</h3>
<p class="text-body-sm text-on-surface-variant">Clustering coefficient maintains stable growth at current thresholds.</p>
</div>
<div class="h-16 w-full bg-surface-container rounded flex items-end px-2 pb-2 space-x-1">
<div class="bg-primary w-full h-[40%] rounded-t-sm"></div>
<div class="bg-primary w-full h-[55%] rounded-t-sm"></div>
<div class="bg-primary w-full h-[85%] rounded-t-sm"></div>
<div class="bg-primary w-full h-[60%] rounded-t-sm"></div>
<div class="bg-secondary w-full h-[95%] rounded-t-sm"></div>
</div>
</div>
<div class="col-span-8 glass-panel rounded-xl p-4 relative overflow-hidden">
<div class="flex justify-between items-center mb-4">
<h3 class="font-title-md text-title-md text-on-surface">Ratification Readiness</h3>
<span class="bg-secondary/10 text-secondary px-3 py-1 rounded-full text-label-caps font-label-caps border border-secondary/20">READY</span>
</div>
<div class="space-y-3">
<div class="flex justify-between items-center">
<span class="text-body-sm text-on-surface-variant">Graph Structural Integrity</span>
<div class="w-1/2 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-primary w-[92%]"></div>
</div>
</div>
<div class="flex justify-between items-center">
<span class="text-body-sm text-on-surface-variant">Intent Alignment</span>
<div class="w-1/2 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-primary w-[88%]"></div>
</div>
</div>
<div class="flex justify-between items-center">
<span class="text-body-sm text-on-surface-variant">Enforcement Matching</span>
<div class="w-1/2 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-secondary w-[100%]"></div>
</div>
</div>
</div>
</div>
</div>
<!-- Primary Action Section -->
<div class="flex flex-col items-center py-12 space-y-6">
<p class="text-on-surface-variant text-center max-w-lg font-body-lg text-body-lg">
                        Finalize the structural transformation and commit the current modularity configuration to the permanent ledger. This action is immutable.
                    </p>
<button class="bg-primary-container text-on-primary-container px-8 py-4 rounded-xl font-title-md text-title-md font-bold shadow-[0_8px_32px_rgba(62,144,255,0.3)] hover:scale-105 active:scale-95 spring-transition">
                        Submit Blueprint for Formal Ratification
                    </button>
</div>
</div>
</main>
<!-- Inspector (Right Rail) -->
<aside class="hidden lg:flex flex-col w-[320px] bg-surface-container-low/80 backdrop-blur-xl border-l border-outline-variant/30 z-40">
<div class="p-container-margin border-b border-outline-variant/30">
<h2 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Inspector</h2>
<p class="text-label-caps font-label-caps text-on-surface-variant">Active Parameters</p>
</div>
<div class="flex-1 overflow-y-auto p-panel-padding space-y-6">
<!-- Collapsible Sections -->
<section>
<div class="flex justify-between items-center mb-4">
<span class="font-title-md text-title-md text-on-surface">Blueprint Meta</span>
<span class="material-symbols-outlined text-on-surface-variant">expand_more</span>
</div>
<div class="space-y-4">
<div class="p-3 glass-panel rounded-xl">
<label class="font-label-caps text-label-caps text-on-surface-variant">ID</label>
<p class="font-mono-precision text-mono-precision text-primary">LBW-RAT-00249-X</p>
</div>
<div class="p-3 glass-panel rounded-xl">
<label class="font-label-caps text-label-caps text-on-surface-variant">VERSION</label>
<p class="font-mono-precision text-mono-precision">v1.2.4-Alpha</p>
</div>
<div class="p-3 glass-panel rounded-xl">
<label class="font-label-caps text-label-caps text-on-surface-variant">STABILITY INDEX</label>
<p class="font-mono-precision text-mono-precision text-secondary">0.992</p>
</div>
</div>
</section>
<section>
<div class="flex justify-between items-center mb-4">
<span class="font-title-md text-title-md text-on-surface">Geometric Constraints</span>
<span class="material-symbols-outlined text-on-surface-variant">settings_suggest</span>
</div>
<div class="grid grid-cols-2 gap-2">
<div class="p-2 border border-outline-variant/20 rounded text-center">
<span class="font-label-caps text-[10px] text-on-surface-variant block">MIN RAD</span>
<span class="font-mono-precision text-on-surface">0.12mm</span>
</div>
<div class="p-2 border border-outline-variant/20 rounded text-center">
<span class="font-label-caps text-[10px] text-on-surface-variant block">MAX DEPTH</span>
<span class="font-mono-precision text-on-surface">4.80mm</span>
</div>
<div class="p-2 border border-outline-variant/20 rounded text-center">
<span class="font-label-caps text-[10px] text-on-surface-variant block">TOLERANCE</span>
<span class="font-mono-precision text-on-surface">±0.001</span>
</div>
<div class="p-2 border border-outline-variant/20 rounded text-center">
<span class="font-label-caps text-[10px] text-on-surface-variant block">WEIGHT</span>
<span class="font-mono-precision text-on-surface">2.4kg</span>
</div>
</div>
</section>
<section>
<h3 class="font-title-md text-title-md text-on-surface mb-4">Preview</h3>
<div class="aspect-square glass-panel rounded-xl overflow-hidden relative group">
<div class="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent"></div>
<img class="w-full h-full object-cover mix-blend-screen opacity-80 group-hover:scale-110 transition-transform duration-700" data-alt="A highly detailed 3D technical blueprint visualization of a complex mechanical part rendered in a dark CAD software style. The object is illuminated by cool blue neon lights that highlight its precision edges and metallic textures. Soft atmospheric shadows and a faint grid background enhance the high-end industrial engineering aesthetic. The rendering is sharp, clean, and professional." src="https://lh3.googleusercontent.com/aida-public/AB6AXuD4v96nCX7X_MUINHwVbyDqL-CZhYbUdDv9WcY-a7KDXE3RCBZgpzCmkaUQnhtMOM4NK7VqtevKp4VtirjC8GWmjJKjCsmf42DsMbKR3OuQEVpRkTYcHm9Te-6gjoFiQ03YcR88Sn-FXXO0zTeZjgiOgmLN4aFy3QvEbnjF45SBqsNRjAeASUdDgReb1Lr_Et-7G9MmRjRMFYTuCBnQq9KJyuZzZ-RlM3Bu_5mdkvpjoujO_37BQDdgBGfqHD4rnPnnlhsJA7v-LaQ"/>
<div class="absolute bottom-2 right-2 flex space-x-1">
<div class="w-2 h-2 bg-secondary rounded-full animate-pulse"></div>
<span class="text-[10px] font-label-caps text-secondary">LIVE FEED</span>
</div>
</div>
</section>
</div>
</aside>
</div>
<!-- BottomNavBar (Console) -->
<footer class="fixed bottom-0 left-0 w-full h-12 z-50 flex justify-center space-x-gutter items-center px-container-margin bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30 shadow-[0_-8px_32px_rgba(0,0,0,0.5)]">
<div class="flex-1 flex items-center space-x-4">
<span class="material-symbols-outlined text-secondary text-sm">terminal</span>
<span class="font-mono-precision text-mono-precision text-on-surface-variant/70 text-[11px]">System ready. Modularity plateau reached. Optimization complete.</span>
</div>
<div class="flex space-x-8">
<div class="text-on-surface-variant/70 flex flex-col items-center group cursor-pointer hover:text-on-surface transition-colors">
<span class="material-symbols-outlined text-[18px]">terminal</span>
<span class="font-mono-precision text-[9px] uppercase tracking-wider mt-1">Logs</span>
</div>
<div class="text-tertiary-fixed font-bold flex flex-col items-center group cursor-pointer">
<span class="material-symbols-outlined text-[18px]">play_circle</span>
<span class="font-mono-precision text-[9px] uppercase tracking-wider mt-1">Timeline</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center group cursor-pointer hover:text-on-surface transition-colors">
<span class="material-symbols-outlined text-[18px]">description</span>
<span class="font-mono-precision text-[9px] uppercase tracking-wider mt-1">Output</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center group cursor-pointer hover:text-on-surface transition-colors">
<span class="material-symbols-outlined text-[18px]">bug_report</span>
<span class="font-mono-precision text-[9px] uppercase tracking-wider mt-1">Debug</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center group cursor-pointer hover:text-primary transition-colors" id="dashboard-toggle">
<span class="material-symbols-outlined text-[18px]">dashboard</span>
<span class="font-mono-precision text-[9px] uppercase tracking-wider mt-1">Pulse</span>
</div></div>
<div class="flex-1 flex justify-end space-x-4 items-center">
<span class="font-mono-precision text-[10px] text-on-surface-variant/50">CPU: 14%</span>
<span class="font-mono-precision text-[10px] text-on-surface-variant/50">RAM: 4.2GB</span>
</div>
</footer>
<script>
        // Micro-interactions and effects
        document.querySelectorAll('.active\\:scale-95').forEach(button => {
            button.addEventListener('mousedown', () => {
                button.style.transform = 'scale(0.95)';
            });
            button.addEventListener('mouseup', () => {
                button.style.transform = 'scale(1)';
            });
        });

        // Simulating some console updates
        const consoleText = document.querySelector('footer span.font-mono-precision');
        const statusLogs = [
            "Calculating eigenvector centrality...",
            "Analyzing community structure...",
            "Validating partition integrity...",
            "Modularity plateau confirmed.",
            "Ratification protocols active."
        ];
        let logIndex = 0;
        setInterval(() => {
            logIndex = (logIndex + 1) % statusLogs.length;
            consoleText.style.opacity = 0;
            setTimeout(() => {
                consoleText.innerText = statusLogs[logIndex];
                consoleText.style.opacity = 0.7;
            }, 300);
        }, 5000);
    </script>
<div class="fixed top-0 right-0 h-full w-[380px] z-[100] translate-x-full transition-transform duration-500 ease-in-out flex flex-col" id="floating-dashboard">
<div class="h-full m-4 rounded-xl border border-white/10 bg-white/10 backdrop-blur-[24px] shadow-2xl flex flex-col overflow-hidden">
<!-- Header -->
<div class="p-6 border-b border-white/10 flex justify-between items-center">
<div>
<h2 class="font-headline-lg-mobile text-on-surface">Architectural Pulse</h2>
<div class="flex items-center gap-2 mt-1">
<span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
<span class="text-[10px] font-label-caps text-secondary uppercase tracking-widest">System Nominal</span>
</div>
</div>
<button class="p-2 hover:bg-white/10 rounded-full transition-colors" id="close-dashboard">
<span class="material-symbols-outlined text-on-surface-variant">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
<!-- Critical Drift Section -->
<section>
<h3 class="text-label-caps text-on-surface-variant/50 uppercase mb-4">Critical Drift</h3>
<div class="p-4 rounded-xl bg-white/5 border border-white/5">
<div class="flex items-baseline gap-2">
<span class="text-4xl font-bold text-error">1.24%</span>
<span class="text-xs text-error/70">+0.05% today</span>
</div>
<div class="mt-4 h-1 w-full bg-white/10 rounded-full overflow-hidden">
<div class="h-full bg-error w-[65%]"></div>
</div>
</div>
</section>
<!-- Awaiting Ratification -->
<section>
<h3 class="text-label-caps text-on-surface-variant/50 uppercase mb-4">Awaiting Ratification</h3>
<div class="space-y-3">
<div class="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center">
<span class="font-mono-precision text-xs text-primary">LOOM_MAINFRAME_B2</span>
<span class="text-[10px] text-on-surface-variant">4h left</span>
</div>
<div class="p-3 rounded-lg bg-white/5 border border-white/5 flex justify-between items-center">
<span class="font-mono-precision text-xs text-primary">CORE_EXPANSION_P7</span>
<span class="text-[10px] text-on-surface-variant">6h left</span>
</div>
</div>
</section>
<!-- Contextual Activity -->
<section>
<h3 class="text-label-caps text-on-surface-variant/50 uppercase mb-4">Recent Activity</h3>
<div class="space-y-4">
<div class="flex gap-3">
<div class="w-1 h-8 bg-secondary rounded-full"></div>
<div>
<p class="text-sm text-on-surface">Forge Module optimized Hyperion_V4</p>
<span class="text-[10px] text-on-surface-variant/50 uppercase">12m ago</span>
</div>
</div>
<div class="flex gap-3">
<div class="w-1 h-8 bg-primary rounded-full"></div>
<div>
<p class="text-sm text-on-surface">Engine Core corrected sector 7G</p>
<span class="text-[10px] text-on-surface-variant/50 uppercase">45m ago</span>
</div>
</div>
</div>
</section>
</div>
</div>
</div><script>
    const dashboard = document.getElementById('floating-dashboard');
    const toggleBtn = document.getElementById('dashboard-toggle');
    const closeBtn = document.getElementById('close-dashboard');

    toggleBtn.addEventListener('click', () => {
        dashboard.classList.remove('translate-x-full');
    });

    closeBtn.addEventListener('click', () => {
        dashboard.classList.add('translate-x-full');
    });
</script></body></html>