"""FFM-R007 — Continuous Smoke Verification."""

from validator.core import Violation

RULE_NAME = "Continuous Smoke Verification"
REQUIRED_KINDS = {
    "assert_initial_state",
    "perform_interaction",
    "assert_intermediate_feedback",
    "assert_terminal_state",
    "assert_contract_projection",
    "assert_accessibility_state",
    "assert_no_prohibited_side_effect",
}


def check(manifest, scenarios, manifest_elements_by_id):
    violations = []
    screen = manifest.get("screen")
    contract_paths = {
        item.get("contract_path")
        for item in manifest_elements_by_id.values()
        if item.get("classification") in {"display", "input_control"} and item.get("contract_path")
    }

    if not scenarios:
        violations.append(Violation(
            "FFM-R007-01", "ERROR", "(screen manifest)",
            "Screen has no loadable smoke scenario.", RULE_NAME,
        ))
        return violations

    seen_ids = set()
    for source, scenario in scenarios:
        scenario_id = scenario.get("scenario")
        if scenario_id in seen_ids:
            violations.append(Violation(
                "FFM-R007-07", "ERROR", scenario_id or "(scenario)",
                "Scenario id is duplicated.", RULE_NAME, source,
            ))
        seen_ids.add(scenario_id)

        if scenario.get("screen") != screen:
            violations.append(Violation(
                "FFM-R007-03", "ERROR", scenario_id or "(scenario)",
                f"Scenario screen '{scenario.get('screen')}' does not match manifest screen '{screen}'.",
                RULE_NAME, source,
            ))

        kinds = {step.get("kind") for step in scenario.get("steps", [])}
        missing = REQUIRED_KINDS - kinds
        if missing:
            violations.append(Violation(
                "FFM-R007-02", "ERROR", scenario_id or "(scenario)",
                f"Scenario lacks required step kind(s): {', '.join(sorted(missing))}.",
                RULE_NAME, source,
            ))

        for step in scenario.get("steps", []):
            kind = step.get("kind")
            target = step.get("target")
            if kind == "assert_contract_projection":
                if target not in contract_paths:
                    violations.append(Violation(
                        "FFM-R007-06", "ERROR", target or "(target)",
                        "Contract projection target is not a declared display contract path.",
                        RULE_NAME, source,
                    ))
                continue

            target_el = manifest_elements_by_id.get(target)
            if target_el is None:
                violations.append(Violation(
                    "FFM-R007-04", "ERROR", target or "(target)",
                    "Scenario target does not resolve to a manifest element id.",
                    RULE_NAME, source,
                ))
            elif kind == "perform_interaction" and target_el.get("classification") != "action_control":
                violations.append(Violation(
                    "FFM-R007-05", "ERROR", target,
                    "perform_interaction target is not an action_control.",
                    RULE_NAME, source,
                ))

    return violations
