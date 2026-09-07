"""Task-local contracts for the Goal(5) review; no simulator dependency."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import types
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
SPEC = importlib.util.spec_from_file_location(
    '_goal5_parser', ROOT / 'simulator-source/libero/libero/envs/perturbation_config.py'
)
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)


def entries():
    manifest = json.loads((ASSETS / 'task_manifest.json').read_text(encoding='utf-8'))
    return {(int(t['base_task_id']), t['case_id']): t for t in manifest['tasks']
            if t['suite'] == 'libero_goal'}


def params(task, case):
    entry = entries()[task, case]
    path = ASSETS / entry['bddl_path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['bddl_sha256']
    config = PARSER.parse_bddl_perturbation_config(path)
    active = next(p for p in config['perturbations'] if str(p[0]).upper() == case)
    fields = {}
    for field in active[1:]:
        fields.update(field)
    return fields['params']


def test_goal1_d03_larger_movable_plate():
    p = params(1, 'D03')
    assert p['asset_id'] == 'prl/plastic_plate'
    assert p['asset_scale'] == 0.55
    assert p['asset_contact_margin_m'] == 0.004
    assert p['persistent_movable_asset'] is True


@pytest.mark.parametrize('task,factors', [(4, [1.0, 0.64, 1.20]), (9, [1.0, 0.90, 1.10])])
def test_s07_compiled_collisions_and_predicate_regions(task, factors):
    p = params(task, 'S07')
    assert p['geometry_factors'] == factors
    assert p['goal_region_scale'] == [1.0, 0.64 if task == 4 else 1.60, 1.20]
    assert p['scale_compiled_geometry'] is True


def test_goal7_d17_window_covers_the_interaction():
    p = params(7, 'D17')
    assert p['articulation_grasp_distance_m'] == 0.16
    assert p['recovery_retreat_m'] == 0.20
    assert p['event_duration_steps'] == 48


def test_goal3_d03_does_not_disguise_the_unfixed_success_predicate():
    p = params(3, 'D03')
    assert p['asset_id'] == 'github/object_sim_bowl'
    assert p['asset_scale'] == 0.55
    assert p['receiver_trigger_distance_m'] == 0.24


def test_goal3_d03_requires_drawer_contact_in_goal():
    entry = entries()[3, 'D03']
    text = (ASSETS / entry['bddl_path']).read_text(encoding='utf-8')
    goal = text.split('(:goal', 1)[1].split('(:perturbation_config', 1)[0]
    assert '(InSupported akita_black_bowl_1 wooden_cabinet_1_top_region)' in goal
    assert '(On akita_black_bowl_1 wooden_cabinet_1_top_region)' not in goal
    assert '(In akita_black_bowl_1 wooden_cabinet_1_top_region)' not in goal
    p = params(3, 'D03')
    assert p['goal_support_objects'] == 'wooden_cabinet_1'
    assert p['goal_support_normal_z_min'] == 0.70
    assert p['goal_max_linear_speed_m_s'] == 0.05
    assert p['goal_max_angular_speed_rad_s'] == 0.20


def _site_state_probe(*, support_contact=True, robot_contact=False):
    state_spec = importlib.util.spec_from_file_location(
        '_goal5_object_states',
        ROOT / 'simulator-source/libero/libero/envs/object_states/base_object_states.py',
    )
    state_module = importlib.util.module_from_spec(state_spec)
    # The probe only exercises predicate logic; keep it independent of the
    # optional robosuite installation used by the full simulator.
    robosuite = types.ModuleType('robosuite')
    robosuite_utils = types.ModuleType('robosuite.utils')
    transform_utils = types.ModuleType('robosuite.utils.transform_utils')
    transform_utils.mat2quat = lambda matrix: matrix
    robosuite.utils = robosuite_utils
    robosuite_utils.transform_utils = transform_utils
    previous_modules = {
        name: sys.modules.get(name)
        for name in ('robosuite', 'robosuite.utils', 'robosuite.utils.transform_utils')
    }
    sys.modules.update({
        'robosuite': robosuite,
        'robosuite.utils': robosuite_utils,
        'robosuite.utils.transform_utils': transform_utils,
    })
    try:
        state_spec.loader.exec_module(state_module)
    finally:
        for name, previous in previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    class Model:
        geom_bodyid = [1, 2, 3]
        body_parentid = [0, 0, 0, 0]
        nbody = 4

        @staticmethod
        def get_joint_qvel_addr(joint):
            return (0, 6)

        @staticmethod
        def body_id2name(body_id):
            return {0: 'world', 1: 'akita_black_bowl_1', 2: 'wooden_cabinet_1', 3: 'robot0_link0'}[body_id]

    contacts = []
    if support_contact:
        contacts.append(SimpleNamespace(geom1=0, geom2=1, frame=[0, 0, -1], pos=[0, 0, 1.0]))
    if robot_contact:
        contacts.append(SimpleNamespace(geom1=0, geom2=2, frame=[0, 0, 1], pos=[0, 0, 1.0]))
    env = SimpleNamespace(
        perturbation_plan=SimpleNamespace(params={
            'goal_support_objects': 'wooden_cabinet_1',
            'goal_support_normal_z_min': 0.70,
            'goal_support_contact_z_tolerance_m': 0.010,
            'goal_max_linear_speed_m_s': 0.05,
            'goal_max_angular_speed_rad_s': 0.20,
        }),
        obj_body_id={'akita_black_bowl_1': 1, 'wooden_cabinet_1': 2},
        get_object=lambda name: SimpleNamespace(joints=['akita_black_bowl_1_free_joint']),
        sim=SimpleNamespace(
            model=Model(),
            data=SimpleNamespace(
                body_xpos=[[0, 0, 0], [0, 0, 1.01], [0, 0, 1.0], [0, 0, 0]],
                qvel=[-0.00001, -0.00001, 0.02, 0.001, -0.005, 0.00001],
                cvel=[[0] * 6] * 4,
                ncon=len(contacts),
                contact=contacts,
            ),
        ),
    )
    site = state_module.SiteObjectState.__new__(state_module.SiteObjectState)
    site.env = env
    site.object_name = 'wooden_cabinet_1_top_region'
    site.check_contain = lambda other: True
    bowl = SimpleNamespace(env=env, object_name='akita_black_bowl_1')
    return site, bowl


def test_goal3_d03_supported_predicate_rejects_suspended_or_held_bowl():
    site, bowl = _site_state_probe(support_contact=False)
    assert site.check_placed_inside(bowl) is False

    site, bowl = _site_state_probe(robot_contact=True)
    assert site.check_placed_inside(bowl) is False


def test_goal3_d03_supported_predicate_accepts_released_bowl_on_drawer():
    site, bowl = _site_state_probe()
    assert site.check_placed_inside(bowl) is True


@pytest.mark.parametrize('task,case,name', [
    (3, 'S05', 'open_the_top_drawer_and_put_the_bowl_inside'),
    (9, 'D03', 'put_the_wine_bottle_on_the_rack'),
])
def test_only_explicitly_deleted_goal5_cases_are_absent(task, case, name):
    assert (task, case) not in entries()
    phase = '01_static' if case.startswith('S') else '02_dynamic'
    path = ASSETS / 'bddl/libero-pro2.0-1680-v1/libero_goal' / phase / f'{case}__{name}.bddl'
    assert not path.exists()
    assert (task, 'BASE') in entries()
