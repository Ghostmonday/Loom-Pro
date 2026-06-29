<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Loom Blueprint Workbench - Project Hub</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;display=swap" rel="stylesheet"/>
    <style>
        @font-face {
            font-family: 'Geist';
            src: url('https://cdn.jsdelivr.net/npm/geist@1.0.0/dist/fonts/geist-sans/Geist-Regular.woff2') format('woff2');
        }
        @font-face {
            font-family: 'jetbrainsMono';
            src: url('https://cdn.jsdelivr.net/npm/@fontsource/jet-brains-mono@5.0.0/files/jet-brains-mono-latin-400-normal.woff2') format('woff2');
        }
        body {
            font-family: 'Geist', sans-serif;
            background-color: #000000;
            color: #e4e2e4;
            overflow: hidden;
        }
        .glass-panel {
            background: rgba(28, 28, 30, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 0.5px solid rgba(255, 255, 255, 0.1);
        }
        .glass-card {
            background: rgba(44, 44, 46, 0.4);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 0.5px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass-card:hover {
            background: rgba(44, 44, 46, 0.6);
            border-color: rgba(170, 199, 255, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
        }
        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
    </style>

<body class="bg-background text-on-background h-screen flex flex-col overflow-hidden">
<!-- Background Shader -->

<!-- TopNavBar -->
<header class="bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 shadow-sm flex justify-between items-center px-container-margin w-full h-16 fixed top-0 z-50">
<div class="flex items-center gap-stack-lg">
<span class="font-display-lg text-[24px] font-bold text-primary tracking-tighter">Loom Blueprint Workbench</span>
<nav class="hidden md:flex items-center gap-stack-lg ml-gutter">
<a class="text-on-surface-variant font-medium hover:text-primary transition-colors font-body-lg text-body-lg" href="#">Manifolds</a>
<a class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg" href="#">Blueprints</a>
<a class="text-on-surface-variant font-medium hover:text-primary transition-colors font-body-lg text-body-lg" href="#">Archive</a>
</nav>
</div>
<div class="flex items-center gap-stack-lg">
<div class="relative group">
<input class="bg-surface-container-high/50 border border-outline-variant/30 rounded-full px-4 py-1.5 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-primary transition-all" placeholder="Search blueprints..." type="text"/>
<span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">search</span>
</div>
<div class="flex items-center gap-stack-md">
<button class="p-2 text-on-surface-variant hover:text-primary transition-colors active:scale-95 duration-200">
<span class="material-symbols-outlined">help</span>
</button>
<button class="p-2 text-on-surface-variant hover:text-primary transition-colors active:scale-95 duration-200">
<span class="material-symbols-outlined">settings</span>
</button>
<div class="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center overflow-hidden ml-stack-sm">
<img class="w-full h-full object-cover" data-alt="A professional close-up headshot of a software engineer with glasses, soft studio lighting, focused gaze, minimalist background, 8k resolution, high contrast, neutral colors." src="https://lh3.googleusercontent.com/aida-public/AB6AXuDmG9G2tohcWqyeYpXnWrTZ371cBwh2hzNFSaAZ3vYxpOsVQbmKXDIi7mP2iPagZQUkBq8OIR_cHVCdLiKfDFa7WV8wRQQQkv1-mRvgPDgHrIiZRZ4PhZULUYJPyv_IscF9MsHgl2lv2AqVCkenDDgS58ceogbsSPZ6Vc7mutWrPBl6sA7qd_oojn7VprnRCPvVjAA-BRYofCdVp3rxcbYvN_D_lyMQif6ZSXiLspHv_NwptEAOGBWHYSRBeiyUTbjuoEIge58pubU"/>
</div>
</div>
</div>
</header>
<div class="flex flex-1 pt-16 overflow-hidden relative z-10">
<!-- SideNavBar -->
<aside class="bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 flex flex-col items-center py-stack-lg space-y-stack-md w-[64px] h-full shrink-0">
<div class="flex flex-col items-center gap-stack-lg w-full">
<!-- Active Tool -->
<button class="w-10 h-10 flex items-center justify-center bg-secondary-container text-on-secondary-container rounded-xl transition-all" title="Navigate">
<span class="material-symbols-outlined">near_me</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all" title="Inspect">
<span class="material-symbols-outlined">straighten</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all" title="Graph Layout">
<span class="material-symbols-outlined">architecture</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all" title="Boundaries">
<span class="material-symbols-outlined">layers</span>
</button>
<button class="w-10 h-10 flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all" title="Visibility">
<span class="material-symbols-outlined">visibility</span>
</button>
</div>
<div class="mt-auto flex flex-col items-center gap-stack-lg">
<span class="font-label-caps text-[10px] text-on-surface-variant/50 tracking-widest vertical-rl rotate-180 mb-stack-lg">V1.2</span>
</div>
</aside>
<!-- Main Content Area -->
<main class="flex-1 p-container-margin overflow-y-auto custom-scrollbar flex flex-col gap-gutter">
<!-- Hero Section -->
<section class="mb-gutter">
<h1 class="font-display-lg text-display-lg text-primary mb-stack-md">Architectural Project Hub</h1>
<p class="text-on-surface-variant font-body-lg max-w-2xl opacity-80">Synchronized with active codebases. All structural analysis modules are operational.</p>
</section>
<!-- Quick Actions Grid -->
<section class="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-stack-lg">
<div class="glass-card p-panel-padding rounded-xl flex flex-col gap-stack-md cursor-pointer group">
<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
<span class="material-symbols-outlined">folder_open</span>
</div>
<div>
<h3 class="font-title-md text-on-surface">Open Existing Blueprint</h3>
<p class="text-on-surface-variant text-body-sm">Browse local files or graph store.</p>
</div>
</div>
<div class="glass-card p-panel-padding rounded-xl flex flex-col gap-stack-md cursor-pointer group">
<div class="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary border border-secondary/20">
<span class="material-symbols-outlined">cloud_download</span>
</div>
<div>
<h3 class="font-title-md text-on-surface">Import Code Repository</h3>
<p class="text-on-surface-variant text-body-sm">Parse project source code via git.</p>
</div>
</div>
<div class="glass-card p-panel-padding rounded-xl flex flex-col gap-stack-md cursor-pointer group">
<div class="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary border border-tertiary/20">
<span class="material-symbols-outlined">add_circle</span>
</div>
<div>
<h3 class="font-title-md text-on-surface">Create New Manifold Mapping</h3>
<p class="text-on-surface-variant text-body-sm">Build canvas from custom intent entries.</p>
</div>
</div>
<div class="glass-card p-panel-padding rounded-xl flex flex-col gap-stack-md cursor-pointer group">
<div class="w-10 h-10 rounded-lg bg-on-surface-variant/10 flex items-center justify-center text-on-surface border border-outline-variant/30">
<span class="material-symbols-outlined">resume</span>
</div>
<div>
<h3 class="font-title-md text-on-surface">Resume Work</h3>
<p class="text-on-surface-variant text-body-sm">Project: Hyperion Analysis.</p>
</div>
</div>
</section>
<!-- Main Dashboard Layout -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
<!-- Left: Recent Projects & Activity -->
<div class="lg:col-span-8 flex flex-col gap-gutter">
<!-- Recent Projects -->
<div class="glass-panel rounded-2xl p-container-margin overflow-hidden relative">
<div class="flex justify-between items-center mb-stack-lg">
<h2 class="font-headline-lg text-headline-lg flex items-center gap-stack-sm">
<span class="material-symbols-outlined text-primary">history</span>
                                Recent Projects
                            </h2>
<button class="text-primary font-label-caps hover:underline">View All</button>
</div>
<div class="flex flex-col divide-y divide-outline-variant/20">
<!-- Project Item 1 -->
<div class="py-stack-lg flex items-center justify-between group hover:bg-white/5 transition-colors px-stack-md -mx-stack-md rounded-lg cursor-pointer">
<div class="flex items-center gap-stack-lg">
<div class="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center border border-outline-variant/30 group-hover:border-primary/50 transition-colors overflow-hidden">
<img class="w-full h-full object-cover opacity-60" data-alt="A macro close-up of a complex topological mesh structure, glowing cyan lines on a dark obsidian surface, high-tech architectural rendering, minimalist CAD style, sharp edges, 8k resolution." src="https://lh3.googleusercontent.com/aida-public/AB6AXuAPI3QxhFdkTVAkbKv1SLypmd07LtNSx6VPSohc93YepNciUFfufguOny3n_H95lHn2YQO-SjUJKOBDqXbtRWGmTXXzy11g9mNngbRjxZpvVoCa_SQ-65_AxJkqn9i7g_ylGjdIAQ17uytH_BXVJe5x3anN8Q-EDTUwOfh2ex6Prl-EqO6qS6SLPUw6HNRurP4XiKduswlznJZYNswG7e9JrifXMfkvl-G5p6rH5Wt6Q5d0gQbJkdDgb4ARP_ti91NMFDhphpxPC2s"/>
</div>
<div>
<div class="font-title-md text-on-surface">Project Hyperion - Manifold Map</div>
<div class="text-body-sm text-on-surface-variant">Analyzed: 14m ago by system</div>
</div>
</div>
<div class="flex items-center gap-gutter">
<span class="px-2 py-0.5 rounded text-[10px] font-mono-precision bg-secondary/10 text-secondary border border-secondary/30 uppercase">Stable</span>
<span class="material-symbols-outlined text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
</div>
</div>
<!-- Project Item 2 -->
<div class="py-stack-lg flex items-center justify-between group hover:bg-white/5 transition-colors px-stack-md -mx-stack-md rounded-lg cursor-pointer">
<div class="flex items-center gap-stack-lg">
<div class="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center border border-outline-variant/30 group-hover:border-primary/50 transition-colors overflow-hidden">
<img class="w-full h-full object-cover opacity-60" data-alt="Abstract 3D architectural wireframe of a spherical data center, glowing orange and deep gold accents, dark tech atmosphere, high precision geometry, CAD blueprint style, 8k render." src="https://lh3.googleusercontent.com/aida-public/AB6AXuDghEza3K3K8OuNyO4MDCfqGJRtxol4BaMsgVirF5-Ql4_LYeA_dH9Kmbd1syMNRBSv0lmLV-bDmVIo6yNMjwt5gECmyRiEWUBbmCzcAG6spX60c9Ij3v57EBKQ6kUukbWJXSz172tNL6EiZM8KSFglIVXE5Ay4EHATG4fjiKwtuuC7RAAhfH7MGZ3wmphm7iPe84tN7_jWy3pbkRo5g9gojTuDwOPS-VZW-IkIsviq-HkMRhl3-HY93ni0ubKfpuOJZrhxbSNm0H0"/>
</div>
<div>
<div class="font-title-md text-on-surface">Sentinel Core Infrastructure</div>
<div class="text-body-sm text-on-surface-variant">Last modified: 2h ago by system</div>
</div>
</div>
<div class="flex items-center gap-gutter">
<span class="px-2 py-0.5 rounded text-[10px] font-mono-precision bg-primary/10 text-primary border border-primary/30 uppercase">Drafting</span>
<span class="material-symbols-outlined text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
</div>
</div>
<!-- Project Item 3 -->
<div class="py-stack-lg flex items-center justify-between group hover:bg-white/5 transition-colors px-stack-md -mx-stack-md rounded-lg cursor-pointer">
<div class="flex items-center gap-stack-lg">
<div class="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center border border-outline-variant/30 group-hover:border-primary/50 transition-colors overflow-hidden">
<img class="w-full h-full object-cover opacity-60" data-alt="Minimalist isometric blueprint of a futuristic city block, neon green grid lines, pitch black background, architectural precision, tech-noir aesthetic, 8k resolution." src="https://lh3.googleusercontent.com/aida-public/AB6AXuCV-7EtrIUOcar0PQ2Ul95uMkefIyL19KIXdeC8valUuuxy3OhE2daA2HC3V90iqJcMGbjuMZ-wFk0-BN2ETHvzH96VumK-7jcVqrVV0nQGefeVtWl-WTR2_ZS1Um6EVn2S-DLgQmREukj6i4ymiMy1oG80UnOnA5uTkHeYjIfGh1fgZQbz99YC6IzkNOSGqG9liT320zHc8rdZmClHg6vxd6uBTwN1SZAWYRNQRVaft2RmCN69ByuTUpXBKIugLak1S-yStAefTJk"/>
</div>
<div>
<div class="font-title-md text-on-surface">Loom Node-01 Expansion</div>
<div class="text-body-sm text-on-surface-variant">Last modified: yesterday by system</div>
</div>
</div>
<div class="flex items-center gap-gutter">
<span class="px-2 py-0.5 rounded text-[10px] font-mono-precision bg-on-surface-variant/10 text-on-surface-variant border border-outline-variant/30 uppercase">Archived</span>
<span class="material-symbols-outlined text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity">chevron_right</span>
</div>
</div>
</div>
</div>
<!-- Recent Activity Feed -->
<div class="glass-panel rounded-2xl p-container-margin">
<h2 class="font-headline-lg text-headline-lg mb-stack-lg flex items-center gap-stack-sm">
<span class="material-symbols-outlined text-secondary">analytics</span>
                            Workbench Activity
                        </h2>
<div class="space-y-stack-lg">
<div class="flex gap-stack-lg items-start relative">
<div class="w-px h-full bg-outline-variant/30 absolute left-[15px] top-8 z-0"></div>
<div class="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0 z-10 border border-secondary/30">
<span class="material-symbols-outlined text-[18px]">bolt</span>
</div>
<div class="flex-1">
<p class="text-on-surface font-body-lg"><strong>Claims Ledger</strong> completed lattice optimization for <span class="text-secondary">Hyperion_V4</span>.</p>
<span class="text-[12px] font-mono-precision text-on-surface-variant/60 uppercase">12m ago • Automated Process</span>
</div>
</div>
<div class="flex gap-stack-lg items-start relative">
<div class="w-px h-full bg-outline-variant/30 absolute left-[15px] top-8 z-0"></div>
<div class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0 z-10 border border-primary/30">
<span class="material-symbols-outlined text-[18px]">enable</span>
</div>
<div class="flex-1">
<p class="text-on-surface font-body-lg"><strong>Curvature Analysis</strong> detected topological anomaly in sector 7G. Auto-correction applied.</p>
<span class="text-[12px] font-mono-precision text-on-surface-variant/60 uppercase">45m ago • System Event</span>
</div>
</div>
<div class="flex gap-stack-lg items-start relative">
<div class="w-8 h-8 rounded-full bg-tertiary/20 flex items-center justify-center text-tertiary shrink-0 z-10 border border-tertiary/30">
<span class="material-symbols-outlined text-[18px]">verified_user</span>
</div>
<div class="flex-1">
<p class="text-on-surface font-body-lg"><strong>Ratification</strong> issued security ratification for the latest architectural drift patch.</p>
<span class="text-[12px] font-mono-precision text-on-surface-variant/60 uppercase">2h ago • Admin Action</span>
</div>
</div>
</div>
</div>
</div>
<!-- Right: Metrics & Awaiting Action -->
<div class="lg:col-span-4 flex flex-col gap-gutter">
<!-- Metrics Card -->
<div class="glass-panel rounded-2xl p-container-margin border-l-4 border-error/50">
<div class="flex items-center justify-between mb-stack-md">
<h3 class="font-label-caps text-on-surface-variant opacity-60 uppercase tracking-widest">Architectural Drift Deviation</h3>
<span class="material-symbols-outlined text-error">warning</span>
</div>
<div class="flex items-baseline gap-stack-sm">
<span class="font-display-lg text-[40px] text-error">1.24%</span>
<span class="text-error font-body-sm">+0.05% change today</span>
</div>
<div class="mt-stack-lg h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-error w-[65%] rounded-full shadow-[0_0_8px_rgba(255,180,171,0.5)]"></div>
</div>
<p class="mt-stack-md text-body-sm text-on-surface-variant italic">Critical threshold: 1.50%</p>
</div>
<!-- Ratification List -->
<div class="glass-panel rounded-2xl p-container-margin">
<h3 class="font-title-md text-on-surface mb-stack-lg flex items-center gap-stack-sm">
<span class="material-symbols-outlined text-tertiary">draw</span>
                            Awaiting Ratification
                        </h3>
<div class="space-y-stack-md">
<div class="bg-surface-container-high/40 p-stack-md rounded-xl border border-outline-variant/30 hover:border-tertiary/40 transition-colors cursor-pointer">
<div class="flex justify-between items-start mb-stack-sm">
<span class="font-mono-precision text-[11px] text-tertiary uppercase">Loom_Mainframe_B2</span>
<span class="text-[10px] text-on-surface-variant">4h left</span>
</div>
<div class="text-body-sm font-medium mb-stack-sm">Structural Integrity Check</div>
<div class="flex -space-x-2">
<div class="w-6 h-6 rounded-full border border-background bg-primary-container"></div>
<div class="w-6 h-6 rounded-full border border-background bg-secondary-container"></div>
<div class="flex items-center justify-center w-6 h-6 rounded-full border border-background bg-surface-container-highest text-[8px]">+3</div>
</div>
</div>
<div class="bg-surface-container-high/40 p-stack-md rounded-xl border border-outline-variant/30 hover:border-tertiary/40 transition-colors cursor-pointer">
<div class="flex justify-between items-start mb-stack-sm">
<span class="font-mono-precision text-[11px] text-tertiary uppercase">Core_Expansion_P7</span>
<span class="text-[10px] text-on-surface-variant">6h left</span>
</div>
<div class="text-body-sm font-medium mb-stack-sm">Resource Allocation Drift</div>
</div>
</div>
<button class="w-full mt-stack-lg py-2 rounded-lg bg-surface-container-highest hover:bg-surface-bright transition-colors text-body-sm font-medium">Review All Drafts</button>
</div>
<!-- Module Status -->
<div class="glass-panel rounded-2xl p-container-margin">
<h3 class="font-title-md text-on-surface mb-stack-lg">Module Health</h3>
<div class="space-y-stack-md">
<div class="flex items-center justify-between">
<div class="flex items-center gap-stack-sm">
<div class="w-2 h-2 rounded-full bg-secondary shadow-[0_0_8px_rgba(71,226,102,0.6)]"></div>
<span class="text-body-sm">Forge</span>
</div>
<span class="font-mono-precision text-[12px] opacity-60">99.9%</span>
</div>
<div class="flex items-center justify-between">
<div class="flex items-center gap-stack-sm">
<div class="w-2 h-2 rounded-full bg-secondary shadow-[0_0_8px_rgba(71,226,102,0.6)]"></div>
<span class="text-body-sm">Engine</span>
</div>
<span class="font-mono-precision text-[12px] opacity-60">94.2%</span>
</div>
<div class="flex items-center justify-between">
<div class="flex items-center gap-stack-sm">
<div class="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_rgba(255,184,104,0.6)]"></div>
<span class="text-body-sm">Sentinel</span>
</div>
<span class="font-mono-precision text-[12px] opacity-60">Degraded</span>
</div>
</div>
</div>
</div>
</div>
<!-- Padding for bottom nav -->
<div class="h-20 shrink-0"></div>
</main>
</div>
<!-- BottomNavBar (Status Area) -->
<nav class="fixed bottom-0 left-0 w-full h-12 z-50 flex justify-center space-x-gutter items-center px-container-margin bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30 shadow-[0_-8px_32px_rgba(0,0,0,0.5)] rounded-t-xl">
<a class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98" href="#">
<span class="material-symbols-outlined text-[18px]">terminal</span>
<span class="font-mono-precision text-[10px] uppercase">Logs</span>
</a>
<a class="text-tertiary-fixed font-bold flex flex-col items-center active:scale-98" href="#">
<span class="material-symbols-outlined text-[18px]">play_circle</span>
<span class="font-mono-precision text-[10px] uppercase">Timeline</span>
</a>
<a class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98" href="#">
<span class="material-symbols-outlined text-[18px]">description</span>
<span class="font-mono-precision text-[10px] uppercase">Output</span>
</a>
<a class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98" href="#">
<span class="material-symbols-outlined text-[18px]">bug_report</span>
<span class="font-mono-precision text-[10px] uppercase">Debug</span>
</a>
<div class="h-4 w-px bg-outline-variant/30 mx-stack-lg"></div>
<div class="flex items-center gap-stack-sm text-[11px] font-mono-precision text-secondary opacity-80">
<span class="animate-pulse w-1.5 h-1.5 rounded-full bg-secondary"></span>
            LATENCY: 12ms
        </div>
</nav>
<script>
        // Micro-interactions for glass cards
        document.querySelectorAll('.glass-card').forEach(card => {
            card.addEventListener('mousedown', () => {
                card.style.transform = 'scale(0.98) translateY(0)';
            });
            card.addEventListener('mouseup', () => {
                card.style.transform = 'scale(1) translateY(-2px)';
            });
        });

        // Search bar focus effect
        const searchInput = document.querySelector('input[type="text"]');
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.classList.add('scale-105');
            searchInput.parentElement.style.width = '300px';
        });
        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.classList.remove('scale-105');
            searchInput.parentElement.style.width = '256px';
        });
    </script>
</body></html>
<div class="flex items-center space-x-stack-lg">
<div class="flex items-center space-x-2 text-on-surface-variant/60 font-label-caps text-label-caps uppercase tracking-widest">
<span>Ingest</span>
<span class="material-symbols-outlined text-[14px]">chevron_right</span>
<span class="text-primary">Normalization Forge</span>
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
<h1 class="font-headline-lg text-headline-lg text-on-surface tracking-tight">Normalization Forge</h1>
<p class="text-on-surface-variant font-body-sm text-body-sm mt-1">Reconciling 14 discrete source claims into a unified structural topology.</p>
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
<span class="text-error font-label-caps text-label-caps uppercase tracking-widest">3 Critical Contradictions Detected</span>
<span class="text-on-surface-variant/60 text-body-sm">— Conflict in 'Z-Axis Alignment' between Source-A and Source-F</span>
</div>
<button class="text-error font-label-caps text-label-caps hover:underline">VIEW CONFLICTS</button>
</div>
<!-- Normalization Table (The Matrix) -->
<div class="flex-1 glass-panel rounded-xl overflow-hidden flex flex-col shadow-2xl">
<!-- Frosted Header -->
<div class="grid grid-cols-6 bg-surface-container-high/60 backdrop-blur-md border-b border-outline-variant/30 py-3 px-6 text-on-surface-variant font-label-caps text-label-caps tracking-widest uppercase">
<div class="col-span-2">Structural Attribute</div>
<div>Source Delta</div>
<div>Confidence</div>
<div>Reconciliation</div>
<div class="text-right">Action</div>
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
<span class="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-mono-precision text-[10px]">AWAITING FORGE</span>
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
<span class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary font-mono-precision text-[10px]">CONSOLIDATED</span>
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
<span class="px-2 py-0.5 rounded-full bg-tertiary/10 text-tertiary font-mono-precision text-[10px]">MANUAL OVERRIDE</span>
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
<span class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary font-mono-precision text-[10px]">CONSOLIDATED</span>
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
<span class="text-[10px] font-mono-precision">FORGE_ENGINE_ACTIVE :: PORT_9091</span>
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
<div class="fixed top-0 right-0 h-full w-[380px] z-[100] translate-x-full transition-transform duration-500 ease-in-out flex flex-col bg-white/10 backdrop-blur-[24px] border-l border-white/10 shadow-2xl font-['Geist']" id="floating-dashboard"><div class="p-6 flex justify-between items-center border-b border-white/10"><div class="flex flex-col"><h2 class="text-on-surface font-headline-lg text-[20px] tracking-tight">Architectural Pulse</h2><div class="flex items-center gap-2 mt-1"><span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span><span class="text-[10px] font-mono-precision text-secondary uppercase">System Nominal</span></div></div><button class="p-2 hover:bg-white/10 rounded-full transition-colors" id="dashboard-close"><span class="material-symbols-outlined">close</span></button></div><div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8"><section><div><h3 class="text-on-surface-variant font-label-caps text-[11px] uppercase tracking-widest mb-4">Critical Drift</h3><div class="flex items-baseline gap-2"><span class="text-[48px] font-bold text-error leading-none">1.24%</span><span class="text-error text-[12px] font-medium">+0.05% today</span></div><div class="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden"><div class="h-full bg-error w-[65%] rounded-full shadow-[0_0_12px_rgba(255,180,171,0.4)]"></div></div><p class="mt-2 text-[11px] text-on-surface-variant/60 italic">Threshold: 1.50%</p></div></section><section><h3 class="text-on-surface-variant font-label-caps text-[11px] uppercase tracking-widest mb-4">Awaiting Ratification</h3><div class="space-y-3"><div class="p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"><div class="flex justify-between mb-1"><span class="text-primary font-mono-precision text-[10px]">LOOM_MAINFRAME_B2</span><span class="text-on-surface-variant/40 text-[10px]">4h left</span></div><p class="text-on-surface text-body-sm font-medium">Structural Integrity Check</p></div><div class="p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"><div class="flex justify-between mb-1"><span class="text-primary font-mono-precision text-[10px]">CORE_EXPANSION_P7</span><span class="text-on-surface-variant/40 text-[10px]">6h left</span></div><p class="text-on-surface text-body-sm font-medium">Resource Allocation Drift</p></div></div></section><section><h3 class="text-on-surface-variant font-label-caps text-[11px] uppercase tracking-widest mb-4">Contextual Activity</h3><div class="space-y-4"><div class="flex gap-3"><div class="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0"><span class="material-symbols-outlined text-[14px]">bolt</span></div><div><p class="text-on-surface text-[13px]"><span class="font-bold">Forge Module</span> optimized lattice.</p><p class="text-[10px] text-on-surface-variant/40 uppercase mt-0.5">12m ago</p></div></div><div class="flex gap-3"><div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0"><span class="material-symbols-outlined text-[14px]">enable</span></div><div><p class="text-on-surface text-[13px]"><span class="font-bold">Engine Core</span> corrected anomaly.</p><p class="text-[10px] text-on-surface-variant/40 uppercase mt-0.5">45m ago</p></div></div></div></section></div></div><script>(function(){const toggle = document.getElementById('dashboard-toggle');const close = document.getElementById('dashboard-close');const panel = document.getElementById('floating-dashboard');toggle.addEventListener('click', () => { panel.classList.remove('translate-x-full'); });close.addEventListener('click', () => { panel.classList.add('translate-x-full'); });})();</script></body></html>

<!-- Apple: Geometry Engine (w/ Dashboard) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;display=swap" rel="stylesheet"/>
<style>
        @font-face {
            font-family: 'Geist';
            src: url('https://cdn.jsdelivr.net/npm/geist@1.0.0/dist/fonts/geist-sans/Geist-Regular.woff2') format('woff2');
        }
        @font-face {
            font-family: 'jetbrainsMono';
            src: url('https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5.0.0/files/jetbrains-mono-latin-400-normal.woff2') format('woff2');
        }
        body {
            font-family: 'Geist', sans-serif;
            background-color: #131315;
            color: #e4e2e4;
            overflow: hidden;
            height: 100vh;
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
        .custom-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: #aac7ff;
            border: 2px solid #003064;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(170, 199, 255, 0.4);
            transition: transform 0.1s ease;
        }
        .custom-slider::-webkit-slider-thumb:active {
            transform: scale(1.2);
        }
        .thin-bar {
            width: 2px;
            transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
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
                        "xl": "0.75rem",
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
<body class="bg-background text-on-background flex flex-col">
<!-- TopNavBar -->
<header class="flex justify-between items-center px-container-margin w-full h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 z-50 fixed top-0">
<div class="flex items-center space-x-gutter">
<span class="font-display-lg text-title-md font-bold text-primary">Loom Blueprint Workbench</span>
<nav class="hidden md:flex space-x-stack-lg ml-gutter items-center">
<span class="text-on-surface-variant font-medium font-body-lg text-body-lg">Ingest</span>
<span class="material-symbols-outlined text-outline-variant text-sm">chevron_right</span>
<span class="text-on-surface-variant font-medium font-body-lg text-body-lg">Models</span>
<span class="material-symbols-outlined text-outline-variant text-sm">chevron_right</span>
<span class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg">Geometry Engine</span>
</nav>
</div>
<div class="flex items-center space-x-stack-md">
<div class="relative group">
<span class="material-symbols-outlined p-2 rounded-full hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant">search</span>
</div>
<span class="material-symbols-outlined p-2 rounded-full hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant">settings</span>
<span class="material-symbols-outlined p-2 rounded-full hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant">help</span>
</div>
</header>
<div class="flex flex-1 pt-16 overflow-hidden">
<!-- SideNavBar (Left Tool Dock) -->
<aside class="flex flex-col items-center py-stack-lg space-y-stack-md bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 h-full w-[64px] z-40">
<button class="p-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">near_me</span>
</button>
<button class="p-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">straighten</span>
</button>
<button class="p-3 bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)] transition-all">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">architecture</span>
</button>
<button class="p-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">layers</span>
</button>
<button class="p-3 text-on-surface-variant hover:bg-surface-container-high rounded-xl transition-all">
<span class="material-symbols-outlined">visibility</span>
</button>
</aside>
<!-- Main Workspace Area -->
<main class="flex-1 relative flex flex-col bg-black overflow-hidden">
<!-- WebGL Content Placeholder (Dark Viewport) -->
<div class="absolute inset-0 bg-gradient-to-br from-surface-container-lowest to-black opacity-40"></div>
<div class="relative z-10 flex flex-col h-full p-gutter">
<!-- Bimodal Curvature Distribution Card -->
<div class="glass-panel rounded-xl p-stack-lg border border-outline-variant/20 flex flex-col h-1/2">
<div class="flex justify-between items-center mb-stack-lg">
<div>
<h2 class="font-headline-lg text-title-md text-on-surface">Curvature Distribution</h2>
<p class="font-body-sm text-body-sm text-on-surface-variant">Bimodal analysis of manifold segments</p>
</div>
<div class="flex space-x-stack-md">
<div class="flex items-center space-x-2">
<div class="w-3 h-3 rounded-full bg-[#3b82f6]"></div>
<span class="font-label-caps text-label-caps">Observed</span>
</div>
<div class="flex items-center space-x-2">
<div class="w-3 h-3 rounded-full bg-[#10b981]"></div>
<span class="font-label-caps text-label-caps">Declared</span>
</div>
</div>
</div>
<!-- Chart Canvas Area -->
<div class="flex-1 flex items-end justify-between space-x-[2px] pb-4 px-2" id="distribution-chart">
<!-- Bars generated via JS for dynamic feel -->
</div>
<!-- Threshold Sliders -->
<div class="grid grid-cols-2 gap-gutter mt-stack-lg border-t border-outline-variant/30 pt-stack-lg">
<div class="space-y-2">
<div class="flex justify-between items-center">
<label class="font-label-caps text-label-caps text-primary">THETA_BRIDGE</label>
<span class="font-mono-precision text-mono-precision text-primary" id="val-bridge">0.42</span>
</div>
<input class="w-full h-1 bg-surface-container-highest rounded-full appearance-none custom-slider transition-all hover:bg-primary-container/30" max="100" min="0" oninput="document.getElementById('val-bridge').innerText = (this.value/100).toFixed(2)" type="range" value="42"/>
</div>
<div class="space-y-2">
<div class="flex justify-between items-center">
<label class="font-label-caps text-label-caps text-secondary">THETA_COHESION</label>
<span class="font-mono-precision text-mono-precision text-secondary" id="val-cohesion">0.78</span>
</div>
<input class="w-full h-1 bg-surface-container-highest rounded-full appearance-none custom-slider transition-all hover:bg-secondary-container/30" max="100" min="0" oninput="document.getElementById('val-cohesion').innerText = (this.value/100).toFixed(2)" type="range" value="78"/>
</div>
</div>
</div>
<!-- Metric Deformation Timeline -->
<div class="mt-gutter glass-panel rounded-xl p-stack-lg border border-outline-variant/20 flex-1 overflow-hidden flex flex-col">
<h3 class="font-title-md text-body-lg text-on-surface mb-stack-md">Metric Deformation Timeline</h3>
<div class="flex-1 flex flex-col space-y-stack-sm overflow-y-auto">
<!-- Timeline Rows -->
<div class="flex items-center space-x-gutter p-stack-md hover:bg-white/5 rounded-lg transition-colors border-b border-outline-variant/10">
<span class="font-mono-precision text-mono-precision text-outline w-16">08:24:12</span>
<span class="flex-1 font-body-sm text-body-sm">Global Manifold Optimization Cycle 44</span>
<span class="font-mono-precision text-mono-precision text-secondary">-0.0024 Δ</span>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="bg-secondary h-full w-[88%]"></div>
</div>
</div>
<div class="flex items-center space-x-gutter p-stack-md hover:bg-white/5 rounded-lg transition-colors border-b border-outline-variant/10">
<span class="font-mono-precision text-mono-precision text-outline w-16">08:22:05</span>
<span class="flex-1 font-body-sm text-body-sm">Curvature Normalization (Layer 7)</span>
<span class="font-mono-precision text-mono-precision text-primary">+0.0150 Δ</span>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="bg-primary h-full w-[45%]"></div>
</div>
</div>
<div class="flex items-center space-x-gutter p-stack-md hover:bg-white/5 rounded-lg transition-colors border-b border-outline-variant/10">
<span class="font-mono-precision text-mono-precision text-outline w-16">08:19:44</span>
<span class="flex-1 font-body-sm text-body-sm">Topology Constraint Violation: Node #F2A</span>
<span class="font-mono-precision text-mono-precision text-error">+0.8421 Δ</span>
<div class="w-24 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="bg-error h-full w-[95%]"></div>
</div>
</div>
</div>
</div>
</div>
<!-- Primary Action Button (FAB Style but docked) -->
<button class="fixed bottom-16 right-[344px] flex items-center space-x-stack-md bg-primary text-on-primary font-bold px-stack-lg py-stack-md rounded-full shadow-[0_8px_32px_rgba(170,199,255,0.4)] active:scale-95 transition-all z-40">
<span class="material-symbols-outlined">auto_graph</span>
<span class="font-body-lg text-body-lg">Propose Partition Scheme</span>
</button>
</main>
<!-- Right Inspector Panel -->
<aside class="w-[320px] glass-panel border-l border-outline-variant/30 flex flex-col z-40">
<div class="p-container-margin border-b border-outline-variant/30">
<h3 class="font-title-md text-title-md text-on-surface">Inspector</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant">Loom V1.2.9 Engine</p>
</div>
<div class="flex-1 overflow-y-auto p-panel-padding space-y-gutter">
<!-- Geometry Props Section -->
<section>
<button class="flex justify-between items-center w-full py-2 text-on-surface font-label-caps text-label-caps group">
                        PROPERTIES
                        <span class="material-symbols-outlined text-sm">expand_more</span>
</button>
<div class="space-y-stack-md mt-stack-md">
<div class="flex justify-between items-center glass-popover p-stack-md rounded-lg">
<span class="font-body-sm text-on-surface-variant">Vertex Count</span>
<span class="font-mono-precision text-mono-precision text-on-surface">1,424,092</span>
</div>
<div class="flex justify-between items-center glass-popover p-stack-md rounded-lg">
<span class="font-body-sm text-on-surface-variant">Topology Gen</span>
<span class="font-mono-precision text-mono-precision text-on-surface">B-Spline</span>
</div>
<div class="flex justify-between items-center glass-popover p-stack-md rounded-lg">
<span class="font-body-sm text-on-surface-variant">Deformation</span>
<span class="font-mono-precision text-mono-precision text-secondary">0.02% Low</span>
</div>
</div>
</section>
<!-- Constraint Section -->
<section>
<button class="flex justify-between items-center w-full py-2 text-on-surface font-label-caps text-label-caps">
                        CONSTRAINTS
                        <span class="material-symbols-outlined text-sm">add_circle</span>
</button>
<div class="flex flex-wrap gap-2 mt-stack-md">
<span class="px-3 py-1 glass-popover rounded-full text-label-caps flex items-center gap-1 border border-secondary/20">
<div class="w-1.5 h-1.5 rounded-full bg-secondary"></div> Fixed Normal
                        </span>
<span class="px-3 py-1 glass-popover rounded-full text-label-caps flex items-center gap-1 border border-primary/20">
<div class="w-1.5 h-1.5 rounded-full bg-primary"></div> Symmetry X
                        </span>
<span class="px-3 py-1 glass-popover rounded-full text-label-caps flex items-center gap-1 border border-tertiary/20">
<div class="w-1.5 h-1.5 rounded-full bg-tertiary"></div> Tangency
                        </span>
</div>
</section>
<!-- Preview Image -->
<section class="mt-4">
<div class="aspect-video rounded-xl overflow-hidden glass-panel border border-outline-variant/30 relative">
<div class="bg-cover bg-center w-full h-full opacity-60 grayscale hover:grayscale-0 transition-all duration-500 cursor-zoom-in" data-alt="A highly detailed 3D CAD rendering of a complex aerodynamic engine component featuring smooth metallic surfaces, blue and green wireframe overlays showing curvature distribution, and glowing highlights on precision machined edges. The background is a deep charcoal engineering workspace with high-end glassmorphic UI elements floating in the periphery. Lighting is dramatic and professional, emphasizing the mathematical perfection of the geometric form." style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuC6TQ6L8Um6Ikg1UPgtAcuPXMIftVdL5Ep5hY2Z1V78vAjIjk3dVz_CCQcjeMC1mnoDvZLwXfBrx3x0ZoIM_Iz1ghBbDgNI-LD4NOz-whfA2C_XExiX0xv3pWwUztd2UKD_m5FakyPEYZyGyCf1LbZEgxK4zAhGLGC5GOGNJRtccJtjJw1lBAk0yvVg6S_Vg94S3LJgGC4Wr2Bi0_Q-1QZD3sXV9UVJ1bfDBtcdhEHEMdwr-VCZZT7mia0uZMtUz0RByuqlpKEpGSY')"></div>
<div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-stack-md">
<span class="font-label-caps text-[10px] text-on-surface/80">LIVE PERSPECTIVE A-1</span>
</div>
</div>
</section>
</div>
</aside>
</div>
<!-- BottomNavBar (Console) -->
<footer class="fixed bottom-0 left-0 w-full h-12 z-50 flex justify-center space-x-gutter items-center px-container-margin bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30 shadow-[0_-8px_32px_rgba(0,0,0,0.5)] rounded-t-xl">
<button class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">terminal</span>
<span class="font-mono-precision text-[10px] uppercase">Logs</span>
</button>
<button class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">play_circle</span>
<span class="font-mono-precision text-[10px] uppercase">Timeline</span>
</button>
<button class="text-tertiary-fixed font-bold flex flex-col items-center hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">description</span>
<span class="font-mono-precision text-[10px] uppercase">Output</span>
</button>
<button class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98">
<span class="material-symbols-outlined text-[18px]">bug_report</span>
<span class="font-mono-precision text-[10px] uppercase">Debug</span>
</button>
<button class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors active:scale-98 ml-stack-lg border-l border-outline-variant/30 pl-stack-lg" onclick="document.getElementById('floating-dashboard').classList.toggle('translate-x-full')">
<span class="material-symbols-outlined text-[18px]">dashboard</span>
<span class="font-mono-precision text-[10px] uppercase">Pulse</span>
</button></footer>
<script>
        // Generate Bimodal Curvature Chart
        const chart = document.getElementById('distribution-chart');
        const barCount = 100;
        
        for (let i = 0; i < barCount; i++) {
            const bar = document.createElement('div');
            bar.className = 'thin-bar rounded-t-full';
            
            // Generate bimodal distribution data
            const x = i / barCount;
            const mean1 = 0.3;
            const std1 = 0.1;
            const mean2 = 0.7;
            const std2 = 0.12;
            
            const dist1 = Math.exp(-Math.pow(x - mean1, 2) / (2 * Math.pow(std1, 2)));
            const dist2 = 0.8 * Math.exp(-Math.pow(x - mean2, 2) / (2 * Math.pow(std2, 2)));
            const heightValue = (dist1 + dist2) * 80;
            
            bar.style.height = `${heightValue}%`;
            
            // Visual logic for Thresholds
            if (i < 42) {
                bar.style.backgroundColor = '#3b82f6'; // Blue for lower curvature
                bar.style.opacity = '0.7';
            } else if (i < 78) {
                bar.style.backgroundColor = '#60a5fa'; // Lighter blue bridge
                bar.style.opacity = '0.4';
            } else {
                bar.style.backgroundColor = '#10b981'; // Green for high curvature
                bar.style.opacity = '0.8';
            }
            
            chart.appendChild(bar);
        }

        // Add micro-interaction for chart bars
        chart.addEventListener('mousemove', (e) => {
            const bars = chart.querySelectorAll('.thin-bar');
            const rect = chart.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const index = Math.floor((mouseX / rect.width) * bars.length);
            
            bars.forEach((b, idx) => {
                if (idx === index) {
                    b.style.transform = 'scaleY(1.1)';
                    b.style.opacity = '1';
                } else {
                    b.style.transform = 'scaleY(1)';
                }
            });
        });

        chart.addEventListener('mouseleave', () => {
            const bars = chart.querySelectorAll('.thin-bar');
            bars.forEach(b => {
                b.style.transform = 'scaleY(1)';
                const opacity = b.style.backgroundColor.includes('16') ? '0.7' : '0.8';
                b.style.opacity = b.style.backgroundColor.includes('96') ? '0.4' : opacity;
            });
        });
    </script>
<div class="fixed top-0 right-0 h-full w-[380px] z-[100] glass-panel border-l border-white/10 translate-x-full transition-transform duration-500 ease-in-out flex flex-col shadow-2xl" id="floating-dashboard" style="background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(24px);">
<div class="p-container-margin border-b border-white/10 flex justify-between items-center">
<div>
<h3 class="font-headline-lg text-title-md text-on-surface">Architectural Pulse</h3>
<div class="flex items-center gap-1.5 mt-1">
<div class="w-2 h-2 rounded-full bg-secondary animate-pulse"></div>
<span class="text-[10px] font-label-caps text-secondary uppercase tracking-wider">System Nominal</span>
</div>
</div>
<button class="p-2 hover:bg-white/10 rounded-full transition-colors" onclick="document.getElementById('floating-dashboard').classList.add('translate-x-full')">
<span class="material-symbols-outlined text-on-surface-variant">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto p-container-margin space-y-gutter custom-scrollbar">
<!-- Critical Drift Section -->
<section class="glass-popover p-panel-padding rounded-xl border border-error/20">
<div class="flex justify-between items-center mb-2">
<span class="text-label-caps text-on-surface-variant opacity-60">CRITICAL DRIFT</span>
<span class="material-symbols-outlined text-error text-sm">warning</span>
</div>
<div class="flex items-baseline gap-2">
<span class="text-display-lg text-[32px] text-error">1.24%</span>
<span class="text-[10px] text-error font-mono-precision">+0.05% TODAY</span>
</div>
<div class="mt-3 h-1 w-full bg-white/5 rounded-full overflow-hidden">
<div class="h-full bg-error w-[65%] rounded-full"></div>
</div>
</section>
<!-- Awaiting Ratification -->
<section>
<h4 class="text-label-caps text-on-surface-variant mb-3">AWAITING RATIFICATION</h4>
<div class="space-y-2">
<div class="p-3 bg-white/5 rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer">
<div class="flex justify-between text-[10px] font-mono-precision text-primary mb-1">
<span>LOOM_MAINFRAME_B2</span>
<span class="text-on-surface-variant">4h left</span>
</div>
<div class="text-body-sm font-medium">Structural Integrity Check</div>
</div>
<div class="p-3 bg-white/5 rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer">
<div class="flex justify-between text-[10px] font-mono-precision text-primary mb-1">
<span>CORE_EXPANSION_P7</span>
<span class="text-on-surface-variant">6h left</span>
</div>
<div class="text-body-sm font-medium">Resource Allocation Drift</div>
</div>
</div>
</section>
<!-- Contextual Activity -->
<section>
<h4 class="text-label-caps text-on-surface-variant mb-3">RECENT ACTIVITY</h4>
<div class="space-y-4">
<div class="flex gap-3">
<div class="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0">
<span class="material-symbols-outlined text-[14px]">bolt</span>
</div>
<div>
<p class="text-body-sm text-on-surface">Forge Module optimized lattice.</p>
<span class="text-[10px] text-on-surface-variant/60 uppercase">12m ago</span>
</div>
</div>
<div class="flex gap-3">
<div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0">
<span class="material-symbols-outlined text-[14px]">enable</span>
</div>
<div>
<p class="text-body-sm text-on-surface">Engine Core anomaly corrected.</p>
<span class="text-[10px] text-on-surface-variant/60 uppercase">45m ago</span>
</div>
</div>
</div>
</section>
</div>
<div class="p-container-margin border-t border-white/10">
<button class="w-full py-2.5 bg-primary text-on-primary rounded-lg font-bold text-body-sm hover:opacity-90 transition-opacity">
            Open Full Workbench
        </button>
</div>
</div></body></html>

<!-- Apple: Ratification Sanctuary (w/ Dashboard) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
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
<span class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg">Ratification Sanctuary</span>
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
<h1 class="font-headline-lg text-headline-lg text-on-surface">Sanctuary Analysis</h1>
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
<span class="font-label-caps text-label-caps text-primary opacity-60">OPTIMAL RATIFICATION ZONE</span>
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
<span class="text-body-sm text-on-surface-variant">Loom Integrity</span>
<div class="w-1/2 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-primary w-[92%]"></div>
</div>
</div>
<div class="flex justify-between items-center">
<span class="text-body-sm text-on-surface-variant">Blueprint Fidelity</span>
<div class="w-1/2 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-primary w-[88%]"></div>
</div>
</div>
<div class="flex justify-between items-center">
<span class="text-body-sm text-on-surface-variant">Threshold Compliance</span>
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
            "Sanctuary protocols active."
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

<!-- Apple: Implementation Cockpit (w/ Dashboard) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Loom Blueprint Workbench - Implementation Cockpit</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<style>
        @font-face {
            font-family: 'Geist';
            src: url('https://cdn.jsdelivr.net/gh/vercel/geist-font@main/packages/next/dist/fonts/geist-sans/Geist-Regular.woff2') format('woff2');
            font-weight: 400;
        }
        @font-face {
            font-family: 'Geist';
            src: url('https://cdn.jsdelivr.net/gh/vercel/geist-font@main/packages/next/dist/fonts/geist-sans/Geist-Bold.woff2') format('woff2');
            font-weight: 700;
        }
        @font-face {
            font-family: 'jetbrainsMono';
            src: url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap');
        }

        body {
            font-family: 'Geist', sans-serif;
            background-color: #131315;
            color: #e4e2e4;
            overflow: hidden;
            height: 100vh;
        }

        .glass-panel {
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        .ghost-border {
            border: 0.5px solid rgba(255, 255, 255, 0.1);
        }

        .custom-scrollbar::-webkit-scrollbar {
            width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
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
                "DEFAULT": "12px",
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
<body class="flex flex-col h-screen select-none">
<!-- Top Navigation Bar -->
<header class="bg-surface/80 backdrop-blur-xl text-primary font-body-lg text-body-lg docked full-width top-0 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/30 shadow-sm flex justify-between items-center px-container-margin w-full h-16 z-50">
<div class="flex items-center space-x-gutter">
<span class="font-display-lg text-display-lg font-bold text-primary">Loom Blueprint Workbench</span>
<nav class="flex space-x-6 items-center">
<span class="text-on-surface-variant font-medium hover:text-primary transition-colors cursor-pointer">Ingest</span>
<span class="text-on-surface-variant opacity-30">/</span>
<span class="text-on-surface-variant font-medium hover:text-primary transition-colors cursor-pointer">Drafts</span>
<span class="text-on-surface-variant opacity-30">/</span>
<span class="text-primary font-bold border-b-2 border-primary pb-1 cursor-default">Implementation Cockpit</span>
</nav>
</div>
<div class="flex items-center space-x-4">
<div class="relative">
<span class="absolute inset-y-0 left-3 flex items-center text-on-surface-variant">
<span class="material-symbols-outlined text-sm">search</span>
</span>
<input class="bg-surface-container-highest border-none rounded-full pl-10 pr-4 py-1.5 text-sm focus:ring-1 focus:ring-primary w-64 text-on-surface" placeholder="Search workbench..." type="text"/>
</div>
<button class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors p-2 active:scale-95">settings</button>
<button class="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors p-2 active:scale-95">help</button>
</div>
</header>
<div class="flex flex-1 overflow-hidden">
<!-- Side Navigation (Left Rail) -->
<aside class="bg-surface-container-low/80 backdrop-blur-xl text-secondary font-label-caps text-label-caps docked left-0 h-full w-[64px] bg-surface-container-low/80 backdrop-blur-xl border-r border-outline-variant/30 flat no shadows flex flex-col items-center py-stack-lg space-y-stack-md z-40">
<button class="w-10 h-10 flex items-center justify-center hover:bg-surface-container-high rounded-xl active:scale-90 transition-all text-on-surface-variant">
<span class="material-symbols-outlined">near_me</span>
</button>
<button class="w-10 h-10 flex items-center justify-center hover:bg-surface-container-high rounded-xl active:scale-90 transition-all text-on-surface-variant">
<span class="material-symbols-outlined">straighten</span>
</button>
<button class="w-10 h-10 flex items-center justify-center bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)] active:scale-90 transition-all">
<span class="material-symbols-outlined">architecture</span>
</button>
<button class="w-10 h-10 flex items-center justify-center hover:bg-surface-container-high rounded-xl active:scale-90 transition-all text-on-surface-variant">
<span class="material-symbols-outlined">layers</span>
</button>
<button class="w-10 h-10 flex items-center justify-center hover:bg-surface-container-high rounded-xl active:scale-90 transition-all text-on-surface-variant">
<span class="material-symbols-outlined">visibility</span>
</button>
<div class="flex-grow"></div>
<div class="w-8 h-[1px] bg-outline-variant/30"></div>
<button class="w-10 h-10 flex items-center justify-center hover:bg-surface-container-high rounded-xl active:scale-90 transition-all text-on-surface-variant">
<span class="material-symbols-outlined">terminal</span>
</button>
</aside>
<!-- Main Content Area -->
<main class="flex-1 flex flex-col overflow-hidden relative">
<!-- Split Pane View -->
<div class="flex flex-1 overflow-hidden p-6 gap-6">
<!-- Left Side: Allowed File Tree -->
<div class="flex-1 glass-panel bg-primary/5 rounded-xl ghost-border flex flex-col overflow-hidden">
<div class="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/5">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">folder_open</span>
<h2 class="font-title-md text-title-md text-on-surface">Allowed Buffer</h2>
</div>
<span class="bg-primary/20 text-primary px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Write Access</span>
</div>
<div class="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-2">
<!-- Folder Example -->
<div class="space-y-1">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80 group">
<span class="material-symbols-outlined text-sm text-primary/60 group-hover:text-primary">expand_more</span>
<span class="material-symbols-outlined text-sm text-primary">folder</span>
<span class="text-body-sm font-body-sm">src</span>
</div>
<div class="pl-8 space-y-1 border-l border-primary/10 ml-4">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80 group">
<span class="material-symbols-outlined text-sm text-primary/60 group-hover:text-primary">expand_more</span>
<span class="material-symbols-outlined text-sm text-primary">folder</span>
<span class="text-body-sm font-body-sm">components</span>
</div>
<div class="pl-8 space-y-1 border-l border-primary/10 ml-4">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 text-primary cursor-pointer">
<span class="material-symbols-outlined text-sm">javascript</span>
<span class="text-body-sm font-body-sm">CockpitController.js</span>
<span class="ml-auto w-2 h-2 rounded-full bg-primary animate-pulse"></span>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80">
<span class="material-symbols-outlined text-sm text-primary/60">javascript</span>
<span class="text-body-sm font-body-sm">SentinelProtocol.js</span>
</div>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80">
<span class="material-symbols-outlined text-sm text-primary/60">css</span>
<span class="text-body-sm font-body-sm">MainLayout.css</span>
</div>
</div>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80 group">
<span class="material-symbols-outlined text-sm text-primary/60 group-hover:text-primary">chevron_right</span>
<span class="material-symbols-outlined text-sm text-primary">folder</span>
<span class="text-body-sm font-body-sm">assets</span>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer text-on-surface/80">
<span class="material-symbols-outlined text-sm text-primary/60">description</span>
<span class="text-body-sm font-body-sm">README.md</span>
</div>
</div>
</div>
<!-- Right Side: Forbidden Files -->
<div class="flex-1 glass-panel bg-surface-container-highest/30 rounded-xl ghost-border flex flex-col overflow-hidden">
<div class="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-black/20">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-on-surface-variant/50">lock</span>
<h2 class="font-title-md text-title-md text-on-surface-variant">Forbidden Core</h2>
</div>
<span class="bg-surface-container-highest text-on-surface-variant px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Read Only</span>
</div>
<div class="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-2 opacity-60 grayscale-[0.5]">
<div class="space-y-1">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-default text-on-surface-variant/80">
<span class="material-symbols-outlined text-sm">expand_more</span>
<span class="material-symbols-outlined text-sm">folder</span>
<span class="text-body-sm font-body-sm">kernel</span>
</div>
<div class="pl-8 space-y-1 border-l border-white/5 ml-4">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-on-surface-variant/80">
<span class="material-symbols-outlined text-sm">security</span>
<span class="text-body-sm font-body-sm">AuthManager.bin</span>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-on-surface-variant/80">
<span class="material-symbols-outlined text-sm">memory</span>
<span class="text-body-sm font-body-sm">SystemAllocation.sys</span>
</div>
</div>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-on-surface-variant/80">
<span class="material-symbols-outlined text-sm">chevron_right</span>
<span class="material-symbols-outlined text-sm">folder</span>
<span class="text-body-sm font-body-sm">drivers</span>
</div>
<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-on-surface-variant/80">
<span class="material-symbols-outlined text-sm">key</span>
<span class="text-body-sm font-body-sm">license.key</span>
</div>
</div>
</div>
</div>
<!-- Floating Action Bar / Primary Action -->
<div class="absolute bottom-20 left-1/2 -translate-x-1/2 z-30">
<button class="group relative flex items-center gap-3 bg-primary text-on-primary px-8 py-4 rounded-full font-bold shadow-2xl hover:scale-105 active:scale-95 transition-all overflow-hidden" id="sync-button">
<div class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
<span class="material-symbols-outlined animate-spin-slow">sync</span>
<span class="font-title-md text-title-md tracking-tight">Synchronize Active Sentinel</span>
</button>
</div>
<!-- Bottom Console (Shared Component Mock) -->
<footer class="bg-surface-container-high/90 backdrop-blur-2xl text-tertiary font-mono-precision text-mono-precision docked bottom-0 w-full rounded-t-xl bg-surface-container-high/90 backdrop-blur-2xl border-t border-outline-variant/30 shadow-[0_-8px_32px_rgba(0,0,0,0.5)] fixed bottom-0 left-0 w-full h-12 z-50 flex justify-center space-x-gutter items-center px-container-margin">
<div class="flex-1 flex items-center space-x-6"><div class="text-on-surface-variant/70 flex flex-col items-center hover:text-primary transition-colors cursor-pointer group" onclick="document.getElementById('floating-dashboard').classList.toggle('translate-x-full')">
<span class="material-symbols-outlined text-sm group-hover:scale-110 transition-transform">dashboard</span>
<span class="text-[10px] uppercase">Pulse</span>
</div>
<div class="text-tertiary-fixed font-bold flex flex-col items-center cursor-pointer">
<span class="material-symbols-outlined text-sm">terminal</span>
<span class="text-[10px] uppercase">Logs</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors cursor-pointer">
<span class="material-symbols-outlined text-sm">play_circle</span>
<span class="text-[10px] uppercase">Timeline</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors cursor-pointer">
<span class="material-symbols-outlined text-sm">description</span>
<span class="text-[10px] uppercase">Output</span>
</div>
<div class="text-on-surface-variant/70 flex flex-col items-center hover:text-on-surface transition-colors cursor-pointer">
<span class="material-symbols-outlined text-sm">bug_report</span>
<span class="text-[10px] uppercase">Debug</span>
</div>
</div>
<div class="flex items-center space-x-4 text-[11px] opacity-60">
<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-secondary"></span> System Ready</span>
<span>UTF-8</span>
<span>LN 128, COL 12</span>
</div>
</footer>
</main>
<!-- Inspector (Right Panel) -->
<aside class="w-[320px] bg-surface-container-low/80 backdrop-blur-xl border-l border-outline-variant/30 flex flex-col z-40">
<div class="p-container-margin border-b border-outline-variant/30">
<h3 class="font-title-md text-title-md text-on-surface mb-1">Inspector</h3>
<p class="text-body-sm font-body-sm text-on-surface-variant/60">Active Sentinel Node V4.2</p>
</div>
<div class="flex-1 overflow-y-auto p-panel-padding space-y-stack-lg custom-scrollbar">
<!-- Data Visualization Card -->
<div class="bg-surface-container-highest/40 rounded-xl p-4 ghost-border">
<div class="flex justify-between items-center mb-4">
<span class="font-label-caps text-label-caps text-on-surface-variant">Sync Integrity</span>
<span class="text-secondary font-mono-precision">98.4%</span>
</div>
<div class="h-24 relative overflow-hidden rounded-lg bg-black/40">
</div>
</div>
<!-- Input Fields -->
<div class="space-y-4">
<div>
<label class="font-label-caps text-label-caps text-on-surface-variant mb-2 block">Protocol Name</label>
<input class="w-full bg-surface-container-highest/50 border border-outline-variant/30 rounded-lg px-3 py-2 text-on-surface font-mono-precision text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all" type="text" value="Sentinel_Echo_Alpha"/>
</div>
<div>
<label class="font-label-caps text-label-caps text-on-surface-variant mb-2 block">Constraint Mode</label>
<select class="w-full bg-surface-container-highest/50 border border-outline-variant/30 rounded-lg px-3 py-2 text-on-surface font-mono-precision text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none">
<option>HEURISTIC_STRICT</option>
<option>HEURISTIC_LOOSE</option>
<option>MANUAL_OVERRIDE</option>
</select>
</div>
</div>
<!-- Layers / Chips -->
<div class="space-y-2">
<span class="font-label-caps text-label-caps text-on-surface-variant mb-1 block">Active Constraints</span>
<div class="flex flex-wrap gap-2">
<div class="flex items-center gap-2 bg-secondary/10 text-secondary px-3 py-1 rounded-full ghost-border text-[11px] font-bold">
<span class="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                            STABILITY_LOCK
                        </div>
<div class="flex items-center gap-2 bg-tertiary/10 text-tertiary px-3 py-1 rounded-full ghost-border text-[11px] font-bold">
<span class="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                            REF_VALIDATION
                        </div>
<div class="flex items-center gap-2 bg-primary/10 text-primary px-3 py-1 rounded-full ghost-border text-[11px] font-bold">
<span class="w-1.5 h-1.5 rounded-full bg-primary"></span>
                            ASYNC_SYNC
                        </div>
</div>
</div>
<!-- Metadata Card -->
<div class="bg-surface-container-highest/20 rounded-xl p-4 ghost-border text-[11px] font-mono-precision leading-relaxed opacity-60">
<div class="flex justify-between border-b border-white/5 pb-2 mb-2">
<span>CREATED</span>
<span>2023.10.12:14:22</span>
</div>
<div class="flex justify-between border-b border-white/5 pb-2 mb-2">
<span>MODIFIED</span>
<span>2023.11.01:09:45</span>
</div>
<div class="flex justify-between">
<span>HASH_SIG</span>
<span>AX-982...F421</span>
</div>
</div>
</div>
<!-- Footer Action in Inspector -->
<div class="p-4 bg-surface-container-low border-t border-outline-variant/30">
<button class="w-full py-2 bg-white/5 hover:bg-white/10 text-on-surface rounded-lg font-bold text-sm ghost-border active:scale-95 transition-all">
                    Reset Cockpit Parameters
                </button>
</div>
</aside>
</div>
<!-- Micro-interaction Scripts -->
<script>
        // Sync Button Click Animation
        const syncBtn = document.getElementById('sync-button');
        syncBtn.addEventListener('click', () => {
            const icon = syncBtn.querySelector('.material-symbols-outlined');
            const text = syncBtn.querySelector('span:last-child');
            
            icon.classList.remove('animate-spin-slow');
            icon.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
            icon.style.transform = 'rotate(360deg)';
            
            text.innerText = 'Synchronizing...';
            syncBtn.classList.add('bg-secondary');
            syncBtn.classList.remove('bg-primary');

            setTimeout(() => {
                icon.style.transform = 'rotate(0deg)';
                icon.classList.add('animate-spin-slow');
                text.innerText = 'Sentinel Synchronized';
                
                setTimeout(() => {
                    syncBtn.classList.add('bg-primary');
                    syncBtn.classList.remove('bg-secondary');
                    text.innerText = 'Synchronize Active Sentinel';
                }, 2000);
            }, 1000);
        });

        // Add custom styles for the spin
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin-slow {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            .animate-spin-slow {
                animation: spin-slow 8s linear infinite;
            }
        `;
        document.head.appendChild(style);
    </script>
<aside class="fixed top-0 right-0 h-screen w-[380px] z-[60] translate-x-full transition-transform duration-500 ease-in-out glass-panel bg-white/5 backdrop-blur-[24px] border-l border-white/10 flex flex-col shadow-2xl" id="floating-dashboard">
<!-- Header -->
<div class="p-6 border-b border-white/10 flex justify-between items-center">
<div>
<h2 class="font-headline-lg text-title-md text-on-surface">Architectural Pulse</h2>
<div class="flex items-center gap-2 mt-1">
<span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
<span class="text-[10px] font-mono-precision text-secondary uppercase tracking-widest">System Nominal</span>
</div>
</div>
<button class="p-2 hover:bg-white/10 rounded-full transition-colors" onclick="document.getElementById('floating-dashboard').classList.add('translate-x-full')">
<span class="material-symbols-outlined text-on-surface-variant">close</span>
</button>
</div>
<div class="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
<!-- Critical Drift Section -->
<section>
<h3 class="font-label-caps text-on-surface-variant mb-4 uppercase tracking-widest">Critical Drift</h3>
<div class="bg-white/5 rounded-xl p-4 border border-white/5">
<div class="flex items-baseline gap-2">
<span class="text-display-lg text-[32px] text-error font-bold">1.24%</span>
<span class="text-error text-body-sm">+0.05% today</span>
</div>
<div class="mt-3 h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
<div class="h-full bg-error w-[65%] rounded-full"></div>
</div>
<p class="mt-2 text-[10px] text-on-surface-variant/60 italic">Threshold: 1.50%</p>
</div>
</section>
<!-- Awaiting Ratification -->
<section>
<h3 class="font-label-caps text-on-surface-variant mb-4 uppercase tracking-widest">Awaiting Ratification</h3>
<div class="space-y-3">
<div class="bg-white/5 p-3 rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer">
<div class="flex justify-between text-[10px] font-mono-precision text-primary mb-1">
<span>LOOM_MAINFRAME_B2</span>
<span class="text-on-surface-variant">4h left</span>
</div>
<div class="text-body-sm font-medium">Structural Integrity Check</div>
</div>
<div class="bg-white/5 p-3 rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer">
<div class="flex justify-between text-[10px] font-mono-precision text-primary mb-1">
<span>CORE_EXPANSION_P7</span>
<span class="text-on-surface-variant">6h left</span>
</div>
<div class="text-body-sm font-medium">Resource Allocation Drift</div>
</div>
</div>
</section>
<!-- Contextual Activity -->
<section>
<h3 class="font-label-caps text-on-surface-variant mb-4 uppercase tracking-widest">Recent Activity</h3>
<div class="space-y-4">
<div class="flex gap-3">
<div class="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0">
<span class="material-symbols-outlined text-[14px]">bolt</span>
</div>
<div>
<p class="text-body-sm text-on-surface/90"><strong>Forge</strong> optimized Hyperion_V4 lattice.</p>
<span class="text-[10px] text-on-surface-variant/50 uppercase">12m ago</span>
</div>
</div>
<div class="flex gap-3">
<div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0">
<span class="material-symbols-outlined text-[14px]">enable</span>
</div>
<div>
<p class="text-body-sm text-on-surface/90"><strong>Engine</strong> corrected sector 7G anomaly.</p>
<span class="text-[10px] text-on-surface-variant/50 uppercase">45m ago</span>
</div>
</div>
</div>
</section>
</div>
<!-- Footer -->
<div class="p-6 bg-white/5 border-t border-white/10">
<button class="w-full py-3 bg-primary text-on-primary rounded-lg font-bold text-sm hover:opacity-90 transition-opacity">
            View Full Analytics
        </button>
</div>
</aside></body></html>

<!-- Apple: Sentinel Drift Monitor (w/ Dashboard) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Sentinel Drift Monitor | Loom Blueprint Workbench</title>
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
        .glow-blue { filter: drop-shadow(0 0 8px rgba(71, 226, 102, 0.4)); } /* Using secondary color for vibrant glow */
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
<span class="text-primary font-bold border-b-2 border-primary pb-1 font-body-lg text-body-lg">Sentinel Drift Monitor</span>
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
        const statuses = ["READY", "POLLING", "SYCHRONIZING", "MONITORING", "ANALYZING"];
        let statusIndex = 0;
        setInterval(() => {
            statusIndex = (statusIndex + 1) % statuses.length;
            consoleMsg.innerHTML = `<span class="material-symbols-outlined text-[16px]">terminal</span> SYS_MON_${statuses[statusIndex]}`;
        }, 5000);
    </script>
<aside class="fixed top-0 right-0 h-full w-[380px] translate-x-full transition-transform duration-500 ease-in-out z-[60] flex flex-col font-body-lg" id="floating-dashboard" style="background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-left: 1px solid rgba(255, 255, 255, 0.1); shadow: -10px 0 30px rgba(0,0,0,0.5);"><div class="p-container-margin flex flex-col h-full gap-gutter overflow-y-auto custom-scrollbar"><div class="flex items-center justify-between mb-stack-md"><div class="flex flex-col"><h2 class="font-headline-lg text-title-md text-on-surface">Architectural Pulse</h2><div class="flex items-center gap-unit text-[12px] text-secondary"><span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>System Nominal</div></div><button class="p-2 hover:bg-white/10 rounded-full transition-colors" id="dashboard-close"><span class="material-symbols-outlined">close</span></button></div><div class="bg-white/5 rounded-xl p-panel-padding border border-white/10"><span class="font-label-caps text-[10px] text-on-surface-variant/70 block mb-unit uppercase tracking-widest">Critical Drift</span><div class="flex items-baseline gap-stack-sm"><span class="text-display-lg text-[32px] text-error font-bold">1.24%</span><span class="text-error text-[12px]">+0.05% today</span></div><div class="mt-stack-sm h-1 w-full bg-white/10 rounded-full overflow-hidden"><div class="h-full bg-error w-[65%]"></div></div></div><div class="flex flex-col gap-stack-md"><span class="font-label-caps text-[10px] text-on-surface-variant/70 uppercase tracking-widest">Awaiting Ratification</span><div class="space-y-stack-sm"><div class="bg-white/5 p-stack-md rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer"><div class="flex justify-between text-[11px] font-mono-precision text-primary mb-1"><span>LOOM_MAINFRAME_B2</span><span>4h left</span></div><div class="text-body-sm">Structural Integrity Check</div></div><div class="bg-white/5 p-stack-md rounded-lg border border-white/5 hover:border-primary/30 transition-colors cursor-pointer"><div class="flex justify-between text-[11px] font-mono-precision text-primary mb-1"><span>CORE_EXPANSION_P7</span><span>6h left</span></div><div class="text-body-sm">Resource Allocation Drift</div></div></div></div><div class="flex flex-col gap-stack-md mt-auto"><span class="font-label-caps text-[10px] text-on-surface-variant/70 uppercase tracking-widest">Contextual Activity</span><div class="space-y-stack-md text-[13px]"><div class="flex gap-stack-md"><span class="material-symbols-outlined text-secondary text-[18px]">bolt</span><p class="text-on-surface-variant"><strong class="text-on-surface">Forge</strong> optimized Hyperion_V4 lattice.</p></div><div class="flex gap-stack-md"><span class="material-symbols-outlined text-primary text-[18px]">enable</span><p class="text-on-surface-variant"><strong class="text-on-surface">Engine</strong> corrected sector 7G anomaly.</p></div></div></div></div></aside><script>const dash = document.getElementById('floating-dashboard'); const toggle = document.getElementById('dashboard-toggle'); const close = document.getElementById('dashboard-close'); toggle.addEventListener('click', () => { dash.classList.remove('translate-x-full'); }); close.addEventListener('click', () => { dash.classList.add('translate-x-full'); });</script></body></html>

<!-- Apple: Topological Observatory (w/ Dashboard) -->
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>LOOM BLUEPRINT | Topological Observatory</title>
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