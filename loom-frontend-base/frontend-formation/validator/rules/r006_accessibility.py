"""FFM-R006 — Accessibility-Safe Defaults."""

from validator.core import Violation
from validator.parser.html_loader import INTERACTIVE_ROLES, NATIVE_ROLES

RULE_NAME = "Accessibility-Safe Defaults"
LIVE_ROLES = {"status", "alert"}


def check(document, manifest_elements_by_id):
    violations = []
    feedback_targets = {
        item.get("feedback_target")
        for item in manifest_elements_by_id.values()
        if item.get("classification") == "action_control" and item.get("feedback_target")
    }

    for el in document.elements:
        if el.tabindex_value is not None:
            try:
                tabindex = int(str(el.tabindex_value))
            except ValueError:
                tabindex = 1
            if tabindex > 0:
                violations.append(Violation(
                    "FFM-R006-01", "ERROR", el.ref,
                    "Positive tabindex disrupts logical DOM focus order.",
                    RULE_NAME, document.path,
                ))

        native_role = NATIVE_ROLES.get(el.tag)
        if el.tag == "a" and el.href:
            native_role = "link"
        if native_role and el.role == native_role:
            violations.append(Violation(
                "FFM-R006-02", "ERROR", el.ref,
                f"Native <{el.tag}> redundantly declares role='{el.role}'.",
                RULE_NAME, document.path,
            ))

        if el.classification == "input_control" and not el.associated_label_text.strip():
            violations.append(Violation(
                "FFM-R006-07", "ERROR", el.ref,
                "input_control requires an associated label element.",
                RULE_NAME, document.path,
            ))

        if el.classification == "action_control":
            if not el.accessible_name_present:
                violations.append(Violation(
                    "FFM-R006-03", "ERROR", el.ref,
                    "action_control has no accessible name.",
                    RULE_NAME, document.path,
                ))
            if not el.is_native_interactive:
                if el.role not in INTERACTIVE_ROLES:
                    violations.append(Violation(
                        "FFM-R006-04", "ERROR", el.ref,
                        "Custom action_control lacks a recognized interactive role.",
                        RULE_NAME, document.path,
                    ))
                if el.tabindex_value != "0":
                    violations.append(Violation(
                        "FFM-R006-05", "ERROR", el.ref,
                        "Custom action_control must use tabindex='0'.",
                        RULE_NAME, document.path,
                    ))

        if el.dom_id in feedback_targets:
            if el.aria_live not in {"polite", "assertive"} and el.role not in LIVE_ROLES:
                violations.append(Violation(
                    "FFM-R006-06", "ERROR", el.ref,
                    "Feedback display lacks aria-live or role=status/alert semantics.",
                    RULE_NAME, document.path,
                ))

    return violations
