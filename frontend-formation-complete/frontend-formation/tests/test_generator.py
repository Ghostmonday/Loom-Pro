from pathlib import Path

from generator.core import generate_scaffold
from validator.engine import validate_project

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specification"
SOURCE = ROOT / "examples/source"


def snapshot(directory: Path):
    return {
        str(path.relative_to(directory)): path.read_bytes() for path in sorted(directory.rglob("*")) if path.is_file()
    }


def test_generator_is_closed_under_validation_and_deterministic(tmp_path):
    output = tmp_path / "generated"
    result = generate_scaffold(
        SOURCE / "screen.manifest.yaml",
        SOURCE / "actions.registry.yaml",
        SOURCE / "knowledge.registry.yaml",
        output,
        SPEC,
    )
    assert result.passed
    first = snapshot(output)
    custom_js = output / "screen.custom.js"
    custom_js.write_text("// user extension\n", encoding="utf-8")

    result = generate_scaffold(
        SOURCE / "screen.manifest.yaml",
        SOURCE / "actions.registry.yaml",
        SOURCE / "knowledge.registry.yaml",
        output,
        SPEC,
        force=True,
    )
    assert result.passed
    second = snapshot(output)
    assert second["screen.custom.js"] == b"// user extension\n"
    first["screen.custom.js"] = b"// user extension\n"
    assert second == first

    validated = validate_project(output / "frontend-formation.yaml", SPEC)
    assert validated.passed, [v.to_dict() for v in validated.violations]
