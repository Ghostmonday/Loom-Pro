<!-- Loom Blueprint Workbench - Drift Monitor -->
<!DOCTYPE html>
<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Drift Monitor | Loom Blueprint Workbench</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<!-- Google Fonts: Geist (Sans) and JetBrains Mono -->
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;family=JetBrains+Mono:wght@100..800&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<style>
        body {
            font-family: 'Geist', sans-serif;
            background-color: #131315;
            color: #e4e2e4;
            overflow: hidden;
            margin: 0;
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
        }
        .glass-panel {
            background: rgba(28, 28, 30, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }
        .glass-popover {
            background: rgba(44, 44, 46, 0.9);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 0.5px solid rgba(255, 255, 255, 0.1);
        }
        .chart-grid {
            background-image: 
                linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 40px 40px;
        }
        .drift-line {
            stroke-dasharray: 1000;
            stroke-dashoffset: 1000;
            animation: draw 4s ease-out forwards infinite alternate;
        }
        @keyframes draw {
            to { stroke-dashoffset: 0; }
        }
        .glow-blue { filter: drop-shadow(0 0 8px rgba(71, 226, 102, 0.4)); }
        .glow-tertiary { filter: drop-shadow(0 0 8px rgba(255, 184, 104, 0.4)); }
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
                "on-secondary": "#003910",
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
                "secondary-container": "#09bf49"
            },
            "borderRadius": {
                "DEFAULT": "12px",
                "lg": "12px",
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
          }
        }
      }
    </script>
</head>
<body class="flex flex-col h-screen">
<!-- TopNavBar -->
<header class="bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 shadow-sm flex justify-between items-center px-container-margin w-full h-16 fixed top-0 z-50">
<div class="flex items-center gap-stack-lg">
<span class="font-display-lg text-display-lg font-bold text-primary">Loom Blueprint Workbench</span>
<nav class="hidden md:flex gap-gutter ml-stack-lg items-center">
<span class="text-on-surface-variant font-medium font-body-lg text-body-lg hover:text-primary transition-colors cursor-pointer">Ingest</span>
<span class="text-on-surface-variant/50 material-symbols-outlined">chevron_right</span>
<span class="text-on-surface-variant font-medium font-body-lg text-body-lg hover:text-primary transition-colors cursor-pointer">Pipeline</span>
<span class="text-on-surface-variant/50 material-symbols-outlined">chevron_right</span>
<span class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg">Drift Monitor</span>
</nav>
</div>
<div class="flex items-center gap-gutter">
<div class="relative">
<input class="bg-surface-container-high border-none rounded-full px-stack-lg py-unit text-body-sm font-body-sm w-64 focus:ring-1 focus:ring-primary" placeholder="Search parameters..." type="text"/>
</div>
<button class="text-on-surface-variant hover:text-primary active:scale-95 transition-all"><span class="material-symbols-outlined">help</span></button>
<button class="text-on-surface-variant hover:text-primary active:scale-95 transition-all"><span class="material-symbols-outlined">settings</span></button>
</div>
</header>
<!-- Sidebar & Main Area Wrapper -->
<div class="flex flex-1 pt-16 pb-12 overflow-hidden">
<!-- SideNavBar (Left Tool Dock) -->
<aside class="bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 flex flex-col items-center py-stack-lg space-y-stack-md w-[64px] h-full">
<div class="mb-stack-lg">
<span class="text-on-surface-variant font-label-caps text-[10px] opacity-40">V1.2</span>
</div>
<button class="w-12 h-12 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl active:scale-90 transition-transform duration-200">
<span class="material-symbols-outlined">near_me</span>
</button>
<button class="w-12 h-12 flex items-center justify-center bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)] active:scale-90 transition-transform duration-200">
<span class="material-symbols-outlined">straighten</span>
</button>
<button class="w-12 h-12 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl active:scale-90 transition-transform duration-200">
<span class="material-symbols-outlined">architecture</span>
</button>
<button class="w-12 h-12 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl active:scale-90 transition-transform duration-200">
<span class="material-symbols-outlined">layers</span>
</button>
<button class="w-12 h-12 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl active:scale-90 transition-transform duration-200">
<span class="material-symbols-outlined">visibility</span>
</button>
</aside>
<!-- Main Viewport (The Canvas) -->
<main class="flex-1 relative bg-black chart-grid p-container-margin overflow-hidden">
<!-- Floating HUD Controls -->
<div class="absolute top-container-margin left-container-margin z-10 flex gap-stack-md">
<div class="glass-popover px-stack-lg py-stack-md rounded-lg flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant/70">METRIC TYPE</span>
<span class="font-title-md text-title-md text-primary">Delta-Kappa Drift</span>
</div>
<div class="glass-popover px-stack-lg py-stack-md rounded-lg flex flex-col">
<span class="font-label-caps text-label-caps text-on-surface-variant/70">SYSTEM STATUS</span>
<span class="font-title-md text-title-md text-secondary flex items-center gap-unit">
<span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
                        Nominal Trace
                    </span>
</div>
</div>
<div class="absolute top-container-margin right-container-margin z-10">
<button class="glass-popover px-stack-lg py-stack-md rounded-lg text-on-surface hover:text-primary active:scale-95 transition-all flex items-center gap-unit">
<span class="material-symbols-outlined">calendar_today</span>
<span class="font-body-sm text-body-sm">Last 24 Hours</span>
</button>
</div>
<!-- The Chart Area -->
<div class="w-full h-full flex flex-col justify-end pb-stack-lg relative">
<!-- Drift Threshold Lines -->
<div class="absolute w-full h-px bg-error/30 top-1/4 border-t border-dashed border-error flex items-center">
<span class="bg-error text-on-error px-2 py-0.5 rounded-full font-label-caps text-[10px] -ml-2">STAGE 3: REJECTION</span>
</div>
<div class="absolute w-full h-px bg-primary/30 top-1/2 border-t border-dashed border-primary flex items-center">
<span class="bg-primary-container text-on-primary-container px-2 py-0.5 rounded-full font-label-caps text-[10px] -ml-2">STAGE 2: LOCK</span>
</div>
<div class="absolute w-full h-px bg-tertiary/30 top-3/4 border-t border-dashed border-tertiary flex items-center">
<span class="bg-tertiary text-on-tertiary px-2 py-0.5 rounded-full font-label-caps text-[10px] -ml-2">STAGE 1: WARNING</span>
</div>
<!-- SVG Line Chart (Simulated Data) -->
<svg class="w-full h-full drop-shadow-2xl" viewbox="0 0 1000 400">
<defs>
<lineargradient id="driftGradient" x1="0%" x2="0%" y1="0%" y2="100%">
<stop offset="0%" stop-color="rgba(255, 180, 171, 0.2)"></stop>
<stop offset="100%" stop-color="rgba(170, 199, 255, 0)"></stop>
</lineargradient>
</defs>
<path class="drift-line" d="M0,350 Q100,320 200,360 T400,300 T600,240 T800,280 T1000,150" fill="none" stroke="#aac7ff" stroke-width="3"></path>
<path d="M0,350 Q100,320 200,360 T400,300 T600,240 T800,280 T1000,150 L1000,400 L0,400 Z" fill="url(#driftGradient)"></path>
<!-- Data points -->
<circle class="glow-tertiary" cx="200" cy="360" fill="#ffb868" r="4"></circle>
<circle class="glow-blue" cx="600" cy="240" fill="#47e266" r="4"></circle>
<circle cx="1000" cy="150" fill="#ffb4ab" r="6"></circle>
</svg>
<!-- Primary Action Button Floating -->
<div class="absolute bottom-stack-lg left-1/2 -translate-x-1/2 z-20">
<button class="bg-primary text-on-primary px-container-margin py-stack-lg rounded-xl font-title-md text-title-md shadow-lg active:scale-95 transition-transform flex items-center gap-stack-md group">
<span class="material-symbols-outlined group-hover:rotate-180 transition-transform duration-500">sync_alt</span>
                        Open Automated Refactoring Panel
                    </button>
</div>
</div>
</main>
<!-- Inspector (Right Panel) -->
<aside class="w-[320px] bg-surface-container-low/80 backdrop-blur-xl border-l border-outline-variant/30 flex flex-col p-panel-padding">
<div class="flex items-center justify-between mb-stack-lg">
<h2 class="font-title-md text-title-md">Inspector</h2>
<span class="material-symbols-outlined text-on-surface-variant cursor-pointer">close</span>
</div>
<div class="space-y-stack-lg">
<!-- Layer Info -->
<div class="bg-surface-container-high/50 p-stack-md rounded-lg border border-outline-variant/20">
<span class="font-label-caps text-label-caps text-on-surface-variant/70 block mb-unit">SELECTED ENTITY</span>
<div class="flex items-center gap-unit">
<span class="material-symbols-outlined text-primary">database</span>
<span class="font-body-lg text-body-lg">K-Sigma Pipeline 4</span>
</div>
</div>
<!-- Parameters -->
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-stack-md">CONFIGURATION</span>
<div class="space-y-stack-sm">
<div class="flex justify-between items-center py-unit border-b border-outline-variant/10">
<span class="font-body-sm text-body-sm text-on-surface-variant">Window Size</span>
<span class="font-mono-precision text-mono-precision text-secondary">2048 ms</span>
</div>
<div class="flex justify-between items-center py-unit border-b border-outline-variant/10">
<span class="font-body-sm text-body-sm text-on-surface-variant">Precision</span>
<span class="font-mono-precision text-mono-precision text-secondary">IEEE 754</span>
</div>
<div class="flex justify-between items-center py-unit border-b border-outline-variant/10">
<span class="font-body-sm text-body-sm text-on-surface-variant">Auto-Correct</span>
<span class="bg-secondary-container/20 text-on-secondary-container px-2 py-0.5 rounded text-[10px]">ENABLED</span>
</div>
</div>
</div>
<!-- Active Alerts -->
<div>
<span class="font-label-caps text-label-caps text-on-surface-variant block mb-stack-md">ACTIVE ANOMALIES</span>
<div class="space-y-stack-md">
<div class="glass-popover p-stack-md rounded-lg border-l-4 border-tertiary">
<p class="font-body-sm text-body-sm font-bold">Latency Variance</p>
<p class="font-body-sm text-[12px] text-on-surface-variant">Detected slight drift in kappa normalization. Threshold exceeded by 4.2%.</p>
</div>
<div class="glass-popover p-stack-md rounded-lg border-l-4 border-error">
<p class="font-body-sm text-body-sm font-bold">Node Desync</p>
<p class="font-body-sm text-[12px] text-on-surface-variant">External node cluster reporting 200ms lag. Imminent Stage 3 Rejection.</p>
</div>
</div>
</div>
</div>
</aside>
</div>
<!-- BottomNavBar (Console Area) -->
<footer class="bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30 fixed bottom-0 left-0 w-full h-12 z-50 flex justify-center space-x-gutter items-center px-container-margin shadow-[0_-8px_32px_rgba(0,0,0,0.5)]">
<div class="flex-1 flex gap-gutter items-center">
<span class="font-mono-precision text-mono-precision text-on-surface-variant/70 flex items-center gap-unit">
<span class="material-symbols-outlined text-[16px]">terminal</span>
                SYS_MON_READY
            </span>
<div class="h-4 w-px bg-outline-variant/30"></div>
<span class="font-mono-precision text-mono-precision text-secondary">ACTIVE_NODES: 14</span>
</div>
<div class="flex items-center space-x-gutter">
<button class="text-tertiary-fixed font-bold flex flex-col items-center group font-mono-precision text-mono-precision">
<span class="material-symbols-outlined group-hover:scale-110 transition-transform">terminal</span>
                Logs
            </button>
<button class="text-on-surface-variant/70 flex flex-col items-center group font-mono-precision text-mono-precision hover:text-on-surface transition-colors">
<span class="material-symbols-outlined group-hover:scale-110 transition-transform">play_circle</span>
                Timeline
            </button>
<button class="text-on-surface-variant/70 flex flex-col items-center group font-mono-precision text-mono-precision hover:text-on-surface transition-colors">
<span class="material-symbols-outlined group-hover:scale-110 transition-transform">description</span>
                Output
            </button>
<button class="text-on-surface-variant/70 flex flex-col items-center group font-mono-precision text-mono-precision hover:text-on-surface transition-colors">
<span class="material-symbols-outlined group-hover:scale-110 transition-transform">bug_report</span>
                Debug
            </button>
</div>
<div class="flex-1 flex justify-end gap-stack-lg items-center">
<span class="font-mono-precision text-mono-precision text-on-surface-variant/50">CPU: 24%</span>
<span class="font-mono-precision text-mono-precision text-on-surface-variant/50">RAM: 4.2GB</span>
</div>
<button class="absolute right-container-margin -top-16 w-12 h-12 bg-primary text-on-primary rounded-full shadow-lg flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50 group" id="dashboard-toggle" title="Architectural Pulse"><span class="material-symbols-outlined">dashboard</span></button></footer>
<!-- Micro-interaction Script -->
<script>
        document.querySelectorAll('button').forEach(button => {
            button.addEventListener('mousedown', () => {
                button.style.transform = 'scale(0.95)';
            });
            button.addEventListener('mouseup', () => {
                button.style.transform = '';
            });
            button.addEventListener('mouseleave', () => {
                button.style.transform = '';
            });
        });

        // Simple real-time console log simulation
        const consoleMsg = document.querySelector('.flex-1.flex.gap-gutter.items-center span:first-child');
        const statuses = ["READY", "POLLING", "SYNCHRONIZING", "MONITORING", "ANALYZING"];
        let statusIndex = 0;
        setInterval(() => {
            statusIndex = (statusIndex + 1) % statuses.length;
            consoleMsg.innerHTML = `<span class="material-symbols-outlined text-[16px]">terminal</span> SYS_MON_${statuses[statusIndex]}`;
        }, 5000);
    </script>
<aside class="fixed top-0 right-0 h-full w-[380px] translate-x-full transition-transform duration-500 ease-in-out z-[60] flex flex-col font-body-lg" id="floating-dashboard" style="background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-left: 1px solid rgba(255, 255, 255, 0.1);"><div class="p-container-margin flex flex-col h-full gap-gutter overflow-y-auto custom-scrollbar"><div class="flex items-center justify-between mb-stack-md"><div class="flex flex-col"><h2 class="font-headline-lg text-title-md text-on-surface">Architectural Pulse</h2><div class="flex items-center gap-unit text-[12px] text-secondary"><span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>System Nominal</div></div><button class="p-2 hover:bg-white/10 rounded-full transition-colors" id="dashboard-close"><span class="material-symbols-outlined">close</span></button></div><div class="bg-white/5 rounded-xl p-panel-padding border border-white/10"><span class="font-label-caps text-[10px] text-on-surface-variant/70 block mb-unit uppercase tracking-widest">Critical Drift</span><div class="flex items-baseline gap-stack-sm"><span class="text-display-lg text-[32px] text-error font-bold">1.24%</span><span class="text-error text-[12px]">+0.05% today</span></div><div class="mt-stack-sm h-1 w-full bg-white/10 rounded-full overflow-hidden"><div class="h-full bg-error w-[65%]"></div></div></div><div class="flex flex-col gap-stack-md"><span class="font-label-caps text-[10px] text-on-surface-variant/70 uppercase tracking-widest">Awaiting Ratification</span><div class="space-y-stack-sm"><div class="bg-white/5 p-stack-md rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer"><div class="flex justify-between text-[11px] font-mono-precision text-primary mb-1"><span>LOOM_MAINFRAME_B2</span><span class="text-on-surface-variant/60">4h left</span></div><div class="text-body-sm">Structural Integrity Check</div></div></div></div></div></div></aside>
<script>
    const dashboardToggle = document.getElementById('dashboard-toggle');
    const dashboardClose = document.getElementById('dashboard-close');
    const dashboardPanel = document.getElementById('floating-dashboard');

    dashboardToggle.addEventListener('click', () => {
        dashboardPanel.classList.remove('translate-x-full');
    });

    dashboardClose.addEventListener('click', () => {
        dashboardPanel.classList.add('translate-x-full');
    });
</script>
</body></html>