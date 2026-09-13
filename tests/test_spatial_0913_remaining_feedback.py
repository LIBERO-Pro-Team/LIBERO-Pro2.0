"""Pin the three BDDL-only fixes without changing other Spatial cases."""
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
    (1, 'S11'): {'asset_scale': ('0.737',), 'clutter_minimum_gap_m': ('0.13',)},
    (4, 'D05'): {'asset_scale': ('2.15',), 'barrier_height_m': ('-0.20',),
                 'lateral_offset_m': ('0.0',), 'support_surface': ('main_table',)},
    (8, 'S05'): {'barrier_scale': ('0.65',),
                 'barrier_geometry_factors': ('1.0', '1.0', '2.4'),
                 'barrier_path_fraction': ('0.50',),
                 'barrier_lateral_offset_m': ('-0.12',),
                 'ground_barrier_to_support': ('true',), 'support_surface': ('main_table',)},
}


def entries():
    return {(e['suite'], e['base_task_id'], e['case_id']): e for e in
            json.loads((ROOT / 'assets/task_manifest.json').read_text())['tasks']}


@pytest.mark.parametrize('key', EXPECTED)
def test_published_parameters_hash_and_base_contract(key):
    items = entries()
    entry = items[('libero_spatial', *key)]
    path = ROOT / 'assets' / entry['bddl_path']
    text = path.read_text()
    assert update_case(text, key[1], params=EXPECTED[key]) == text
    canonical = path.read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    assert hashlib.sha256(canonical).hexdigest() == entry['bddl_sha256']
    base = ROOT / 'assets' / items[('libero_spatial', key[0], 'BASE')]['bddl_path']
    assert text.split('(:perturbation_config')[0].strip() == base.read_text().split('(:perturbation_config')[0].strip()


def test_generation_changes_only_the_three_authorized_keys(monkeypatch):
    assert rules.SPATIAL_REVIEW_0913_REMAINING_PARAMS == EXPECTED
    for key, expected in EXPECTED.items():
        params, _ = rules.case_updates('libero_spatial', *key)
        assert all(params[k] == value for k, value in expected.items())
    other = [(suite, task, case) for suite in rules.SUITES for task in range(10)
             for case in rules.PUBLISHED_CASES
             if suite != 'libero_spatial' or (task, case) not in EXPECTED]
    before = {key: rules.case_updates(*key) for key in other}
    monkeypatch.setattr(rules, 'SPATIAL_REVIEW_0913_REMAINING_PARAMS', {})
    assert all(rules.case_updates(*key) == before[key] for key in other)


def test_distractor_size_fix_keeps_asset_offset_and_mobility():
    entry = entries()[('libero_spatial', 1, 'S11')]
    block = case_slice((ROOT / 'assets' / entry['bddl_path']).read_text(), 'S11')[2]
    for field in ('(:asset_id github/object_sim_bowl)', '(:clutter_offsets_xy 0.10 -0.18)',
                  '(:movable_asset true)', '(:physical_collision true)',
                  '(:visual_only_asset false)', '(:clear_of_task_entities true)'):
        assert field in block


def test_paused_runtime_cases_are_not_in_the_parameter_patch():
    assert (5, 'D03') not in rules.SPATIAL_REVIEW_0913_REMAINING_PARAMS
    assert (6, 'D18') not in rules.SPATIAL_REVIEW_0913_REMAINING_PARAMS
