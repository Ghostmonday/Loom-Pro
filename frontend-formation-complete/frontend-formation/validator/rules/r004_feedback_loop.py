"""FFM-R004 — Guaranteed Feedback Loop."""

from validator.core import Violation

RULE_NAME = "Guaranteed Feedback Loop"
REQUIRED_LIFECYCLE_STATES = {"accepted", "pending", "succeeded", "rejected", "failed", "cancelled", "timed_out"}


def check(document, manifest_elements_by_id, action_registry):
    violations = []
    dom_by_id = document.elements_by_id
    actions = (action_registry or {}).get("actions", {})

    for el in document.elements:
        if el.classification != "action_control":
            continue

        target = el.feedback_target
        if not target:
            violations.append(
                Violation(
                    "FFM-R004-01",
                    "ERROR",
                    el.ref,
                    "action_control has no data-feedback-target.",
                    RULE_NAME,
                    document.path,
                )
            )
        else:
            target_dom = dom_by_id.get(target)
            if target_dom is None:
                violations.append(
                    Violation(
                        "FFM-R004-02",
                        "ERROR",
                        el.ref,
                        f"Feedback target '{target}' does not exist in the DOM.",
                        RULE_NAME,
                        document.path,
                    )
                )
            elif target_dom.classification != "display":
                violations.append(
                    Violation(
                        "FFM-R004-06",
                        "ERROR",
                        el.ref,
                        (
                            f"Feedback target '{target}' is classified "
                            f"'{target_dom.classification}' in the DOM, not display."
                        ),
                        RULE_NAME,
                        document.path,
                    )
                )

            target_manifest = manifest_elements_by_id.get(target)
            if target_manifest is None:
                violations.append(
                    Violation(
                        "FFM-R004-05",
                        "ERROR",
                        el.ref,
                        f"Feedback target '{target}' has no manifest entry.",
                        RULE_NAME,
                        document.path,
                    )
                )
            elif target_manifest.get("classification") != "display":
                violations.append(
                    Violation(
                        "FFM-R004-05",
                        "ERROR",
                        el.ref,
                        f"Feedback target '{target}' is not display-classified in the manifest.",
                        RULE_NAME,
                        document.path,
                    )
                )

        if el.action and el.action in actions:
            states = set(actions[el.action].get("lifecycle_states", []))
            missing = REQUIRED_LIFECYCLE_STATES - states
            if missing:
                violations.append(
                    Violation(
                        "FFM-R004-03",
                        "ERROR",
                        el.ref,
                        f"Action '{el.action}' lacks lifecycle state(s): {', '.join(sorted(missing))}.",
                        RULE_NAME,
                        document.path,
                    )
                )

    return violations
