"""Keep the September 13 Spatial fixes task-local and reproducible."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import apply_goal_review_finalization as rules
from scripts.apply_feedback_task_fixes import case_slice, update_case

EXPECTED = {
    (0, 'S01'): {'offset_xy': ('0.0', '-0.075')},
    (0, 'S06'): {'asset_scale': ('0.6696',), 'grounded_height_offset_m': ('0.040',)},
    (4, 'S01'): {'offset_xy': ('-0.020', '-0.010')},
    (4, 'S05'): {'barrier_geometry_factors': ('1.0', '1.0', '3.1'),
                 'barrier_path_fraction': ('0.74',), 'ground_barrier_to_support': ('true',),
                 'support_surface': ('main_table',)},
    (4, 'S11'): {'asset_id': ('github/object_sim_bowl',), 'asset_scale': ('0.6696',),
                 'clutter_offsets_xy': ('0.10', '0.13'), 'clutter_minimum_gap_m': ('0.13',)},
    (7, 'S11'): {'clutter_offsets_xy': ('0.0', '0.19'), 'clutter_minimum_gap_m': ('0.13',)},
    (8, 'S03'): {'asset_id': ('generated/support_riser_wide_top',),
                 'asset_geometry_factors': ('1.0', '1.0', '3.0'), 'height_delta_m': ('0.090',)},
    (8, 'S06'): {'asset_scale': ('0.6696',), 'grounded_height_offset_m': ('0.080',)},
    (8, 'S10'): {'clutter_offsets_xy': ('0.20', '-0.18'),
                 'clutter_minimum_gap_m': ('0.14',), 'support_surface': ('main_table',)},
}


def entries():
    return {(e['suite'], e['base_task_id'], e['case_id']): e for e in
            json.loads((ROOT / 'assets/task_manifest.json').read_text())['tasks']}


@pytest.mark.parametrize('key', EXPECTED)
def test_published_parameters_and_hash(key):
    items = entries()
    entry = items[('libero_spatial', *key)]
    path = ROOT / 'assets' / entry['bddl_path']
    text = path.read_text()
    assert update_case(text, key[1], params=EXPECTED[key]) == text
    assert hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == entry['bddl_sha256']
    base = ROOT / 'assets' / items[('libero_spatial', key[0], 'BASE')]['bddl_path']
    assert text.split('(:perturbation_config')[0].strip() == base.read_text().split('(:perturbation_config')[0].strip()


def test_generation_overrides_are_limited_to_the_nine_cases(monkeypatch):
    assert set(rules.SPATIAL_REVIEW_0913_PARAMS) == set(EXPECTED)
    for key, expected in EXPECTED.items():
        params, _ = rules.case_updates('libero_spatial', *key)
        assert all(params[k] == v for k, v in expected.items())
    keys = [(suite, task, case) for suite in rules.SUITES for task in range(10)
            for case in rules.PUBLISHED_CASES
            if suite != 'libero_spatial' or (task, case) not in EXPECTED]
    before = {key: rules.case_updates(*key) for key in keys}
    monkeypatch.setattr(rules, 'SPATIAL_REVIEW_0913_PARAMS', {})
    assert all(rules.case_updates(*key) == before[key] for key in keys)


def test_s06_keeps_size_pose_and_grounding_contract():
    for task in (0, 8):
        entry = entries()[('libero_spatial', task, 'S06')]
        block = case_slice((ROOT / 'assets' / entry['bddl_path']).read_text(), 'S06')[2]
        for field in ('(:asset_scale 0.6696)', '(:asset_quat 1.0 0.0 0.0 0.0)',
                      '(:sampler_compatible true)', '(:grounded_replacement true)',
                      '(:support_surface main_table)'):
            assert field in block


@pytest.mark.parametrize('task,case', [(4, 'S11'), (7, 'S11'), (8, 'S10')])
def test_clutter_remains_movable_physical(task, case):
    entry = entries()[('libero_spatial', task, case)]
    block = case_slice((ROOT / 'assets' / entry['bddl_path']).read_text(), case)[2]
    for field in ('(:movable_asset true)', '(:physical_collision true)',
                  '(:visual_only_asset false)', '(:clear_of_task_entities true)'):
        assert field in block
