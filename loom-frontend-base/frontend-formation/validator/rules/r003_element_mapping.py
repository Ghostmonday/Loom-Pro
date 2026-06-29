"""FFM-R003 — Strict Element Mapping and exact binding parity."""

from validator.core import Violation
from validator.parser.manifest_loader import element_id_counts

RULE_NAME = "Strict Element Mapping"
VALID_CLASSIFICATIONS = {"action_control", "display", "presentation", "input_control"}


def check(document, manifest, manifest_elements_by_id):
    violations = []

    for duplicate_id in sorted(document.duplicate_ids):
        violations.append(Violation(
            "FFM-R003-09", "ERROR", f"#{duplicate_id}",
            "DOM id is duplicated; references are ambiguous.",
            RULE_NAME, document.path,
        ))

    for duplicate_id, count in sorted(element_id_counts(manifest).items()):
        if count > 1:
            violations.append(Violation(
                "FFM-R003-10", "ERROR", f"#{duplicate_id} (manifest)",
                f"Manifest id is declared {count} times; dictionary normalization would hide entries.",
                RULE_NAME,
            ))

    dom_by_id = document.elements_by_id
    for el in document.elements:
        if el.classification and el.classification not in VALID_CLASSIFICATIONS:
            violations.append(Violation(
                "FFM-R003-01", "ERROR", el.ref,
                f"Invalid data-classification '{el.classification}'.",
                RULE_NAME, document.path,
            ))

        if not el.dom_id:
            continue
        manifest_el = manifest_elements_by_id.get(el.dom_id)
        if el.classification and manifest_el is None:
            violations.append(Violation(
                "FFM-R003-02", "ERROR", el.ref,
                "Classified DOM element has no manifest entry.",
                RULE_NAME, document.path,
            ))
            continue
        if manifest_el is None:
            continue

        expected_class = manifest_el.get("classification")
        if el.classification != expected_class:
            violations.append(Violation(
                "FFM-R003-03", "ERROR", el.ref,
                f"DOM classification '{el.classification}' does not match manifest classification '{expected_class}'.",
                RULE_NAME, document.path,
            ))

        if expected_class == "action_control":
            if el.action != manifest_el.get("action"):
                violations.append(Violation(
                    "FFM-R003-06", "ERROR", el.ref,
                    f"DOM action '{el.action}' does not match manifest action '{manifest_el.get('action')}'.",
                    RULE_NAME, document.path,
                ))
            if el.feedback_target != manifest_el.get("feedback_target"):
                violations.append(Violation(
                    "FFM-R003-08", "ERROR", el.ref,
                    f"DOM feedback target '{el.feedback_target}' does not match manifest feedback target '{manifest_el.get('feedback_target')}'.",
                    RULE_NAME, document.path,
                ))
        elif expected_class in {"display", "input_control"}:
            if el.contract_path != manifest_el.get("contract_path"):
                violations.append(Violation(
                    "FFM-R003-07", "ERROR", el.ref,
                    f"DOM contract path '{el.contract_path}' does not match manifest contract path '{manifest_el.get('contract_path')}'.",
                    RULE_NAME, document.path,
                ))
            if expected_class == "input_control" and el.tag != manifest_el.get("tag"):
                violations.append(Violation(
                    "FFM-R003-11", "ERROR", el.ref,
                    f"DOM tag '{el.tag}' does not match manifest tag '{manifest_el.get('tag')}'.",
                    RULE_NAME, document.path,
                ))

    for manifest_id in manifest_elements_by_id:
        if manifest_id not in dom_by_id:
            violations.append(Violation(
                "FFM-R003-05", "ERROR", f"#{manifest_id} (manifest only)",
                "Manifest declares an element with no corresponding DOM element.",
                RULE_NAME,
            ))

    return violations
