"""Exercise task-local recovery and keep all other task plans unchanged."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.apply_feedback_task_fixes import update_case

ENVS = ROOT / 'simulator-source/libero/libero/envs'
ASSETS = ENVS.parent / 'assets/perturbation_assets'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rt = load('_spatial_recovery_runtime', ENVS / 'nonphysical_perturbations.py')
parser = load('_spatial_recovery_parser', ENVS / 'perturbation_config.py')
FLAGS = {(5, 'D03'): 'preserve_settled_task_poses', (6, 'D18'): 'reset_drop_velocity'}


def task_path(task, case):
    entries = json.loads((ROOT / 'assets/task_manifest.json').read_text())['tasks']
    entry = next(e for e in entries if (e['suite'], e['base_task_id'], e['case_id']) ==
                 ('libero_spatial', task, case))
    return ROOT / 'assets' / entry['bddl_path']


def config_with_flag(tmp_path, task, case, enabled=True):
    path = tmp_path / task_path(task, case).name
    path.write_text(update_case(task_path(task, case).read_text(), case,
                               params={FLAGS[task, case]: ('true' if enabled else 'false',)}))
    return parser.parse_bddl_perturbation_config(path)


def environment():
    names = ['world', 'akita_black_bowl_1', 'plate_1', 'perturbation_d03_0', 'other']
    positions = np.array([[0, 0, 0], [0, 0, 1.08], [.3, .2, .97], [-.4, .4, 3], [-.4, -.4, .9]])
    quats = np.tile([1., 0., 0., 0.], (5, 1))
    velocities = np.arange(24, dtype=float).reshape(4, 6) / 20
    joints = {name + '_joint': index - 1 for index, name in enumerate(names) if index}
    data = SimpleNamespace(body_xpos=positions, body_xquat=quats, qvel=velocities.ravel(),
                           ncon=0, contact=[], site_xpos=np.array([[0., 0., 1.2]]))

    def set_qpos(joint, value):
        positions[joints[joint] + 1] = value[:3]
        quats[joints[joint] + 1] = value[3:]

    data.set_joint_qpos = set_qpos
    data.set_joint_qvel = lambda joint, value: velocities.__setitem__(joints[joint], value)
    model = SimpleNamespace(nbody=5, ngeom=1, body_pos=positions, body_quat=quats,
                            body_parentid=np.array([-1, 0, 0, 0, 0]), body_gravcomp=np.zeros(5),
                            geom_bodyid=np.array([3]), geom_contype=np.array([1]),
                            geom_conaffinity=np.array([1]), geom_group=np.array([0]),
                            jnt_type=np.zeros(4, dtype=int), jnt_dofadr=np.arange(4) * 6,
                            joint_name2id=lambda name: joints[name], body_id2name=lambda i: names[i])
    return SimpleNamespace(
        obj_body_id={name: i for i, name in enumerate(names) if i},
        objects_dict={name: SimpleNamespace(joints=[name + '_joint']) for name in names[1:]},
        object_sites_dict={}, object_states_dict={}, workspace_offset=np.array([0., 0., .9]),
        parsed_problem={'goal_state': [['on', 'akita_black_bowl_1', 'plate_1']], 'regions': {}},
        robots=[SimpleNamespace(eef_site_id=0)], sim=SimpleNamespace(model=model, data=data, forward=lambda: None))


@pytest.mark.parametrize('enabled', [True, False])
@pytest.mark.parametrize('repeat', [False, True])
def test_d03_preserves_settled_entities_only_when_enabled(tmp_path, enabled, repeat):
    plan = rt.build_execution_plan(config_with_flag(tmp_path, 5, 'D03', enabled), ASSETS)
    env = environment()
    runtime = rt.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime.apply_static(env)
    if repeat:
        runtime.begin_rollout(env)
    old = {name: pose[0].copy() for name, pose in runtime._saved_poses.items()}
    env.sim.data.body_xpos[1, 2] = .934
    env.sim.data.body_xpos[2, 2] = .9025
    settled = env.sim.data.body_xpos.copy()
    velocity_before = env.sim.data.qvel.copy()
    runtime.begin_rollout(env)
    for name in ('akita_black_bowl_1', 'plate_1'):
        expected = settled[env.obj_body_id[name]] if enabled else old[name]
        np.testing.assert_array_equal(rt._entity_pose(env, name)[0], expected)
        np.testing.assert_array_equal(runtime._saved_poses[name][0], expected)
    np.testing.assert_array_equal(env.sim.data.qvel[:12], velocity_before[:12])
    np.testing.assert_array_equal(env.sim.data.qvel[18:], velocity_before[18:])
    np.testing.assert_array_equal(env.sim.data.body_xpos[3], [0, 0, -5])
    np.testing.assert_array_equal(env.sim.data.qvel[12:18], 0)
    assert env.sim.model.geom_contype[0] == 0
    assert not runtime._dynamic_applied


@pytest.mark.parametrize('enabled', [True, False])
def test_d18_clears_only_target_velocity_once(tmp_path, enabled):
    plan = rt.build_execution_plan(config_with_flag(tmp_path, 6, 'D18', enabled), ASSETS)
    env = environment()
    env.sim.data.body_xpos[1, 2] = .93
    runtime = rt.NonPhysicalPerturbationRuntime(plan, seed=143)
    runtime.apply_static(env)
    runtime.begin_rollout(env)
    env.sim.data.body_xpos[1, 2] = 1.2
    env.sim.data.qvel[:6] = [.8, 0, .3, 0, 3, 0]
    before = env.sim.data.qvel.copy()
    other_poses = env.sim.data.body_xpos[2:].copy()
    runtime.previous_action = np.array([0, 0, 0, 0, 0, 0, 1.])
    runtime.before_simulation_step(env, 1)
    assert runtime._dynamic_applied
    np.testing.assert_array_equal(env.sim.data.qvel[:6], np.zeros(6) if enabled else before[:6])
    np.testing.assert_array_equal(env.sim.data.qvel[6:], before[6:])
    np.testing.assert_array_equal(env.sim.data.body_xpos[2:], other_poses)
    assert np.linalg.norm(env.sim.data.body_xpos[1, :2]) == pytest.approx(.1)
    assert env.sim.data.body_xpos[1, 2] == pytest.approx(.93)
    env.sim.data.qvel[:6] = 1.0
    runtime.before_simulation_step(env, 2)
    np.testing.assert_array_equal(env.sim.data.qvel[:6], 1.)


@pytest.mark.parametrize('key', FLAGS)
@pytest.mark.parametrize('change', ['suite', 'task', 'case', 'target'])
def test_scoped_flags_reject_wrong_task_identity(tmp_path, key, change):
    config = config_with_flag(tmp_path, *key)
    if change == 'suite':
        config['source_suite'] = 'libero_object'
    elif change == 'task':
        config['source_task'] = 'pick_up_the_black_bowl_next_to_the_plate_and_place_it_on_the_plate'
    elif change == 'case':
        other = 'D18' if key[1] == 'D03' else 'D03'
        config['active_cases'] = config['case_id'] = other
        rt._case_entries(config)[other]['params'][FLAGS[key]] = True
    else:
        # The parsed target field is a scalar, so mutate its source dictionary.
        for row in config['perturbations']:
            if str(row[0]).upper() == key[1]:
                for field in row[1:]:
                    if isinstance(field, dict) and 'targets' in field:
                        field['targets'] = 'akita_black_bowl_2'
    with pytest.raises(rt.PerturbationConfigurationError, match='restricted'):
        rt.build_execution_plan(config, ASSETS)


def test_published_flags_and_generator_are_limited_to_two_tasks():
    from scripts import apply_goal_review_finalization as rules
    entries = json.loads((ROOT / 'assets/task_manifest.json').read_text())['tasks']
    enabled = {}
    for entry in entries:
        path = ROOT / 'assets' / entry['bddl_path']
        config = parser.parse_bddl_perturbation_config(path)
        plan = rt.build_execution_plan(config, ASSETS)
        for flag in FLAGS.values():
            if plan.params.get(flag):
                enabled[flag] = enabled.get(flag, []) + [(entry['suite'], entry['base_task_id'], entry['case_id'])]
    for key, flag in FLAGS.items():
        assert enabled.get(flag) == [('libero_spatial', *key)]
        params, _ = rules.case_updates('libero_spatial', *key)
        assert params[flag] == ('true',)
        entry = next(e for e in entries if (e['suite'], e['base_task_id'], e['case_id']) == ('libero_spatial', *key))
        data = task_path(*key).read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        assert hashlib.sha256(data).hexdigest() == entry['bddl_sha256']
