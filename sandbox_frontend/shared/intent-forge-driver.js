(function () {
  "use strict";

  var API_PREFIX = "/api/v1/intent-forge";
  var ACTIVE_STATUSES = ["QUESTIONING", "CONFLICT_RESOLUTION"];
  var FINALIZE_STATUSES = ["QUESTIONING", "VALIDATING"];

  function $(id) { return document.getElementById(id); }
  function explicitMockEnabled() {
    var qs = new URLSearchParams(window.location.search || "");
    return qs.get("loom_driver") === "mock" || qs.get("demo") === "1" || window.LOOM_USE_MOCK_DRIVER === true;
  }
  function uuid() {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      var v = c === "x" ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  function feedback(message, error) {
    var el = $("vision-feedback");
    if (!el) return;
    el.textContent = message || "";
    el.dataset.error = error ? "true" : "false";
    el.classList.toggle("text-error", !!error);
    el.classList.toggle("text-on-surface-variant", !error);
  }
  function setBusy(isBusy) {
    var overlay = $("analysis-overlay");
    if (overlay) {
      overlay.dataset.busy = isBusy ? "true" : "false";
      overlay.classList.toggle("hidden", !isBusy);
    }
  }
  function state() {
    window.LoomIntentForgeState = window.LoomIntentForgeState || {
      sessionId: null,
      sessionStatus: "CREATED",
      blueprintVersion: 0,
      currentQuestionId: null,
      answers: [],
      latestSession: null
    };
    return window.LoomIntentForgeState;
  }
  function headers() {
    return {
      "Content-Type": "application/json",
      "X-User-Id": localStorage.getItem("loom.user_id") || "terminal-user",
      "X-Loom-Api-Key": localStorage.getItem("loom.api_key") || ""
    };
  }
  function normalizeError(data, status) {
    if (status === 409) return "Version conflict. Reload the session state before continuing.";
    if (data && data.detail) return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    return "Request failed with status " + status;
  }
  function request(path, options) {
    return fetch(path, options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) throw new Error(normalizeError(data, response.status));
        return data;
      });
    });
  }
  function currentQuestion(data) {
    return data.current_question || data.question || null;
  }
  function setPanelVisible(id, visible) {
    var el = $(id);
    if (el) el.classList.toggle("hidden", !visible);
  }
  function render(data) {
    var s = state();
    s.latestSession = data;
    if (data.session_id) s.sessionId = data.session_id;
    if (data.session_status) s.sessionStatus = data.session_status;
    if (typeof data.blueprint_version === "number") s.blueprintVersion = data.blueprint_version;
    updateStageLocks(data);
    var hasSession = !!(s.sessionId || data.session_id);
    setPanelVisible("question-panel", hasSession);
    setPanelVisible("readiness-panel", hasSession);
    setPanelVisible("understanding-panel", hasSession);
    setPanelVisible("handoff-panel", hasSession);
    var question = currentQuestion(data);
    if (question) {
      s.currentQuestionId = question.id || question.question_id || null;
      $("question-text").textContent = question.text || question.prompt || "Answer the next question.";
      $("question-why").textContent = question.why || question.rationale || "Loom is interrogating the blueprint state.";
      var def = $("question-default");
      if (def) {
        var defaultText = question.default || question.default_answer || "";
        def.textContent = defaultText;
        def.classList.toggle("hidden", !defaultText);
      }
    }
    var readiness = (data.latest_analysis && data.latest_analysis.readiness) || data.readiness || {};
    var score = typeof readiness.score === "number" ? readiness.score : 0;
    $("readiness-score").textContent = score.toFixed(2);
    $("readiness-reason").textContent = readiness.reason || data.session_status || "Awaiting backend readiness.";
    var gate = $("readiness-gate");
    if (gate) gate.dataset.canHandoff = readiness.ready_to_finalize || data.session_status === "FINAL_CONFIRMATION" ? "true" : "false";
    renderUnderstanding(data);
    renderClaimsLedger(data);
    syncButtons();
  }
  function updateStageLocks(data) {
    if (!window.LoomShell || !window.LoomShell.unlockStages) return;
    var status = data.session_status || state().sessionStatus || "";
    var unlocks = [];
    if (data.session_id || state().sessionId || status) {
      unlocks.push("claims-ledger");
    }
    var gates = data.claims_ledger && data.claims_ledger.promotion_gates ? data.claims_ledger.promotion_gates : {};
    if (gates.blueprint_influence_available === true) {
      unlocks.push("blueprint-ratification");
    }
    if (status === "FINALIZED" || status === "HANDED_OFF") {
      unlocks.push("curvature-analysis", "topological-observatory");
    }
    if (status === "HANDED_OFF") {
      unlocks.push("drift-monitor", "packet-export");
    }
    if (unlocks.length) window.LoomShell.unlockStages(unlocks);
  }
  function renderUnderstanding(data) {
    var list = $("understanding-list");
    if (!list) return;
    var items = data.answers || data.answer_history || state().answers || [];
    if (!items.length && data.latest_analysis && data.latest_analysis.claims) items = data.latest_analysis.claims;
    list.innerHTML = "";
    if (!items.length) {
      list.innerHTML = '<li class="font-body-sm text-body-sm text-on-surface-variant py-stack-sm border-b border-outline-variant/20">No requirements yet captured.</li>';
      return;
    }
    items.forEach(function (item, index) {
      var li = document.createElement("li");
      li.className = "font-body-sm text-body-sm text-on-surface-variant py-stack-sm border-b border-outline-variant/20";
      var answer = item.answer || item.text || item.claim || JSON.stringify(item);
      var qid = item.question_id || item.id || ("answer-" + index);
      li.innerHTML = '<button class="text-primary mr-2" data-revise-question-id="' + qid + '">Revise</button>' + answer;
      list.appendChild(li);
    });
  }
  function text(value) {
    return String(value == null ? "" : value);
  }
  function html(value) {
    return text(value).replace(/[&<>"']/g, function (ch) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[ch];
    });
  }
  function setText(id, value) {
    var el = $(id);
    if (el) el.textContent = value;
  }
  function gate(id, passed) {
    var el = $(id);
    if (!el) return;
    el.textContent = passed ? "check_circle" : "radio_button_unchecked";
    el.classList.toggle("text-secondary", !!passed);
    el.classList.toggle("text-on-surface-variant", !passed);
  }
  function renderClaimsLedger(data) {
    var rows = $("claims-ledger-rows");
    if (!rows) return;
    var ledger = data && data.claims_ledger ? data.claims_ledger : {};
    var claims = Array.isArray(ledger.claims) ? ledger.claims : [];
    var gates = ledger.promotion_gates || {};
    setText("claims-ledger-status", claims.length ? "Session evidence loaded" : "Awaiting session evidence");
    setText("claims-ledger-evidence-count", ledger.evidence_packet_count || 0);
    setText("claims-ledger-evidence-note", claims.length ? "Evidence packets are session-backed." : "No Build session loaded.");
    setText("claims-ledger-promoted-count", ledger.promoted_count || 0);
    setText("claims-ledger-contradiction-count", ledger.contradiction_count || 0);
    setText("claims-ledger-contradiction-note", ledger.contradiction_count ? "Blocking contradictions require resolution." : "No real conflicts detected.");
    setText("claims-ledger-influence-state", gates.blueprint_influence_available ? "Open" : "Locked");
    setText("claims-ledger-influence-note", gates.blueprint_influence_available ? "Promoted claims can inform projection." : "Only verified claims may cross.");
    var promote = $("claims-ledger-promote");
    if (promote) {
      promote.disabled = gates.blueprint_influence_available !== true;
      promote.classList.toggle("opacity-50", promote.disabled);
      promote.classList.toggle("cursor-not-allowed", promote.disabled);
      promote.classList.toggle("bg-primary", !promote.disabled);
      promote.classList.toggle("text-on-primary", !promote.disabled);
      promote.classList.toggle("border-outline-variant/30", promote.disabled);
    }
    gate("claims-gate-evidence", gates.evidence_packet_received);
    gate("claims-gate-extracted", gates.claims_extracted_with_provenance);
    gate("claims-gate-contradictions", gates.contradictions_resolved_or_blocked);
    gate("claims-gate-influence", gates.blueprint_influence_available);

    var empty = $("claims-ledger-empty");
    rows.classList.toggle("hidden", !claims.length);
    if (empty) empty.classList.toggle("hidden", !!claims.length);
    rows.innerHTML = "";
    claims.forEach(function (claim) {
      var row = document.createElement("div");
      row.className = "grid grid-cols-[1.6fr_1fr_1fr_1fr] gap-gutter px-stack-lg py-stack-md items-center";
      var status = text(claim.promotion_status || "blocked");
      row.innerHTML =
        '<span class="font-body-sm text-body-sm text-on-surface">' + html(claim.text) + '</span>' +
        '<span class="font-mono-precision text-mono-precision text-on-surface-variant">' + html((claim.evidence_refs && claim.evidence_refs[0] && claim.evidence_refs[0].source_kind) || "evidence") + '</span>' +
        '<span class="font-mono-precision text-mono-precision text-on-surface-variant">' + html(claim.kind || "claim") + '</span>' +
        '<span><span class="px-2 py-0.5 rounded text-[10px] font-mono-precision uppercase ' +
        (status === "promoted" ? 'bg-secondary/10 text-secondary border border-secondary/30' : 'bg-tertiary/10 text-tertiary border border-tertiary/30') +
        '">' + html(status) + '</span></span>';
      rows.appendChild(row);
    });
  }
  function refreshClaimsLedger() {
    var s = state();
    if (!s.sessionId) {
      renderClaimsLedger(s.latestSession || {});
      return Promise.resolve();
    }
    return request(API_PREFIX + "/sessions/" + encodeURIComponent(s.sessionId) + "/claims-ledger", {
      method: "GET",
      headers: headers()
    }).then(function (ledger) {
      var latest = s.latestSession || {};
      latest.claims_ledger = ledger;
      s.latestSession = latest;
      updateStageLocks(latest);
      renderClaimsLedger(latest);
    }).catch(function (err) {
      feedback(err.message, true);
    });
  }
  function syncButtons() {
    var s = state();
    var prompt = $("prompt-input");
    var answer = $("answer-input");
    var start = $("btn-start-session");
    var submit = $("btn-submit-answer");
    var finalize = $("btn-finalize-now");
    var confirm = $("btn-confirm-handoff");
    var accept = $("btn-accept-handoff");
    if (start) start.disabled = !(prompt && prompt.value.trim());
    if (submit) submit.disabled = !(answer && answer.value.trim() && s.sessionId && s.currentQuestionId && ACTIVE_STATUSES.indexOf(s.sessionStatus) >= 0);
    if (finalize) finalize.disabled = !(s.sessionId && FINALIZE_STATUSES.indexOf(s.sessionStatus) >= 0);
    if (confirm) confirm.disabled = s.sessionStatus !== "FINAL_CONFIRMATION";
    if (accept) accept.disabled = s.sessionStatus !== "FINALIZED";
  }
  function mutate(path, body) {
    body = body || {};
    body.idempotency_key = uuid();
    return request(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
  }
  var realDriver = {
    start: function () {
      var prompt = $("prompt-input").value.trim();
      if (!prompt) return feedback("Enter a vision before starting.", true);
      return mutate(API_PREFIX + "/sessions", { prompt: prompt, tier: "paid" });
    },
    submit: function () {
      var s = state();
      var answer = $("answer-input").value.trim();
      if (!answer || !s.sessionId || !s.currentQuestionId) return feedback("Answer input and active question are required.", true);
      return mutate(API_PREFIX + "/sessions/" + encodeURIComponent(s.sessionId) + "/answers", {
        question_id: s.currentQuestionId,
        answer: answer,
        expected_blueprint_version: s.blueprintVersion
      }).then(function (data) {
        s.answers.push({ question_id: s.currentQuestionId, answer: answer });
        $("answer-input").value = "";
        localStorage.removeItem("loom.answer_draft");
        return data;
      });
    },
    finalize: function () {
      var s = state();
      return mutate(API_PREFIX + "/sessions/" + encodeURIComponent(s.sessionId) + "/finalize", { expected_blueprint_version: s.blueprintVersion, force: false });
    },
    handoff: function (action) {
      var s = state();
      return mutate(API_PREFIX + "/sessions/" + encodeURIComponent(s.sessionId) + "/handoff", { action: action, expected_blueprint_version: s.blueprintVersion });
    },
    revise: function (questionId, answer) {
      var s = state();
      return mutate(API_PREFIX + "/sessions/" + encodeURIComponent(s.sessionId) + "/revise", { question_id: questionId, answer: answer, expected_blueprint_version: s.blueprintVersion });
    }
  };
  var mockDriver = {
    start: function () { return Promise.resolve({ session_id: "demo-session", session_status: "QUESTIONING", blueprint_version: 1, current_question: { id: "demo-q1", text: "What outcome must the software achieve first?", why: "Demo driver enabled explicitly." }, readiness: { score: 0.1, reason: "Demo session started." } }); },
    submit: function () { return Promise.resolve({ session_status: "VALIDATING", blueprint_version: 2, readiness: { score: 0.82, ready_to_finalize: true, reason: "Demo answer accepted." } }); },
    finalize: function () { return Promise.resolve({ session_status: "FINAL_CONFIRMATION", blueprint_version: 3, readiness: { score: 1, ready_to_finalize: true, reason: "Ready for confirmation." } }); },
    handoff: function (action) { return Promise.resolve({ session_status: action === "confirm" ? "FINALIZED" : "HANDED_OFF", blueprint_version: 4 }); },
    revise: function () { return Promise.resolve({ session_status: "QUESTIONING", blueprint_version: 5 }); }
  };
  function run(op) {
    setBusy(true);
    feedback("", false);
    var driver = explicitMockEnabled() ? mockDriver : realDriver;
    return op(driver).then(render).catch(function (err) { feedback(err.message, true); }).finally(function () { setBusy(false); syncButtons(); });
  }
  function initIntentForge() {
    if (!$("prompt-input") || $("prompt-input").dataset.bound === "true") return;
    $("prompt-input").dataset.bound = "true";
    $("prompt-input").value = localStorage.getItem("loom.prompt_draft") || "";
    $("answer-input").value = localStorage.getItem("loom.answer_draft") || "";
    ["prompt-input", "answer-input"].forEach(function (id) {
      var el = $(id);
      el.addEventListener("input", function () {
        localStorage.setItem(id === "prompt-input" ? "loom.prompt_draft" : "loom.answer_draft", el.value);
        syncButtons();
      });
    });
    $("btn-start-session").addEventListener("click", function () { run(function (d) { return d.start(); }); });
    $("btn-submit-answer").addEventListener("click", function () { run(function (d) { return d.submit(); }); });
    $("btn-finalize-now").addEventListener("click", function () { run(function (d) { return d.finalize(); }); });
    $("btn-confirm-handoff").addEventListener("click", function () { run(function (d) { return d.handoff("confirm"); }); });
    $("btn-accept-handoff").addEventListener("click", function () { run(function (d) { return d.handoff("accept"); }); });
    $("btn-undo-draft").addEventListener("click", function () { $("answer-input").value = ""; localStorage.removeItem("loom.answer_draft"); syncButtons(); });
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-revise-question-id]");
      if (!btn) return;
      var editor = $("vision-revision-editor");
      editor.dataset.questionId = btn.getAttribute("data-revise-question-id");
      editor.value = btn.parentElement.textContent.replace(/^Revise/, "").trim();
    });
    syncButtons();
    window.LoomIntentForgeDriver = { mode: explicitMockEnabled() ? "mock" : "api", real: realDriver, mock: mockDriver };
  }
  document.addEventListener("workspace-loaded", function (event) { if (event.detail.id === "intent-forge") initIntentForge(); });
  document.addEventListener("workspace-loaded", function (event) {
    if (event.detail.id === "claims-ledger") refreshClaimsLedger();
  });
  if (document.readyState !== "loading") initIntentForge(); else document.addEventListener("DOMContentLoaded", initIntentForge);
})();
