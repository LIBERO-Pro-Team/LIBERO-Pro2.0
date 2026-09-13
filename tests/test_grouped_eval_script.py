import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_grouped_eval.py"


def _module():
    spec = importlib.util.spec_from_file_location("run_grouped_eval", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_supports_group_suite_case_and_matrix_selection() -> None:
    args = _module().parse_args(
        [
            "plan",
            "--group",
            "dynamic",
            "--split",
            "test",
            "--suite",
            "libero_goal",
            "--case",
            "D07",
            "--seeds",
            "42",
            "43",
            "--init-state-ids",
            "0",
            "1",
            "--matrix",
            "--control-mode",
            "absolute",
        ]
    )

    assert args.group == "dynamic"
    assert args.split == "test"
    assert args.suites == ["libero_goal"]
    assert args.cases == ["D07"]
    assert args.seeds == [42, 43]
    assert args.init_state_ids == [0, 1]
    assert args.matrix is True
    assert args.control_mode == "absolute"


def test_seed_range_shorthand_is_deterministic() -> None:
    module = _module()

    assert module.resolve_seeds(None, 42, 3) == [42, 43, 44]
    assert module.resolve_seeds([7, 9], None, 1) == [7, 9]
    with pytest.raises(ValueError, match="only be combined"):
        module.resolve_seeds([7, 9], None, 2)
