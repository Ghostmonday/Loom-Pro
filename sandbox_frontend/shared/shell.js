/**
 * Loom Blueprint Workbench — Unified Shell
 *
 * Single shared shell for all workspace pages.
 * Handles: state management, hash-based routing, shell rendering,
 * workspace loading, and component interactions.
 *
 * Every page uses the same TopNavBar, SideNavBar, BottomConsole,
 * FloatingDashboard, and RightInspector. Only the central workspace
 * content changes between pages.
 */

(function () {
  "use strict";

  /* ═══════════════════════════════════════════════════════════
   *  WORKSPACE REGISTRY
   * ═══════════════════════════════════════════════════════════ */

  var WORKSPACES = {
    "hub": {
      label: "Project Hub",
      navGroup: "hub",
      sidebarTool: "navigate",
      url: "workspaces/hub.html",
      icon: "dashboard",
      defaultTooltip: "Navigate"
    },
    "intent-forge": {
      label: "Intent Forge",
      navGroup: "forge",
      sidebarTool: "inspect",
      url: "workspaces/intent-forge.html",
      icon: "straighten",
      defaultTooltip: "Inspect"
    },
    "blueprint-ratification": {
      label: "Blueprint Ratification",
      navGroup: "blueprint",
      sidebarTool: "graph-layout",
      url: "workspaces/blueprint-ratification.html",
      icon: "architecture",
      defaultTooltip: "Graph Layout"
    },
    "claims-ledger": {
      label: "Claims Ledger",
      navGroup: "claims",
      sidebarTool: "graph-layout",
      url: "workspaces/claims-ledger.html",
      icon: "architecture",
      defaultTooltip: "Graph Layout"
    },
    "curvature-analysis": {
      label: "Curvature Analysis",
      navGroup: "analysis",
      sidebarTool: "graph-layout",
      url: "workspaces/curvature-analysis.html",
      icon: "architecture",
      defaultTooltip: "Graph Layout"
    },
    "drift-monitor": {
      label: "Drift Monitor",
      navGroup: "pipeline",
      sidebarTool: "inspect",
      url: "workspaces/drift-monitor.html",
      icon: "straighten",
      defaultTooltip: "Inspect"
    },
    "packet-export": {
      label: "Packet Export",
      navGroup: "export",
      sidebarTool: "graph-layout",
      url: "workspaces/packet-export.html",
      icon: "architecture",
      defaultTooltip: "Graph Layout"
    },
    "topological-observatory": {
      label: "Topological Observatory",
      navGroup: "observatory",
      sidebarTool: "visibility",
      url: "workspaces/topological-observatory.html",
      icon: "visibility",
      defaultTooltip: "Visibility"
    }
  };

  /* Pipeline stage order for navigation */
  var PIPELINE_STAGES = [
    { id: "hub",                label: "Hub",              icon: "dashboard" },
    { id: "intent-forge",       label: "Intent Forge",     icon: "straighten" },
    { id: "claims-ledger",      label: "Claims",           icon: "layers" },
    { id: "blueprint-ratification", label: "Ratification", icon: "architecture" },
    { id: "curvature-analysis", label: "Curvature",        icon: "architecture" },
    { id: "topological-observatory", label: "Observatory", icon: "visibility" },
    { id: "drift-monitor",      label: "Drift",            icon: "straighten" },
    { id: "packet-export",      label: "Export",           icon: "terminal" }
  ];

  var STAGE_LOCKS = {
    hub: {
      unlockedByDefault: true,
      reason: "The hub is always available."
    },
    "intent-forge": {
      unlockedByDefault: true,
      reason: "Start here. Capture the product intent before blueprint work."
    },
    "claims-ledger": {
      requiredStage: "intent-forge",
      requiredLabel: "Start an Intent Forge session",
      reason: "Claims require session-backed evidence before they can be inspected."
    },
    "blueprint-ratification": {
      requiredStage: "claims-ledger",
      requiredLabel: "Reach final blueprint confirmation",
      reason: "Ratification is only meaningful after Loom validates enough claims and requirements."
    },
    "curvature-analysis": {
      requiredStage: "blueprint-ratification",
      requiredLabel: "Finalize or hand off the blueprint",
      reason: "Curvature analysis needs a real graph projection, not an empty intake state."
    },
    "topological-observatory": {
      requiredStage: "curvature-analysis",
      requiredLabel: "Finalize or hand off the blueprint",
      reason: "The observatory opens once Loom has a real topology to inspect."
    },
    "drift-monitor": {
      requiredStage: "topological-observatory",
      requiredLabel: "Create a finalized topology",
      reason: "Drift monitoring compares topology over time, so it requires a finalized baseline."
    },
    "packet-export": {
      requiredStage: "drift-monitor",
      requiredLabel: "Complete blueprint handoff",
      reason: "Exports are locked until a blueprint packet exists."
    }
  };

  /* SideBar tool definitions */
  var SIDEBAR_TOOLS = [
    { id: "navigate",      icon: "near_me",        tooltip: "Navigate" },
    { id: "inspect",       icon: "straighten",     tooltip: "Inspect" },
    { id: "graph-layout",  icon: "architecture",   tooltip: "Graph Layout" },
    { id: "boundaries",    icon: "layers",         tooltip: "Boundaries" },
    { id: "visibility",    icon: "visibility",     tooltip: "Visibility" },
    { id: "terminal",      icon: "terminal",       tooltip: "Terminal", optional: true }
  ];

  /* ═══════════════════════════════════════════════════════════
   *  STATE
   * ═══════════════════════════════════════════════════════════ */

  var state = {
    currentWorkspace: null,
    activeTool: "inspect",
    consoleTab: "log",
    dashboardOpen: false,
    searchQuery: "",
    inspectorVisible: true,
    previousWorkspace: null
  };

  function stageStorageKey(stageId) {
    return "loom.stage." + stageId + ".unlocked";
  }

  function isStageUnlocked(stageId) {
    var lock = STAGE_LOCKS[stageId];
    if (!lock) return true;
    if (lock.unlockedByDefault) return true;
    return localStorage.getItem(stageStorageKey(stageId)) === "true";
  }

  function unlockStage(stageId) {
    if (!STAGE_LOCKS[stageId]) return;
    localStorage.setItem(stageStorageKey(stageId), "true");
    if (dom.topnav) renderTopNav();
  }

  function unlockStages(stageIds) {
    stageIds.forEach(unlockStage);
  }

  function resetStageLocks() {
    Object.keys(STAGE_LOCKS).forEach(function (stageId) {
      if (!STAGE_LOCKS[stageId].unlockedByDefault) {
        localStorage.removeItem(stageStorageKey(stageId));
      }
    });
    if (dom.topnav) renderTopNav();
  }

  function stageLabel(stageId) {
    var ws = WORKSPACES[stageId];
    return ws ? ws.label : stageId;
  }

  function renderLockedWorkspace(workspaceId) {
    var lock = STAGE_LOCKS[workspaceId] || {};
    var nextStage = lock.requiredStage || "intent-forge";
    var nextLabel = lock.requiredLabel || ("Open " + stageLabel(nextStage));
    dom.workspace.innerHTML =
      '<div class="workspace-shell min-h-[62vh] flex items-center justify-center">' +
      '<div class="glass-panel rounded-xl p-container-margin max-w-2xl text-center space-y-stack-lg">' +
      '<span class="material-symbols-outlined text-primary/80 text-[44px]">lock</span>' +
      '<div>' +
      '<div class="workspace-kicker mb-stack-sm">Stage locked</div>' +
      '<h1 class="font-headline-lg text-headline-lg text-on-surface">' + stageLabel(workspaceId) + '</h1>' +
      '<p class="font-body-lg text-body-lg text-on-surface-variant/80 mt-stack-md">' + (lock.reason || "This stage is not ready yet.") + '</p>' +
      '</div>' +
      '<button class="px-6 py-2 bg-primary text-on-primary font-bold rounded-xl hover:opacity-90 active:scale-95 transition-all" data-open-required-stage="' + nextStage + '">' + nextLabel + '</button>' +
      '</div>' +
      '</div>';
    var button = dom.workspace.querySelector("[data-open-required-stage]");
    if (button) {
      button.addEventListener("click", function () {
        navigateTo(button.getAttribute("data-open-required-stage"));
      });
    }
  }

  /* ═══════════════════════════════════════════════════════════
   *  DOM CACHE
   * ═══════════════════════════════════════════════════════════ */

  var dom = {};

  function cacheDom() {
    dom = {
      workspace: document.getElementById("workspace-content"),
      topnav: document.getElementById("shell-topnav"),
      sidenav: document.getElementById("shell-sidenav"),
      console: document.getElementById("shell-console"),
      dashboard: document.getElementById("shell-dashboard"),
      inspector: document.getElementById("shell-inspector"),
      brand: document.getElementById("shell-brand"),
      navLinks: document.getElementById("shell-nav-links"),
      searchInput: document.getElementById("shell-search"),
      settingsBtn: document.getElementById("shell-settings"),
      helpBtn: document.getElementById("shell-help"),
      avatar: document.getElementById("shell-avatar"),
      toolContainer: document.getElementById("shell-tools"),
      versionLabel: document.getElementById("shell-version"),
      consoleTabs: document.getElementById("console-tabs"),
      consoleContent: document.getElementById("console-content"),
      dashboardPanel: document.getElementById("dashboard-panel"),
      dashboardToggle: document.getElementById("dashboard-toggle"),
      dashboardClose: document.getElementById("dashboard-close"),
      inspectorPanel: document.getElementById("shell-inspector"),
      userAvatar: document.getElementById("shell-avatar-img")
    };
  }

  /* ═══════════════════════════════════════════════════════════
   *  SHELL RENDERERS
   * ═══════════════════════════════════════════════════════════ */

  function renderTopNav() {
    var html = '<div class="flex items-center gap-stack-lg">' +
      '<span id="shell-brand" class="font-display-lg text-title-md font-bold text-primary tracking-tight cursor-pointer">Loom Blueprint Workbench</span>' +
      '<nav id="shell-nav-links" class="hidden md:flex items-center gap-1 ml-gutter">';

    PIPELINE_STAGES.forEach(function (ws) {
      var unlocked = isStageUnlocked(ws.id);
      var activeClass = ws.id === state.currentWorkspace
        ? 'text-primary font-bold border-b-2 border-primary'
        : unlocked
          ? 'text-on-surface-variant font-medium hover:text-primary'
          : 'text-on-surface-variant/35 font-medium cursor-not-allowed';
      var lockIcon = unlocked ? "" : '<span class="material-symbols-outlined text-[14px] align-[-2px] ml-1">lock</span>';
      html += '<a class="' + activeClass + ' font-body-lg text-body-lg px-2 py-1 spring-transition" data-workspace="' + ws.id + '" aria-disabled="' + (!unlocked) + '">' + ws.label + lockIcon + '</a>';
    });

    html += '</nav></div>' +
      '<div class="flex items-center gap-stack-md">' +
      '<div class="relative hidden sm:block">' +
      '<span class="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[14px] text-on-surface-variant opacity-50">search</span>' +
      '<input id="shell-search" class="bg-white/5 border border-white/10 rounded-lg text-[12px] pl-8 pr-3 py-1.5 w-44 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all placeholder:opacity-30 text-on-surface" placeholder="Search workspace..." type="text"/>' +
      '</div>' +
      '<button id="shell-settings" class="material-symbols-outlined text-on-surface-variant hover:text-on-surface hover:bg-white/10 p-1.5 rounded-lg spring-transition">settings</button>' +
      '<button id="shell-help" class="material-symbols-outlined text-on-surface-variant hover:text-on-surface hover:bg-white/10 p-1.5 rounded-lg spring-transition">help</button>' +
      '<div class="h-6 w-[1px] bg-white/10 mx-1"></div>' +
      '<div id="shell-avatar" class="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-secondary-fixed opacity-80 cursor-pointer"></div>' +
      '</div>';

    dom.topnav.innerHTML = html;

    // Re-bind nav link clicks
    dom.topnav.querySelectorAll('[data-workspace]').forEach(function (el) {
      el.addEventListener("click", function () {
        navigateTo(el.getAttribute("data-workspace"));
      });
    });

    dom.searchInput = document.getElementById("shell-search");
    dom.settingsBtn = document.getElementById("shell-settings");
    dom.helpBtn = document.getElementById("shell-help");
    dom.avatar = document.getElementById("shell-avatar");
  }

  function renderSideNav() {
    var html = '<div class="flex flex-col items-center gap-stack-lg w-full">';

    SIDEBAR_TOOLS.forEach(function (tool) {
      var isActive = tool.id === state.activeTool;
      var activeClass = isActive
        ? 'bg-secondary-container text-on-secondary-container rounded-xl shadow-[0_0_15px_rgba(71,226,102,0.3)]'
        : 'text-on-surface-variant hover:bg-surface-container-high rounded-xl';
      html += '<button class="w-10 h-10 flex items-center justify-center ' + activeClass + ' spring-transition" data-tool="' + tool.id + '" title="' + tool.tooltip + '">' +
        '<span class="material-symbols-outlined">' + tool.icon + '</span></button>';
    });

    html += '</div>' +
      '<div class="mt-auto flex flex-col items-center gap-stack-lg">' +
      '<span class="font-label-caps text-[10px] text-on-surface-variant/50 tracking-widest vertical-rl rotate-180 mb-stack-lg">V1.2</span>' +
      '</div>';

    dom.sidenav.innerHTML = html;

    // Bind tool clicks
    dom.sidenav.querySelectorAll('[data-tool]').forEach(function (el) {
      el.addEventListener("click", function () {
        var toolId = el.getAttribute("data-tool");
        state.activeTool = toolId;
        renderSideNav();
      });
    });
  }

  function renderConsole() {
    var tabs = ["Logs", "Timeline", "Output", "Debug"];
    var html = '<div class="flex items-center h-full px-container-margin gap-gutter">' +
      '<div id="console-tabs" class="flex items-center gap-stack-md">';

    tabs.forEach(function (tab) {
      var id = tab.toLowerCase();
      var activeClass = id === state.consoleTab
        ? 'text-primary font-bold border-b-2 border-primary'
        : 'text-on-surface-variant hover:text-primary';
      html += '<button class="font-body-sm text-body-sm ' + activeClass + ' spring-transition" data-console-tab="' + id + '">' + tab + '</button>';
    });

    html += '</div>' +
      '<div class="flex-1"></div>' +
      '<button id="dashboard-toggle" class="material-symbols-outlined text-on-surface-variant hover:text-primary cursor-pointer spring-transition" title="Architectural pulse">monitoring</button>' +
      '</div>';

    dom.console.innerHTML = html;

    // Bind console tab clicks
    dom.console.querySelectorAll('[data-console-tab]').forEach(function (el) {
      el.addEventListener("click", function () {
        state.consoleTab = el.getAttribute("data-console-tab");
        renderConsole();
      });
    });

    // Bind dashboard toggle
    var toggle = document.getElementById("dashboard-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        state.dashboardOpen = !state.dashboardOpen;
        dom.dashboardPanel.classList.toggle("open", state.dashboardOpen);
      });
    }

    dom.dashboardToggle = toggle;
  }

  function renderFloatingDashboard() {
    // Pre-rendered in HTML, just update visibility
    if (dom.dashboardClose) {
      dom.dashboardClose.addEventListener("click", function () {
        state.dashboardOpen = false;
        dom.dashboardPanel.classList.remove("open");
      });
    }
  }

  function renderRightInspector() {
    var content = document.getElementById("inspector-content");
    if (state.currentWorkspace === "hub") {
      dom.inspectorPanel.style.display = "none";
    } else {
      dom.inspectorPanel.style.display = "flex";
      if (content) {
        var ws = WORKSPACES[state.currentWorkspace] || WORKSPACES["intent-forge"];
        content.innerHTML =
          '<div class="inspector-card">' +
          '<div class="inspector-label">Active surface</div>' +
          '<div class="inspector-value">' + ws.label + '</div>' +
          '</div>' +
          '<div class="inspector-card">' +
          '<div class="inspector-label">Lifecycle</div>' +
          '<div class="inspector-value">Intent → Teleology → Blueprint → Sprint</div>' +
          '</div>' +
          '<div class="inspector-card">' +
          '<div class="inspector-label">Authority</div>' +
          '<div class="inspector-value">Backend state is canonical. UI is projection only.</div>' +
          '</div>';
      }
    }
  }

  /* ═══════════════════════════════════════════════════════════
   *  ROUTER
   * ═══════════════════════════════════════════════════════════ */

  function navigateTo(workspaceId) {
    if (!WORKSPACES[workspaceId]) {
      workspaceId = "hub";
    }
    if (workspaceId === state.currentWorkspace) return;

    state.previousWorkspace = state.currentWorkspace;
    state.currentWorkspace = workspaceId;
    state.activeTool = WORKSPACES[workspaceId].sidebarTool;
    state.inspectorVisible = (workspaceId !== "hub");

    // Update URL hash
    window.location.hash = workspaceId;

    // Re-render shell components
    renderTopNav();
    renderSideNav();
    renderConsole();
    renderRightInspector();

    if (!isStageUnlocked(workspaceId)) {
      renderLockedWorkspace(workspaceId);
      return;
    }

    // Load workspace content
    loadWorkspace(workspaceId);
  }

  function loadWorkspace(workspaceId) {
    var ws = WORKSPACES[workspaceId];
    if (!ws) return;

    // Show loading state
    dom.workspace.innerHTML = '<div class="workspace-loading">Loading ' + ws.label + '…</div>';

    // Fetch workspace content
    var xhr = new XMLHttpRequest();
    var separator = ws.url.indexOf("?") === -1 ? "?" : "&";
    xhr.open("GET", ws.url + separator + "v=ui-stage-locks-20260701", true);
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 400) {
        dom.workspace.innerHTML = xhr.responseText;
        // Execute any inline scripts in the workspace content
        dom.workspace.querySelectorAll("script").forEach(function (oldScript) {
          var newScript = document.createElement("script");
          Array.prototype.forEach.call(oldScript.attributes, function (attr) {
            newScript.setAttribute(attr.name, attr.value);
          });
          newScript.textContent = oldScript.textContent;
          oldScript.parentNode.replaceChild(newScript, oldScript);
        });
        // Notify workspace that it's been loaded
        var event = new CustomEvent("workspace-loaded", { detail: { id: workspaceId } });
        document.dispatchEvent(event);
      } else {
        dom.workspace.innerHTML = '<div class="workspace-loading">Failed to load workspace.</div>';
      }
    };
    xhr.onerror = function () {
      dom.workspace.innerHTML = '<div class="workspace-loading">Network error loading workspace.</div>';
    };
    xhr.send();
  }

  /* ═══════════════════════════════════════════════════════════
   *  HASH-BASED ROUTING
   * ═══════════════════════════════════════════════════════════ */

  function handleHashChange() {
    var hash = window.location.hash.replace("#", "");
    if (hash && WORKSPACES[hash]) {
      navigateTo(hash);
    } else {
      navigateTo("intent-forge");
    }
  }

  /* ═══════════════════════════════════════════════════════════
   *  SEARCH
   * ═══════════════════════════════════════════════════════════ */

  function setupSearch() {
    document.addEventListener("click", function (e) {
      var search = dom.searchInput;
      if (!search) return;
      if (e.target === search || search.contains(e.target)) {
        search.style.width = "220px";
      } else {
        search.style.width = "";
      }
    });
  }

  /* ═══════════════════════════════════════════════════════════
   *  INIT
   * ═══════════════════════════════════════════════════════════ */

  function init() {
    cacheDom();
    renderTopNav();
    renderSideNav();
    renderConsole();
    renderFloatingDashboard();
    renderRightInspector();
    setupSearch();

    // Listen for hash changes
    window.addEventListener("hashchange", handleHashChange);

    // Initial route
    var initialHash = window.location.hash.replace("#", "");
    if (initialHash && WORKSPACES[initialHash]) {
      navigateTo(initialHash);
    } else {
      navigateTo("intent-forge");
    }
  }

  // Wait for DOM
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose for debugging and external use
  window.LoomShell = {
    state: state,
    navigateTo: navigateTo,
    workspaces: WORKSPACES,
    loadWorkspace: loadWorkspace,
    isStageUnlocked: isStageUnlocked,
    unlockStage: unlockStage,
    unlockStages: unlockStages,
    resetStageLocks: resetStageLocks
  };

})();
