"""FFM-R002 — Screen Mission Singularity."""

from validator.core import Violation

RULE_NAME = "Screen Mission Singularity"


def check(manifest, document):
    violations = []
    mission = manifest.get("mission")
    mission_id = manifest.get("mission_id")
    manifest_screen = manifest.get("screen")

    if not mission:
        violations.append(Violation(
            "FFM-R002-01", "ERROR", "(screen manifest)",
            "Manifest does not declare a screen mission.", RULE_NAME,
        ))

    if len(document.screen_roots) == 0:
        violations.append(Violation(
            "FFM-R002-04", "ERROR", "(screen root)",
            f"No DOM root declares data-screen='{manifest_screen}'.",
            RULE_NAME, document.path,
        ))
        return violations

    if len(document.screen_roots) > 1:
        violations.append(Violation(
            "FFM-R002-05", "ERROR", "(screen roots)",
            f"Expected exactly one data-screen root; found {len(document.screen_roots)}.",
            RULE_NAME, document.path,
        ))

    root = document.screen_roots[0]
    if root.screen != manifest_screen:
        violations.append(Violation(
            "FFM-R002-04", "ERROR", root.ref,
            f"DOM data-screen '{root.screen}' does not match manifest screen '{manifest_screen}'.",
            RULE_NAME, document.path,
        ))

    if not root.mission:
        violations.append(Violation(
            "FFM-R002-02", "ERROR", root.ref,
            "DOM screen root has no data-mission declaration.",
            RULE_NAME, document.path,
        ))
    elif mission_id and root.mission != mission_id:
        violations.append(Violation(
            "FFM-R002-06", "ERROR", root.ref,
            f"DOM data-mission '{root.mission}' does not match manifest mission_id '{mission_id}'.",
            RULE_NAME, document.path,
        ))

    return violations
