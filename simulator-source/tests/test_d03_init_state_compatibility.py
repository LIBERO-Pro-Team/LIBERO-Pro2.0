import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


SIMULATOR_ROOT = Path(__file__).resolve().parents[1]
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

from libero.libero.envs.env_wrapper import _task_compatible_init_state


def _environment(*, opted_in: bool):
    current = np.arange(60, dtype=float) + 1000.0
    model = SimpleNamespace(
        nq=31,
        nv=28,
        jnt_type=np.array([0], dtype=int),
        jnt_qposadr=np.array([23], dtype=int),
        jnt_dofadr=np.array([21], dtype=int),
        joint_name2id=lambda _name: 0,
    )
    sim = SimpleNamespace(
        model=model,
        get_state=lambda: SimpleNamespace(flatten=lambda: current.copy()),
    )
    runtime = SimpleNamespace(
        _persistent_d03_obstacle_name=lambda: "perturbation_d03_0"
    )
    plan = SimpleNamespace(
        case_id="D03" if opted_in else "D04",
        params={"persistent_movable_asset": opted_in},
    )
    env = SimpleNamespace(
        perturbation_plan=plan,
        perturbation_runtime=runtime,
        objects_dict={
            "perturbation_d03_0": SimpleNamespace(joints=["obstacle_joint"])
        },
        sim=sim,
    )
    return env, current


def test_persistent_movable_d03_merges_one_free_joint_into_base_state() -> None:
    env, current = _environment(opted_in=True)
    incoming = np.arange(47, dtype=float)

    merged = _task_compatible_init_state(env, incoming)

    assert merged.shape == (60,)
    assert merged[0] == incoming[0]
    np.testing.assert_array_equal(merged[1:24], incoming[1:24])
    np.testing.assert_array_equal(merged[24:31], current[24:31])
    np.testing.assert_array_equal(merged[31:32], incoming[24:25])
    np.testing.assert_array_equal(merged[32:53], incoming[25:46])
    np.testing.assert_array_equal(merged[53:59], current[53:59])
    np.testing.assert_array_equal(merged[59:], incoming[46:])


def test_non_opted_in_task_keeps_strict_original_state() -> None:
    env, _ = _environment(opted_in=False)
    incoming = np.arange(47, dtype=float)

    result = _task_compatible_init_state(env, incoming)

    assert result is incoming


def test_static_distractor_merges_multiple_free_joints_into_base_state() -> None:
    old_nq = 24
    old_nv = 22
    current = np.arange(1 + 38 + 34, dtype=float) + 1000.0
    model = SimpleNamespace(
        nq=38,
        nv=34,
        jnt_type=np.array([0, 0], dtype=int),
        jnt_qposadr=np.array([10, 25], dtype=int),
        jnt_dofadr=np.array([9, 21], dtype=int),
        joint_name2id=lambda name: {"first_joint": 0, "second_joint": 1}[name],
    )
    env = SimpleNamespace(
        perturbation_plan=SimpleNamespace(
            case_id="S10", params={"movable_asset": True}
        ),
        perturbation_asset_injection=SimpleNamespace(
            injected_names=("perturbation_s10_0", "perturbation_s10_1")
        ),
        objects_dict={
            "perturbation_s10_0": SimpleNamespace(
                joints=["first_joint", "removed_internal_joint"]
            ),
            "perturbation_s10_1": SimpleNamespace(joints=["second_joint"]),
        },
        sim=SimpleNamespace(
            model=model,
            get_state=lambda: SimpleNamespace(flatten=lambda: current.copy()),
        ),
    )
    incoming = np.arange(1 + old_nq + old_nv, dtype=float)

    merged = _task_compatible_init_state(env, incoming)

    assert merged.shape == current.shape
    np.testing.assert_array_equal(merged[1:11], incoming[1:11])
    np.testing.assert_array_equal(merged[11:18], current[11:18])
    np.testing.assert_array_equal(merged[18:26], incoming[11:19])
    np.testing.assert_array_equal(merged[26:33], current[26:33])
    np.testing.assert_array_equal(merged[33:39], incoming[19:25])
    np.testing.assert_array_equal(merged[39:48], incoming[25:34])
    np.testing.assert_array_equal(merged[48:54], current[48:54])
    np.testing.assert_array_equal(merged[54:60], incoming[34:40])
    np.testing.assert_array_equal(merged[60:66], current[60:66])
    np.testing.assert_array_equal(merged[66:73], incoming[40:47])
