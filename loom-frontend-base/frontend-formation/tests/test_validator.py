from pathlib import Path

import pytest
import yaml
from generator.core import GenerationError, generate_scaffold
from validator.engine import validate_project
from validator.parser.manifest_loader import SchemaValidationError, load_manifest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specification"


def test_passing_project_is_clean():
    result = validate_project(ROOT / "examples/passing/frontend-formation.yaml", SPEC)
    assert result.passed, [v.to_dict() for v in result.violations]
    assert result.checked_screens == 1
    assert result.error_count == 0


def test_failing_project_exercises_all_rule_families():
    result = validate_project(ROOT / "examples/failing/frontend-formation.yaml", SPEC)
    assert not result.passed
    codes = {v.code for v in result.violations}
    for family in range(1, 8):
        prefix = f"FFM-R00{family}-"
        assert any(code.startswith(prefix) for code in codes), (family, sorted(codes))
    assert "FFM-R003-06" in codes
    assert "FFM-R003-07" in codes
    assert "FFM-R003-08" in codes
    assert "FFM-R003-09" in codes
    assert "FFM-R003-10" in codes
    assert "FFM-R004-06" in codes
    assert "FFM-R002-05" in codes


def _vision_manifest():
    with open(ROOT.parent / "examples/loom-source/vision-canvas.manifest.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_input_control_manifest_schema_accepts_supported_attributes(tmp_path):
    manifest = _vision_manifest()
    target = tmp_path / "manifest.yaml"
    target.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    loaded = load_manifest(target, SPEC)
    prompt = next(item for item in loaded["elements"] if item["id"] == "vision-prompt-input")
    assert prompt["classification"] == "input_control"
    assert prompt["tag"] == "textarea"


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda element: element.pop("contract_path"), "contract_path"),
        (lambda element: element.update({"tag": "div"}), "'div' is not one of"),
        (lambda element: element.pop("label"), "label"),
        (lambda element: element.update({"type": "checkbox"}), "'checkbox' is not one of"),
    ],
)
def test_input_control_schema_rejects_malformed_manifests(tmp_path, mutate, expected):
    manifest = _vision_manifest()
    element = next(item for item in manifest["elements"] if item["id"] == "vision-prompt-input")
    mutate(element)
    target = tmp_path / "manifest.yaml"
    target.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    with pytest.raises(SchemaValidationError) as exc:
        load_manifest(target, SPEC)
    assert expected in "\n".join(exc.value.errors)


def test_input_control_generator_rejects_duplicate_ids(tmp_path):
    manifest = _vision_manifest()
    manifest["elements"].append(dict(manifest["elements"][0]))
    target = tmp_path / "manifest.yaml"
    target.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    with pytest.raises(GenerationError) as exc:
        generate_scaffold(
            target,
            ROOT.parent / "examples/loom-source/actions.registry.yaml",
            ROOT.parent / "examples/loom-source/knowledge.registry.yaml",
            tmp_path / "generated",
            SPEC,
        )
    assert "FFM-R003-10" in str(exc.value)
