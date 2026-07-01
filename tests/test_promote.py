from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest
from aoc_cli.commands.promote import _find_promote_sh, _find_vault_root, _run_vault_linter, promote_cmd
from typer import Typer
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def temp_vault(tmp_path):
    vault = tmp_path / "my-vault"
    vault.mkdir()
    (vault / ".gaijinn" / "bridge").mkdir(parents=True)
    (vault / ".gaijinn" / "bridge" / "council.md").touch()
    (vault / "10_Operations").mkdir()
    (vault / "10_Operations" / "knowledge-linter.py").touch()
    (vault / "10_Operations" / "promote.sh").touch()
    return vault


def test_find_vault_root_success(temp_vault, monkeypatch):
    monkeypatch.chdir(temp_vault)
    assert _find_vault_root(temp_vault) == temp_vault


def test_find_vault_root_walk_up(temp_vault, monkeypatch):
    subdir = temp_vault / "some" / "nested" / "dir"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    assert _find_vault_root(subdir) == temp_vault


def test_find_vault_root_not_found(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    # Mock home to avoid hitting real home
    with patch("pathlib.Path.home", return_value=tmp_path / "fake-home"):
        assert _find_vault_root(empty) is None


def test_run_vault_linter_success(temp_vault):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="All good", stderr="")
        assert _run_vault_linter(temp_vault) is True
        mock_run.assert_called_once()


def test_run_vault_linter_failure(temp_vault):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="Violations", stderr="Error")
        assert _run_vault_linter(temp_vault) is False


def test_run_vault_linter_missing(tmp_path):
    assert _run_vault_linter(tmp_path) is False


def test_find_promote_sh_primary(temp_vault):
    expected = temp_vault / "10_Operations" / "agents" / "promoter" / "promote.sh"
    expected.parent.mkdir(parents=True)
    expected.touch()
    assert _find_promote_sh(temp_vault) == expected


def test_find_promote_sh_fallback(temp_vault):
    expected = temp_vault / "10_Operations" / "promote.sh"
    # Ensure primary doesn't exist
    primary = temp_vault / "10_Operations" / "agents" / "promoter" / "promote.sh"
    if primary.exists():
        primary.unlink()
    assert _find_promote_sh(temp_vault) == expected


class TestPromoteCmd:
    @pytest.fixture
    def app(self):
        # Disable rich for tests to avoid capture issues with ANSI codes
        app = Typer(add_completion=False, rich_markup_mode=None)
        # Explicit name to avoid promote-cmd vs promote issues
        app.command(name="promote")(promote_cmd)
        # Adding a dummy command forces sub-command help mode
        app.command(name="dummy")(lambda: None)
        return app

    def test_promote_help(self, app):
        result = runner.invoke(app, ["promote", "--help"], color=False)
        assert result.exit_code == 0

        # Robust check: strip ANSI and underscores/hyphens normalization
        clean_output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.output)
        normalized_output = clean_output.lower().replace("_", "-")

        assert "vault-root" in normalized_output
        assert "list-files" in normalized_output
        assert "skip-linter" in normalized_output

    def test_promote_cmd_success(self, app, temp_vault, monkeypatch):
        monkeypatch.chdir(temp_vault)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
            result = runner.invoke(app, ["promote", "--vault-root", str(temp_vault)])
            assert result.exit_code == 0, result.output
            assert "Promotion complete" in result.output
            # 2 linter runs + 1 promote run
            assert mock_run.call_count == 3

    def test_promote_cmd_no_vault(self, app, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("pathlib.Path.home", return_value=tmp_path / "fake-home"):
            result = runner.invoke(app, ["promote"])
            assert result.exit_code == 1, result.output
            assert "ERROR: Could not detect vault root" in result.output

    def test_promote_cmd_list(self, app, temp_vault):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, ["promote", "--vault-root", str(temp_vault), "--list-files"])
            assert result.exit_code == 0, result.output
            mock_run.assert_called_once()
            assert "--list" in mock_run.call_args[0][0]

    def test_promote_cmd_skip_linter(self, app, temp_vault):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = runner.invoke(app, ["promote", "--vault-root", str(temp_vault), "--skip-linter"])
            assert result.exit_code == 0, result.output
            assert "Vault linter skipped" in result.output
            # Only 1 call (promote.sh)
            assert mock_run.call_count == 1

    def test_promote_cmd_linter_fail(self, app, temp_vault):
        with patch("subprocess.run") as mock_run:
            # First call is linter
            mock_run.return_value = MagicMock(returncode=1, stdout="Fail", stderr="")
            result = runner.invoke(app, ["promote", "--vault-root", str(temp_vault)])
            assert result.exit_code == 1, result.output
            assert "PRE-PROMOTION LINTER FAILED" in result.output
            assert mock_run.call_count == 1

    def test_promote_cmd_promote_fail(self, app, temp_vault):
        with patch("subprocess.run") as mock_run:
            # First call (linter) success, second (promote) fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="Linter OK"),
                MagicMock(returncode=1, stdout="Promote Fail"),
            ]
            result = runner.invoke(app, ["promote", "--vault-root", str(temp_vault)])
            assert result.exit_code == 1, result.output
            assert mock_run.call_count == 2
