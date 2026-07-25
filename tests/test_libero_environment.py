from pathlib import Path

import numpy as np
import pytest

from libero_remote.environment.libero import (
    _controller_action_bounds,
    _resolve_task_bddl_file,
    _set_controller_mode,
)


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


@pytest.mark.parametrize(
    ("control_mode", "expected_use_delta"),
    [("relative", True), ("absolute", False)],
)
def test_controller_mode_is_applied_to_every_robot(
    control_mode: str, expected_use_delta: bool
) -> None:
    class Controller:
        use_delta = None

    class Robot:
        controller = Controller()

    class Environment:
        robots = [Robot(), Robot()]

    _set_controller_mode(Environment(), control_mode)

    assert all(robot.controller.use_delta is expected_use_delta for robot in Environment.robots)


def test_absolute_controller_bounds_accept_pose_and_axis_angle_targets() -> None:
    raw_low = np.full(7, -1.0, dtype=np.float32)
    raw_high = np.full(7, 1.0, dtype=np.float32)

    low, high = _controller_action_bounds(raw_low, raw_high, "absolute")

    model_action = np.array(
        [-0.01, 0.0, 0.89, 1.90, -2.21, -0.25, 1.0], dtype=np.float32
    )
    assert np.all(model_action >= low)
    assert np.all(model_action <= high)
    np.testing.assert_array_equal(low[-1:], raw_low[-1:])
    np.testing.assert_array_equal(high[-1:], raw_high[-1:])
