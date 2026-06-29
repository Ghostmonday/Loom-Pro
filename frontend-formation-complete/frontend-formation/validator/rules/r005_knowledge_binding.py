"""FFM-R005 — Five-Domain Knowledge Binding."""

from validator.core import Violation

RULE_NAME = "Five-Domain Knowledge Binding"
DOMAINS = ("design_intent", "behavioral", "operational", "governance", "institutional")


def check(manifest, knowledge_registry):
    violations = []
    declared = manifest.get("knowledge_bindings") or {}
    registry = (knowledge_registry or {}).get("bindings", {})

    for domain in DOMAINS:
        value = declared.get(domain)
        if value is None:
            violations.append(Violation(
                "FFM-R005-01", "ERROR", f"knowledge_bindings.{domain}",
                f"Missing required {domain} knowledge binding.", RULE_NAME,
            ))
            continue

        if isinstance(value, dict):
            if value.get("status") != "not_applicable" or len(str(value.get("justification", "")).strip()) < 10:
                violations.append(Violation(
                    "FFM-R005-04", "ERROR", f"knowledge_bindings.{domain}",
                    "not_applicable declaration requires status and a substantive justification.",
                    RULE_NAME,
                ))
            continue

        entry = registry.get(value)
        if entry is None:
            violations.append(Violation(
                "FFM-R005-02", "ERROR", f"knowledge_bindings.{domain}",
                f"Knowledge binding '{value}' is not declared in the knowledge registry.",
                RULE_NAME,
            ))
        elif entry.get("domain") != domain:
            violations.append(Violation(
                "FFM-R005-03", "ERROR", f"knowledge_bindings.{domain}",
                f"Knowledge binding '{value}' belongs to domain '{entry.get('domain')}', not '{domain}'.",
                RULE_NAME,
            ))

    return violations
