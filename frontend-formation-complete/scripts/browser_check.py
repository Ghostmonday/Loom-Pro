#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEBROOT = ROOT / ".generated" / "loom"
REPORT = ROOT / "reports" / "browser-check.json"

POLYFILL = r"""
<script>
(function installOpaqueOriginStorage() {
  const store = globalThis.__loomBrowserTestStorage || (globalThis.__loomBrowserTestStorage = new Map());
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem(key) { key = String(key); return store.has(key) ? store.get(key) : null; },
      setItem(key, value) { store.set(String(key), String(value)); },
      removeItem(key) { store.delete(String(key)); },
      clear() { store.clear(); },
      key(index) { return Array.from(store.keys())[index] ?? null; },
      get length() { return store.size; }
    }
  });
})();
</script>
"""


def assembled_html(screen: str) -> str:
    directory = WEBROOT / screen
    html = (directory / "index.html").read_text(encoding="utf-8")
    css = (
        (directory / "screen.css").read_text(encoding="utf-8")
        + "\n"
        + (directory / "screen.custom.css").read_text(encoding="utf-8")
    )
    mock = (directory / "mock-driver.js").read_text(encoding="utf-8")
    shell = (directory / "shell.js").read_text(encoding="utf-8")
    custom = (directory / "screen.custom.js").read_text(encoding="utf-8")

    html = re.sub(r'\s*<link rel="stylesheet" href="screen(?:\.custom)?\.css">', "", html)
    html = html.replace('<script src="mock-driver.js"></script>', f"{POLYFILL}<script>{mock}</script>")
    html = html.replace('<script src="shell.js"></script>', f"<script>{shell}</script>")
    html = html.replace('<script src="screen.custom.js"></script>', f"<script>{custom}</script>")
    html = html.replace("</head>", f"<style>{css}</style></head>")
    return html


def load_screen(page, screen: str):
    page.set_content(assembled_html(screen), wait_until="load")
    page.wait_for_selector("#screen-root")


def semantic_snapshot(page):
    return page.eval_on_selector_all(
        "[data-classification]",
        """nodes => nodes.map(n => ({
      id: n.id,
      classification: n.getAttribute('data-classification'),
      action: n.getAttribute('data-action'),
      contractPath: n.getAttribute('data-contract-path'),
      feedbackTarget: n.getAttribute('data-feedback-target')
    }))""",
    )


def activate(page, control_id: str, feedback_id: str, method: str = "mouse", expected: str = "succeeded"):
    if method == "keyboard":
        page.locator(f"#{control_id}").focus()
        page.keyboard.press("Enter")
    else:
        page.click(f"#{control_id}")
    page.wait_for_function(
        "([id]) => document.getElementById(id)?.textContent.startsWith('[pending]')",
        arg=[feedback_id],
        timeout=1000,
    )
    page.wait_for_function(
        "([id, state]) => document.getElementById(id)?.textContent.startsWith('[' + state + ']')",
        arg=[feedback_id, expected],
        timeout=2500,
    )
    return page.locator(f"#{feedback_id}").inner_text()


def main() -> int:
    results = {
        "passed": True,
        "execution_mode": "Chromium set_content with generated HTML/CSS/JS inlined; localStorage polyfilled because network and file navigation are administrator-blocked in this environment.",
        "checks": [],
        "console_errors": [],
        "page_errors": [],
    }

    with sync_playwright() as pw:
        exec_path = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
        browser = pw.chromium.launch(headless=True, executable_path=exec_path, args=["--no-sandbox"])
        page = browser.new_page()
        page.on("console", lambda msg: results["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: results["page_errors"].append(str(exc)))

        # Mock the sessions POST API endpoint to simulate the real backend response
        def handle_post_session(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                json={
                    "session_id": "0123456789ab",
                    "session_status": "QUESTIONING",
                    "current_question": {
                        "question_id": "q_test",
                        "text": "Which authority boundaries must the system enforce without exception?",
                        "domain": "governance",
                    },
                    "readiness": {"score": 0.25},
                    "latest_analysis": {"rationale": "Prompt accepted; evidence-state analysis initialized."},
                },
            )

        page.route("**/api/v1/intent-forge/sessions", handle_post_session)

        # Mock the answers POST API endpoint to simulate the real backend questioning response loop
        answers_calls = [0]

        def handle_post_answers(route):
            answers_calls[0] += 1
            if answers_calls[0] == 1:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    json={
                        "session_id": "0123456789ab",
                        "session_status": "QUESTIONING",
                        "current_question": {
                            "question_id": "q_test_2",
                            "text": "What failure or refusal states must remain distinct in the final system?",
                            "domain": "governance",
                        },
                        "latest_analysis": {
                            "readiness": {"score": 0.58},
                            "rationale": "Authority boundaries confirmed; failure semantics remain unresolved.",
                        },
                        "blueprint_version": 2,
                    },
                )
            else:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    json={
                        "session_id": "0123456789ab",
                        "session_status": "FINALIZED",
                        "current_question": None,
                        "latest_analysis": {
                            "readiness": {"score": 0.91},
                            "rationale": "Authority, failure semantics, and operational intent confirmed.",
                        },
                        "blueprint_version": 3,
                    },
                )

        page.route("**/api/v1/intent-forge/sessions/*/answers", handle_post_answers)

        # Prove a real gate refusal before running the canonical path.
        load_screen(page, "terminal")
        page.evaluate("localStorage.clear()")
        load_screen(page, "terminal")
        rejection = activate(page, "terminal-assign-swarm-btn", "terminal-feedback", expected="rejected")
        results["checks"].append(
            {"name": "terminal rejects swarm before prepare", "passed": rejection.startswith("[rejected]")}
        )

        # Canonical genesis path: Vision -> Command Engine -> Terminal -> Deliverable.
        load_screen(page, "vision_canvas")
        page.evaluate("localStorage.clear()")
        load_screen(page, "vision_canvas")
        before = semantic_snapshot(page)
        activate(page, "vision-start-btn", "vision-feedback")
        activate(page, "vision-submit-answer-btn", "vision-feedback", method="keyboard")
        activate(page, "vision-submit-answer-btn", "vision-feedback")
        activate(page, "vision-confirm-handoff-btn", "vision-feedback")
        activate(page, "vision-accept-handoff-btn", "vision-feedback")
        results["checks"].append({"name": "vision keyboard activation", "passed": True})
        results["checks"].append(
            {"name": "vision contract metadata stable", "passed": before == semantic_snapshot(page)}
        )

        load_screen(page, "command_engine")
        before = semantic_snapshot(page)
        activate(page, "command-deliberate-btn", "command-feedback")
        activate(page, "command-synthesize-btn", "command-feedback")
        activate(page, "command-prepare-btn", "command-feedback")
        results["checks"].append(
            {
                "name": "command action-specific progression",
                "passed": "prepared=true" in page.locator("#command-approval-display").inner_text(),
            }
        )
        results["checks"].append(
            {"name": "command contract metadata stable", "passed": before == semantic_snapshot(page)}
        )

        load_screen(page, "terminal")
        before = semantic_snapshot(page)
        for control in (
            "terminal-assign-swarm-btn",
            "terminal-deploy-btn",
            "terminal-poll-grid-btn",
            "terminal-merge-btn",
            "terminal-poll-merge-btn",
            "terminal-download-btn",
            "terminal-diff-btn",
        ):
            activate(page, control, "terminal-feedback")
        results["checks"].append(
            {
                "name": "terminal merge completes cleanly",
                "passed": "blocked=0" in page.locator("#terminal-merge-display").inner_text()
                and "ready=true" in page.locator("#terminal-deliverable-display").inner_text(),
            }
        )
        results["checks"].append(
            {"name": "terminal contract metadata stable", "passed": before == semantic_snapshot(page)}
        )

        load_screen(page, "deliverable_launch")
        before = semantic_snapshot(page)
        for control in (
            "deliverable-detect-btn",
            "deliverable-present-btn",
            "deliverable-open-browser-btn",
            "deliverable-download-btn",
            "deliverable-diff-btn",
            "deliverable-register-btn",
        ):
            activate(page, control, "deliverable-feedback")
        results["checks"].append(
            {
                "name": "deliverable launch and lineage",
                "passed": "state=succeeded" in page.locator("#deliverable-run-display").inner_text()
                and "registered=true" in page.locator("#deliverable-lineage-display").inner_text(),
            }
        )
        results["checks"].append(
            {"name": "deliverable contract metadata stable", "passed": before == semantic_snapshot(page)}
        )

        # Independent continuation branch.
        load_screen(page, "continuation")
        before = semantic_snapshot(page)
        for control in (
            "continuation-attach-btn",
            "continuation-resume-btn",
            "continuation-kind-btn",
            "continuation-bootstrap-btn",
            "continuation-mode-btn",
            "continuation-answer-btn",
            "continuation-scope-btn",
            "continuation-confirm-handoff-btn",
            "continuation-accept-handoff-btn",
        ):
            activate(page, control, "continuation-feedback")
        results["checks"].append(
            {
                "name": "continuation reaches handed off",
                "passed": "accepted=true" in page.locator("#continuation-handoff-display").inner_text(),
            }
        )
        results["checks"].append(
            {"name": "continuation contract metadata stable", "passed": before == semantic_snapshot(page)}
        )

        browser.close()

    results["passed"] = (
        all(check["passed"] for check in results["checks"])
        and not results["console_errors"]
        and not results["page_errors"]
    )
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
