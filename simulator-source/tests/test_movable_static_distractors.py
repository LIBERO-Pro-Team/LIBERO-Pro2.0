import sys
import xml.etree.ElementTree as ET
from pathlib import Path


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
