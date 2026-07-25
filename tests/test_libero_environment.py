from pathlib import Path

import pytest

from libero_remote.environment.libero import _resolve_task_bddl_file


class _Suite:
    def get_task_bddl_file_path(self, task_id: int) -> str:
        return f"/legacy/task-{task_id}.bddl"


class _Task:
    problem_folder = "libero_goal"
    bddl_file = "open_the_drawer.bddl"


def test_task_bddl_uses_configured_asset_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bddl_file = tmp_path / "libero_goal" / _Task.bddl_file
    bddl_file.parent.mkdir()
    bddl_file.write_text("(define (problem test))", encoding="ascii")
    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(tmp_path))

    resolved = _resolve_task_bddl_file(_Suite(), _Task(), 0)

    assert resolved == str(bddl_file.resolve())


def test_task_bddl_falls_back_to_libero_suite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LIBERO_REMOTE_BDDL_ROOT", raising=False)

    assert _resolve_task_bddl_file(_Suite(), _Task(), 3) == "/legacy/task-3.bddl"


def test_task_bddl_rejects_missing_configured_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="Configured BDDL file does not exist"):
        _resolve_task_bddl_file(_Suite(), _Task(), 0)


def test_task_bddl_cannot_escape_configured_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class EscapingTask:
        problem_folder = ".."
        bddl_file = "outside.bddl"

    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(tmp_path))

    with pytest.raises(ValueError, match="outside LIBERO_REMOTE_BDDL_ROOT"):
        _resolve_task_bddl_file(_Suite(), EscapingTask(), 0)
