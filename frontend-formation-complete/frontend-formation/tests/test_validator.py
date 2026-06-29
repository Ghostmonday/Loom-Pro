from pathlib import Path

from validator.engine import validate_project

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
