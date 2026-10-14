import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


SIMULATOR_ROOT = Path(__file__).resolve().parents[1]
if str(SIMULATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_ROOT))

from libero.libero.envs import nonphysical_perturbations as runtime


def _plan(case_id: str, *, movable: bool) -> runtime.ExecutionPlan:
    return runtime.ExecutionPlan(
        case_id=case_id,
        schedule="static",
        operator="asset_or_appearance",
        variant="distractor",
        targets=("target_1",),
        references=("reference_1",),
        mechanisms=("asset",),
        assets=(runtime.AssetSpec("test/asset", Path("asset.xml"), staged=False),),
        params={"movable_asset": movable, "physical_collision": True},
    )


def test_static_distractor_requires_explicit_opt_in_to_be_movable() -> None:
    calls: list[tuple[str, str, object]] = []
    roots: list[ET.Element] = []

    class FakeObject:
        category_name = ""
        rotation = (0.0, 0.0)
        rotation_axis = "z"
        object_properties = {}

        def __init__(self, joints: object):
            self.joints = ["free_joint"] if joints == "default" else []
            self.root = ET.fromstring(
                '<body><geom name="collision" group="0" contype="1" '
                'conaffinity="1" type="box" size="0.02 0.02 0.02"/></body>'
            )

        def get_obj(self) -> ET.Element:
            return self.root

    def factory(path: str, *, name: str, joints: object) -> FakeObject:
        calls.append((path, name, joints))
        result = FakeObject(joints)
        roots.append(result.root)
        return result

    runtime.inject_plan_assets({}, _plan("S11", movable=True), factory)
    runtime.inject_plan_assets({}, _plan("S11", movable=False), factory)

    assert calls[0][2] == "default"
    assert roots[0].get("pos") == "0 0 3"
    assert roots[0].find("geom").get("contype") == "1"
    assert roots[0].find("geom").get("conaffinity") == "1"
    assert calls[1][2] is None
    assert roots[1].get("pos") == "0 0 -5"


def test_movable_articulated_distractor_keeps_only_its_free_joint() -> None:
    root = ET.fromstring(
        "<body><joint name='free' type='free'/>"
        "<body><joint name='drawer' type='slide'/><joint name='door' type='hinge'/>"
        "<geom group='0' type='box' size='0.02 0.02 0.02'/></body></body>"
    )

    class FakeObject:
        category_name = ""
        rotation = (0.0, 0.0)
        rotation_axis = "z"
        object_properties = {}
        joints = ["free", "drawer", "door"]

        def get_obj(self) -> ET.Element:
            return root

    plan = _plan("S11", movable=True)
    plan.params["weld_internal_asset_joints"] = True

    runtime.inject_plan_assets(
        {}, plan, lambda _path, *, name, joints: FakeObject()
    )

    assert [joint.get("type") for joint in root.findall(".//joint")] == ["free"]


def test_task_level_contact_margin_only_changes_collision_geoms() -> None:
    root = ET.fromstring(
        "<body><geom name='collision' group='0' contype='1' conaffinity='1'/>"
        "<geom name='visual' group='1' contype='0' conaffinity='0'/></body>"
    )

    class FakeObject:
        category_name = ""
        rotation = (0.0, 0.0)
        rotation_axis = "z"
        object_properties = {}
        joints = ["free"]

        def get_obj(self) -> ET.Element:
            return root

    plan = _plan("S10", movable=True)
    plan.params["asset_contact_margin_m"] = 0.006

    runtime.inject_plan_assets(
        {}, plan, lambda _path, *, name, joints: FakeObject()
    )

    assert root.find("geom[@name='collision']").get("margin") == "0.006"
    assert root.find("geom[@name='visual']").get("margin") is None


@pytest.mark.parametrize("enabled", [False, True])
def test_initial_asset_velocity_reset_preserves_scene_and_later_motion(enabled):
    plan = _plan("S10", movable=True)
    plan.params["zero_initial_asset_velocity"] = enabled
    engine = runtime.NonPhysicalPerturbationRuntime(plan)
    qvel = np.arange(12, dtype=float) + 1.0
    qpos = np.arange(14, dtype=float)
    before = qvel.copy()
    model = SimpleNamespace(
        joint_name2id=lambda name: 0, jnt_type=[0], jnt_dofadr=[6]
    )
    data = SimpleNamespace(qvel=qvel, qpos=qpos)
    env = SimpleNamespace(
        perturbation_asset_injection=SimpleNamespace(injected_names=("clutter",)),
        objects_dict={"clutter": SimpleNamespace(joints=["clutter_joint"])},
        sim=SimpleNamespace(model=model, data=data, forward=lambda: None),
    )
    engine.begin_rollout(env)
    np.testing.assert_array_equal(qvel[:6], before[:6])
    np.testing.assert_array_equal(qvel[6:], np.zeros(6) if enabled else before[6:])
    np.testing.assert_array_equal(qpos, np.arange(14, dtype=float))
    qvel[6:] = 0.5
    engine.transform_action(np.zeros(7), 1)
    np.testing.assert_array_equal(qvel[6:], np.full(6, 0.5))


def test_s10_box_collision_keeps_visual_mesh_mass_and_free_joint():
    root = ET.fromstring(
        '<body><joint type="free"/><geom group="0" type="mesh" mesh="collision" '
        'mass="0.028" friction="0.8 0.005 0.0001"/>'
        '<geom group="1" type="mesh" mesh="visual" contype="0" conaffinity="0"/></body>'
    )
    obj = SimpleNamespace(joints=["free"], get_obj=lambda: root)
    plan = _plan("S10", movable=True)
    plan.params.update(asset_collision_box_half_size=[0.03861756, 0.045803085, 0.02738214],
                       asset_collision_box_offset_xyz=[-0.00983288, -0.002414605, 0.00839394])
    visual = ET.tostring(root.find("geom[@group='1']"))
    runtime.inject_plan_assets({}, plan, lambda *args, **kwargs: obj)
    collision = root.find("geom[@group='0']")
    assert collision.get("type") == "box"
    assert collision.get("mesh") is None
    assert collision.get("mass") == "0.028"
    assert collision.get("friction") == "0.8 0.005 0.0001"
    assert ET.tostring(root.find("geom[@group='1']")) == visual
    assert root.find("joint").get("type") == "free"


@pytest.mark.parametrize("suite,case,movable", [
    ("libero_object", "S10", True), ("libero_goal", "S11", True),
    ("libero_goal", "S10", False),
])
@pytest.mark.parametrize("field,value", [
    ("zero_initial_asset_velocity", True),
    ("asset_collision_box_half_size", [0.03, 0.04, 0.02]),
])
def test_goal_s10_options_reject_other_suites_cases_and_fixed_assets(suite, case, movable, field, value):
    params = {"movable_asset": movable, field: value}
    config = dict(case_id=case, active_cases=[case], source_suite=suite,
                  perturbations=[[case, dict(operator="asset_or_appearance"),
                                  dict(variant="clutter"), dict(params=params)]])
    config["perturbations"].extend([other] for other in runtime.LEGACY_CASE_IDS if other != case)
    assets = SIMULATOR_ROOT / "libero/libero/assets/perturbation_assets"
    with pytest.raises(runtime.PerturbationConfigurationError, match="movable Goal S10"):
        runtime.build_execution_plan(config, assets)
