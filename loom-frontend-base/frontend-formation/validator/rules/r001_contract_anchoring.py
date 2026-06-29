"""FFM-R001 — Contract Anchoring."""

from validator.core import Violation

RULE_NAME = "Contract Anchoring"


def check(document, action_registry):
    violations = []
    actions = (action_registry or {}).get("actions", {})

    for el in document.elements:
        if el.inline_handlers:
            violations.append(Violation(
                "FFM-R001-06", "ERROR", el.ref,
                f"Inline event handler(s) {', '.join(el.inline_handlers)} bypass the declarative action contract.",
                RULE_NAME, document.path,
            ))

        if el.is_semantic_interactive and not el.classification:
            violations.append(Violation(
                "FFM-R001-01", "ERROR", el.ref,
                "Semantic interactive element has no data-classification.",
                RULE_NAME, document.path,
            ))
            continue

        if not el.classification:
            continue

        if el.classification == "action_control":
            if not el.action:
                violations.append(Violation(
                    "FFM-R001-02", "ERROR", el.ref,
                    "action_control has no data-action.", RULE_NAME, document.path,
                ))
            elif el.action not in actions:
                violations.append(Violation(
                    "FFM-R001-03", "ERROR", el.ref,
                    f"Action '{el.action}' is not declared in the action registry.",
                    RULE_NAME, document.path,
                ))
            if not el.dom_id:
                violations.append(Violation(
                    "FFM-R001-07", "ERROR", el.ref,
                    "action_control has no stable id for manifest and feedback references.",
                    RULE_NAME, document.path,
                ))

        elif el.classification in {"display", "input_control"}:
            if not el.contract_path:
                violations.append(Violation(
                    "FFM-R001-04", "ERROR", el.ref,
                    f"{el.classification} has no data-contract-path.", RULE_NAME, document.path,
                ))
            if el.classification == "input_control" and el.tag not in {"input", "textarea"}:
                violations.append(Violation(
                    "FFM-R001-08", "ERROR", el.ref,
                    "input_control must be rendered as input or textarea.", RULE_NAME, document.path,
                ))
            if not el.dom_id:
                violations.append(Violation(
                    "FFM-R001-07", "ERROR", el.ref,
                    f"{el.classification} has no stable id for manifest and projection references.",
                    RULE_NAME, document.path,
                ))

        elif el.classification == "presentation":
            leaked = [name for name, value in (
                ("data-action", el.action),
                ("data-contract-path", el.contract_path),
                ("data-feedback-target", el.feedback_target),
            ) if value]
            if leaked:
                violations.append(Violation(
                    "FFM-R001-05", "ERROR", el.ref,
                    f"presentation node leaks semantic binding(s): {', '.join(leaked)}.",
                    RULE_NAME, document.path,
                ))

    return violations
