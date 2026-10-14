"""Generate the full 40-task LIBERO perturbation dataset.

The generator keeps the original LIBERO BDDL body intact and appends the
versioned perturbation contract.  Targets and references come from parsed
goal predicates, never from a four-task name substitution table.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = ROOT / "assets" / "bddl" / "00_original" / "bddl"
DEFAULT_OUTPUT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
DEFAULT_MANIFEST = ROOT / "assets" / "task_manifest.json"
ASSET_ROOT = ROOT / "simulator-source" / "libero" / "libero" / "assets" / "perturbation_assets"
PUBLISHED_MANIFEST_VERSION = "libero-pro2.0-1706-v1"

SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
# OpenPI examples/libero/main.py limits, excluding its 10 reset wait steps.
PI0_MAX_STEPS_BY_SUITE = {
    "libero_spatial": 220,
    "libero_object": 280,
    "libero_goal": 300,
    "libero_10": 520,
}
CASES = tuple(
    ["BASE"]
    + [f"S{i:02d}" for i in range(1, 23)]
    + [f"D{i:02d}" for i in range(1, 22)]
)
SCHEMA_CASES = tuple(
    [f"S{i:02d}" for i in range(1, 23)]
    + [f"D{i:02d}" for i in range(1, 22)]
)

SUITE_TASKS: Mapping[str, Tuple[str, ...]] = {
    "libero_spatial": (
        "pick_up_the_black_bowl_between_the_plate_and_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_from_table_center_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_cookie_box_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_ramekin_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_cookie_box_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_stove_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_next_to_the_plate_and_place_it_on_the_plate",
        "pick_up_the_black_bowl_on_the_wooden_cabinet_and_place_it_on_the_plate",
    ),
    "libero_object": (
        "pick_up_the_alphabet_soup_and_place_it_in_the_basket",
        "pick_up_the_cream_cheese_and_place_it_in_the_basket",
        "pick_up_the_salad_dressing_and_place_it_in_the_basket",
        "pick_up_the_bbq_sauce_and_place_it_in_the_basket",
        "pick_up_the_ketchup_and_place_it_in_the_basket",
        "pick_up_the_tomato_sauce_and_place_it_in_the_basket",
        "pick_up_the_butter_and_place_it_in_the_basket",
        "pick_up_the_milk_and_place_it_in_the_basket",
        "pick_up_the_chocolate_pudding_and_place_it_in_the_basket",
        "pick_up_the_orange_juice_and_place_it_in_the_basket",
    ),
    "libero_goal": (
        "open_the_middle_drawer_of_the_cabinet",
        "put_the_bowl_on_the_stove",
        "put_the_wine_bottle_on_top_of_the_cabinet",
        "open_the_top_drawer_and_put_the_bowl_inside",
        "put_the_bowl_on_top_of_the_cabinet",
        "push_the_plate_to_the_front_of_the_stove",
        "put_the_cream_cheese_in_the_bowl",
        "turn_on_the_stove",
        "put_the_bowl_on_the_plate",
        "put_the_wine_bottle_on_the_rack",
    ),
    "libero_10": (
        "LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket",
        "LIVING_ROOM_SCENE2_put_both_the_cream_cheese_box_and_the_butter_in_the_basket",
        "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it",
        "KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it",
        "LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate",
        "STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy",
        "LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate",
        "LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket",
        "KITCHEN_SCENE8_put_both_moka_pots_on_the_stove",
        "KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it",
    ),
}


def scan_tokens(text: str) -> List[Any]:
    tokens = re.findall(r"\(|\)|[^\s()]+", re.sub(r";[^\n]*", "", text))

    def parse(index: int) -> Tuple[Any, int]:
        token = tokens[index]
        if token != "(":
            return token, index + 1
        values: List[Any] = []
        index += 1
        while index < len(tokens) and tokens[index] != ")":
            value, index = parse(index)
            values.append(value)
        if index >= len(tokens):
            raise ValueError("Unclosed BDDL list")
        return values, index + 1

    result, next_index = parse(0)
    if next_index != len(tokens) or not isinstance(result, list):
        raise ValueError("Invalid BDDL expression")
    return result


def group_map(tree: Sequence[Any]) -> Dict[str, List[Any]]:
    return {
        str(group[0]): list(group[1:])
        for group in tree[2:]
        if isinstance(group, list) and group and isinstance(group[0], str)
    }


def declarations(values: Sequence[Any]) -> List[Tuple[str, str]]:
    """Parse PDDL/BDDL declarations where several names share one type."""

    result: List[Tuple[str, str]] = []
    index = 0
    while index < len(values):
        names: List[str] = []
        while index < len(values) and values[index] != "-":
            names.append(str(values[index]))
            index += 1
        if index >= len(values):
            raise ValueError("declaration missing '-'")
        index += 1
        if index >= len(values):
            raise ValueError("declaration missing type")
        object_type = str(values[index])
        index += 1
        result.extend((name, object_type) for name in names)
    return result


def nested_field(group: Sequence[Any], name: str) -> Any:
    for value in group:
        if isinstance(value, list) and value and value[0] == name:
            return value[1:]
    return None


def flatten_goal(values: Sequence[Any]) -> List[List[Any]]:
    if len(values) == 1 and isinstance(values[0], list):
        root = values[0]
        if root and str(root[0]).lower() == "and":
            return [list(item) for item in root[1:] if isinstance(item, list)]
        return [list(root)]
    return [list(item) for item in values if isinstance(item, list)]


def resolve_entity(value: str, entities: Iterable[str]) -> str:
    candidates = [entity for entity in entities if value == entity or value.startswith(entity + "_")]
    return max(candidates, key=len) if candidates else value


def asset_for_type(object_type: str) -> Tuple[str, float]:
    value = object_type.lower()
    if any(token in value for token in ("mug", "glass")):
        return "prl/plastic_glass", 0.70
    if "bowl" in value:
        return "github/object_sim_bowl", 0.70
    if "plate" in value:
        return "prl/plastic_plate", 0.55
    if "bottle" in value:
        return "prl/fuze_bottle", 0.72
    if any(token in value for token in ("book", "notebook")):
        return "prl/notebook", 0.70
    if any(token in value for token in ("can", "soup", "sauce")):
        return "ycb/YcbTomatoSoupCan", 0.72
    if any(token in value for token in ("pot", "pan", "fry")):
        return "prl/gelatin_box", 0.70
    return "prl/cracker_box", 0.70


@dataclass(frozen=True)
class TaskProfile:
    suite: str
    task_id: int
    task_name: str
    language: str
    objects: Tuple[Tuple[str, str], ...]
    fixtures: Tuple[Tuple[str, str], ...]
    goal: Tuple[Tuple[Any, ...], ...]
    initial_regions: Mapping[str, str]
    interaction_mode: str
    primary: str
    primary_object: str
    receiver: str
    secondary: str
    support: str
    s06_asset: str
    s06_scale: float
    s11_asset: str
    s11_scale: float

    @property
    def entities(self) -> Tuple[str, ...]:
        return tuple(name for name, _ in self.objects + self.fixtures)


def load_profile(suite: str, task_id: int, task_name: str) -> TaskProfile:
    path = ORIGINAL_ROOT / suite / f"{task_name}.bddl"
    tree = scan_tokens(path.read_text(encoding="utf-8"))
    groups = group_map(tree)
    objects = tuple(declarations(groups.get(":objects", [])))
    fixtures = tuple(declarations(groups.get(":fixtures", [])))
    entities = tuple(name for name, _ in objects + fixtures)
    goal = tuple(tuple(item) for item in flatten_goal(groups.get(":goal", [])))
    articulation = {"open", "close", "turnon", "turnoff"}
    interaction_mode = "articulation" if any(
        item and str(item[0]).lower() in articulation for item in goal
    ) and not any(item and str(item[0]).lower() in {"on", "in"} for item in goal) else "placement"

    initial_regions: Dict[str, str] = {}
    for item in groups.get(":init", []):
        if isinstance(item, list) and len(item) >= 3 and str(item[0]).lower() == "on":
            initial_regions[str(item[1])] = str(item[2])

    goal_objects = [
        str(item[1]) for item in goal
        if len(item) >= 2 and str(item[0]).lower() in {"on", "in"}
        and str(item[1]) in dict(objects)
    ]
    interaction_entities: List[str] = []
    receivers: List[str] = []
    for item in goal:
        if len(item) < 2:
            continue
        first = resolve_entity(str(item[1]), entities)
        if first not in interaction_entities:
            interaction_entities.append(first)
        if len(item) >= 3:
            second = resolve_entity(str(item[2]), entities)
            if second not in receivers:
                receivers.append(second)

    object_names = [name for name, _ in objects]
    primary_object = goal_objects[0] if goal_objects else (object_names[0] if object_names else "")
    primary = interaction_entities[0] if interaction_mode == "articulation" and interaction_entities else primary_object
    receiver = receivers[0] if receivers else (primary if primary else (fixtures[0][0] if fixtures else ""))
    excluded = set(goal_objects) | {receiver, primary}
    distractors = [name for name in object_names if name not in excluded]
    secondary = distractors[0] if distractors else next(
        (name for name in object_names if name != primary), primary_object
    )

    support = resolve_entity(initial_regions.get(primary_object, ""), entities)
    if support not in entities:
        support = next((name for name, _ in fixtures if name not in {primary, receiver}), receiver)
    if not support:
        support = receiver

    type_by_name = dict(objects)
    s06_target = primary_object if primary_object in type_by_name else secondary
    s06_asset, s06_scale = asset_for_type(type_by_name.get(s06_target, "object"))
    s11_target = primary_object if primary_object in type_by_name else secondary
    s11_asset, s11_scale = asset_for_type(type_by_name.get(s11_target, "object"))

    language_values = groups.get(":language", [])
    language = " ".join(str(value) for value in language_values).strip()
    return TaskProfile(
        suite=suite,
        task_id=task_id,
        task_name=task_name,
        language=language,
        objects=objects,
        fixtures=fixtures,
        goal=goal,
        initial_regions=initial_regions,
        interaction_mode=interaction_mode,
        primary=primary,
        primary_object=primary_object,
        receiver=receiver,
        secondary=secondary,
        support=support,
        s06_asset=s06_asset,
        s06_scale=s06_scale,
        s11_asset=s11_asset,
        s11_scale=s11_scale,
    )


def atom_list(values: Sequence[str]) -> str:
    return " ".join(str(value) for value in values)


def params_block(values: Mapping[str, Any]) -> str:
    if not values:
        return ""
    lines = ["        (:params"]
    for key, value in values.items():
        if isinstance(value, (tuple, list)):
            rendered = " ".join(str(item) for item in value)
        else:
            rendered = str(value)
        lines.append(f"          (:{key} {rendered})")
    lines.append("        )")
    return "\n".join(lines) + "\n"


def _final_review_rules() -> Any:
    try:
        from scripts import apply_goal_review_finalization
    except ImportError:  # Direct execution from the scripts directory.
        import apply_goal_review_finalization

    return apply_goal_review_finalization


def _merge_case_fields(
    fields: List[Tuple[str, str]], updates: Mapping[str, Sequence[str]]
) -> List[Tuple[str, str]]:
    values = dict(fields)
    for key, atoms in updates.items():
        values[key] = atom_list(atoms)
    return [(key, values[key]) for key in values]


def case_entry(case_id: str, profile: TaskProfile, active_case: str) -> str:
    mode = profile.interaction_mode
    placement = mode == "placement"
    primary = profile.primary
    receiver = profile.receiver
    secondary = profile.secondary
    if case_id == "S01":
        targets = [primary]
        fields = [("operator", "pose_transform"), ("targets", atom_list(targets)), ("variant", "xy_yaw")]
    elif case_id == "S02":
        fields = [("operator", "pose_transform"), ("targets", receiver), ("variant", "xy_yaw")]
    elif case_id == "S03":
        fields = [("operator", "geometry_variant"), ("targets", f"{receiver} {profile.support}"), ("variant", "receiver_or_support_height")]
    elif case_id == "S04":
        first = profile.primary_object if profile.primary_object else secondary
        fields = [("operator", "pose_transform"), ("targets", f"{first} {secondary}"), ("variant", "planar_object_position_swap"), ("constraints", "same_support_surface collision_free task_completable")]
    elif case_id == "S05":
        targets = f"{primary} {receiver}" if placement else f"{secondary} {primary}"
        fields = [("operator", "geometry_variant"), ("targets", targets), ("references", secondary), ("variant", "restricted_approach_or_path"), ("constraints", "initial_collision_free ik_reachable full_path_exists")]
    elif case_id == "S06":
        fields = [("operator", "asset_or_appearance"), ("targets", profile.primary_object if profile.primary_object else secondary), ("variant", "same_class_or_unseen_instance")]
    elif case_id == "S07":
        geometry_target = receiver if placement and receiver != "main_table" else primary
        fields = [("operator", "geometry_variant"), ("targets", geometry_target), ("parts", "opening rim contain_region"), ("variant", "functional_part_geometry")]
    elif case_id == "S08":
        fields = [("operator", "geometry_variant"), ("targets", profile.primary_object if profile.primary_object else primary), ("variant", "scale_or_aspect_ratio")]
    elif case_id == "S09":
        geometry_receiver = receiver if receiver != "main_table" else primary
        targets = f"{profile.primary_object} {geometry_receiver}" if placement else f"{secondary} {primary}"
        fields = [("operator", "geometry_variant"), ("targets", targets), ("variant", "container_opening_clearance_and_pose_coupling"), ("constraints", "real_collision_geometry full_containment positive_clearance insertion_depth")]
    elif case_id == "S10":
        fields = [("operator", "asset_or_appearance"), ("targets", profile.primary_object if profile.primary_object else secondary), ("references", secondary), ("variant", "irrelevant_object_clutter")]
    elif case_id == "S11":
        fields = [("operator", "asset_or_appearance"), ("targets", profile.primary_object if profile.primary_object else secondary), ("references", secondary), ("variant", "same_class_or_visually_similar_distractor")]
    elif case_id == "S12":
        fields = [("operator", "occlusion_or_obstacle"), ("targets", f"{primary} {receiver}" if placement else primary), ("references", f"{secondary} agentview"), ("variant", "persistent_front_occlusion")]
    elif case_id == "S13":
        fields = [("operator", "asset_or_appearance"), ("targets", f"{primary} {receiver}" if placement else primary), ("variant", "color_texture_reflection_or_surface_state")]
    elif case_id == "S14":
        fields = [("operator", "asset_or_appearance"), ("targets", f"{profile.support} {primary}"), ("variant", "foreground_background_contrast_or_scene_domain")]
    elif case_id == "S15":
        fields = [("operator", "camera_transform"), ("targets", "agentview robot0_eye_in_hand"), ("variant", "fixed_extrinsics_or_cross_camera_calibration")]
    elif case_id == "S16":
        fields = [("operator", "camera_transform"), ("targets", "agentview robot0_eye_in_hand"), ("variant", "intrinsics_fov_resolution_crop_or_distortion")]
    elif case_id == "S17":
        fields = [("operator", "state_or_language_event"), ("targets", "robot0"), ("variant", "initial_joints_eef_orientation_or_gripper_opening")]
    elif case_id == "S18":
        fields = [("operator", "state_or_language_event"), ("targets", "robot0"), ("variant", "base_tcp_joint_zero_or_grasp_center_calibration")]
    elif case_id == "S19":
        fields = [("operator", "observation_fault"), ("targets", "rgb depth"), ("variant", "compression_noise_blur_exposure_contamination_or_depth_holes")]
    elif case_id == "S20":
        fields = [("operator", "timing_or_action_fault"), ("targets", "observation inference control action"), ("variant", "fixed_rate_delay_or_action_window")]
    elif case_id == "S21":
        fields = [("operator", "state_or_language_event"), ("targets", "task_instruction"), ("variant", "semantic_paraphrase")]
    elif case_id == "S22":
        fields = [
            ("operator", "asset_or_appearance"),
            ("targets", "workspace_surface"),
            ("variant", "support_surface_texture_replacement"),
            (
                "constraints",
                "collision_geometry_unchanged friction_unchanged object_poses_unchanged",
            ),
        ]
    elif case_id == "D01":
        fields = [("operator", "pose_transform"), ("targets", primary), ("trigger", "approach_or_pregrasp"), ("variant", "xy_yaw_update")]
    elif case_id == "D02":
        fields = [("operator", "pose_transform"), ("targets", receiver if placement else primary), ("trigger", "postgrasp_or_preplace"), ("variant", "xy_yaw_update")]
    elif case_id == "D03":
        fields = [("operator", "occlusion_or_obstacle"), ("targets", receiver if placement else primary), ("references", secondary), ("trigger", "preplace"), ("variant", "occupy_or_release_receiver")]
    elif case_id == "D04":
        fields = [("operator", "occlusion_or_obstacle"), ("targets", f"{primary} {receiver}" if placement else primary), ("references", secondary), ("trigger", "task_phase"), ("variant", "enter_hold_exit_occlusion")]
    elif case_id == "D05":
        fields = [("operator", "occlusion_or_obstacle"), ("targets", "robot_future_path"), ("references", secondary), ("trigger", "transport"), ("variant", "obstacle_enters_path"), ("constraints", "alternate_collision_free_path_exists")]
    elif case_id == "D06":
        fields = [("operator", "pose_transform"), ("targets", f"{secondary} {profile.primary_object}"), ("trigger", "task_phase"), ("variant", "distractor_move_or_local_rearrangement")]
    elif case_id == "D07":
        fields = [("operator", "camera_transform"), ("targets", "agentview robot0_eye_in_hand"), ("trigger", "task_phase"), ("variant", "shake_drift_or_persistent_offset")]
    elif case_id == "D08":
        fields = [("operator", "observation_fault"), ("targets", "agentview robot0_eye_in_hand"), ("trigger", "task_phase"), ("variant", "camera_dropout_then_restore")]
    elif case_id == "D09":
        fields = [("operator", "observation_fault"), ("targets", "rgb"), ("trigger", "task_phase"), ("variant", "light_shadow_or_exposure_change")]
    elif case_id == "D10":
        fields = [("operator", "observation_fault"), ("targets", "rgb depth"), ("trigger", "task_phase"), ("variant", "drop_repeat_or_freeze_frames")]
    elif case_id == "D11":
        fields = [("operator", "observation_fault"), ("targets", "agentview robot0_eye_in_hand depth proprioception"), ("trigger", "task_phase"), ("variant", "timestamp_offset_or_state_freeze")]
    elif case_id == "D12":
        fields = [("operator", "timing_or_action_fault"), ("targets", "observation inference"), ("trigger", "task_phase"), ("variant", "transient_latency_spike")]
    elif case_id == "D13":
        fields = [("operator", "timing_or_action_fault"), ("targets", "arm gripper"), ("trigger", "task_phase"), ("variant", "delay_jitter_or_desynchronization")]
    elif case_id == "D14":
        fields = [("operator", "timing_or_action_fault"), ("targets", "action"), ("trigger", "task_phase"), ("variant", "command_drop_or_repeat")]
    elif case_id == "D15":
        fields = [("operator", "timing_or_action_fault"), ("targets", "action_chunk replan"), ("trigger", "state_change"), ("variant", "stale_chunk_late_chunk_or_replan_interrupt")]
    elif case_id == "D16":
        fields = [("operator", "state_or_language_event"), ("targets", "robot0"), ("trigger", "task_phase"), ("variant", "bounded_action_takeover_or_reachable_state_offset"), ("constraints", "no_physical_contact")]
    elif case_id == "D17":
        fields = [("operator", "state_or_language_event"), ("targets", f"{primary} gripper"), ("trigger", "grasp_attempt"), ("variant", "grasp_failure_result"), ("constraints", "retry_remains_possible")]
    elif case_id == "D18":
        fields = [("operator", "state_or_language_event"), ("targets", primary), ("trigger", "transport"), ("variant", "reachable_collision_free_drop_state"), ("constraints", "recovery_remains_possible")]
    elif case_id == "D19":
        fields = [("operator", "state_or_language_event"), ("targets", f"{primary} {receiver}" if placement else primary), ("trigger", "place_attempt"), ("variant", "misplace_partial_insert_or_wrong_receiver_result"), ("constraints", "correction_remains_possible")]
    elif case_id == "D20":
        fields = [
            ("operator", "pose_transform"),
            ("targets", "robot0"),
            ("trigger", "robot_in_motion"),
            ("variant", "collision_induced_reachable_joint_displacement"),
            (
                "constraints",
                "single_trigger joint_limits collision_free no_self_collision workspace_clearance",
            ),
        ]
    elif case_id == "D21":
        fields = [("operator", "state_or_language_event"), ("targets", "task_instruction"), ("trigger", "task_phase"), ("variant", "equivalent_restatement_or_clarification"), ("constraints", "semantic_goal_unchanged")]
    else:
        raise ValueError(case_id)

    params: Dict[str, Any] = {"interaction_mode": profile.interaction_mode}
    if case_id == "S06":
        params.update({"asset_id": profile.s06_asset, "asset_scale": profile.s06_scale})
    elif case_id == "S04" and profile.suite == "libero_10" and profile.task_id == 2:
        params.update(
            {
                "grounded_swap": True,
                "ground_support_from_declared_surface": True,
                "swap_cluster_radius_m": 0.18,
                "support_surface": "kitchen_table",
            }
        )
    elif case_id == "S11":
        params.update({"asset_id": profile.s11_asset, "asset_scale": profile.s11_scale})
    elif case_id == "D02":
        params["offset_xy"] = (-0.12, 0.09) if receiver.startswith("basket_") else (-0.06, 0.045)
    elif case_id == "D15":
        params.update({"chunk_size": 4, "stale_chunk_steps": 4})
    elif case_id == "D14":
        params.update({"repeat_count": 8, "event_duration_steps": 8})
    elif case_id == "D16" and active_case == "D16":
        params["event_duration_steps"] = 6
    elif case_id == "D17" and active_case == "D17":
        params.update({"event_duration_steps": 40, "recovery_retreat_m": 0.07})
    elif case_id in {"D18", "D19"} and profile.interaction_mode == "articulation":
        params["trigger_state_change_m"] = 0.02
    elif case_id == "S21":
        params.update({"source": profile.language.replace(" ", "_"), "value": "please_" + profile.language.replace(" ", "_")})
    elif case_id == "S22":
        params.update(
            {
                "material_id": "s22_table_texture",
                "texture_asset": "textures/table_light_wood.png",
                "texture_scale": (2.0, 2.0),
            }
        )
    elif case_id == "D20":
        params.update(
            {
                "trigger_eef_motion_m": 0.025,
                "trigger_action_norm": 0.05,
                "joint_delta_rad": 0.10,
                "min_eef_displacement_m": 0.035,
                "min_workspace_clearance_m": 0.035,
                "penetration_tolerance_m": 0.001,
            }
        )
    elif case_id == "D21":
        params["interaction_mode"] = profile.interaction_mode
    if (
        case_id == active_case
        and case_id in {"S06", "S11"}
        and profile.suite == "libero_10"
        and profile.task_id == 8
    ):
        params.update({"asset_id": "libero/yellow_moka_pot", "asset_scale": 1.0})
    if case_id == active_case:
        final_params, final_fields = _final_review_rules().case_updates(
            profile.suite, profile.task_id, case_id
        )
        fields = _merge_case_fields(fields, final_fields)
        params.update(final_params)
        if (
            profile.suite == "libero_goal"
            and case_id == "S06"
            and profile.task_id in {0, 7}
        ):
            for key in (
                "asset_id",
                "asset_scale",
                "asset_quat",
                "geometry_factors",
                "grounded_replacement",
                "sampler_compatible",
                "support_surface",
            ):
                params.pop(key, None)
    lines = [f"      ({case_id}"]
    for key, value in fields:
        lines.append(f"        (:{key} {value})")
    rendered_params = params_block(params)
    if rendered_params:
        lines.append(rendered_params.rstrip("\n"))
    lines.append("      )")
    return "\n".join(lines)


def perturbation_config(profile: TaskProfile, active_case: str) -> str:
    kind = "base" if active_case == "BASE" else "static" if active_case.startswith("S") else "dynamic"
    lines = [
        "  (:perturbation_config",
        "    (:schema_version 5)",
        "    (:profile nonphysical_shared_operator_schema)",
        f"    (:source_suite {profile.suite})",
        f"    (:source_task {profile.task_name})",
        "    (:configuration_mode shared_operator_instances)",
        f"    (:active_cases {'none' if active_case == 'BASE' else active_case})",
        f"    (:case_id {active_case})",
        f"    (:case_kind {kind})",
        "    (:excluded_domains mass friction force stiffness damping collision_impulse)",
        "    (:schema_status base_capability_catalog)",
        "",
        "    (:case_defaults",
        "      (:enable_rule listed_in_active_cases)",
        "      (:unlisted_cases disabled)",
        "      (:schedule_rule S_static_D_dynamic)",
        "      (:base_constraints goal_unchanged collision_free task_completable)",
        "      (:runtime_rule selected_operator_and_schedule)",
        "    )",
        "",
        "    (:schedule_catalog",
        "      (static (:start reset) (:duration episode) (:restore false))",
        "      (dynamic (:start event_trigger) (:duration case_defined) (:restore case_defined))",
        "    )",
        "",
        "    (:perturbations",
    ]
    for case_id in SCHEMA_CASES:
        lines.append(case_entry(case_id, profile, active_case))
    lines.extend(["    )", "  )"])
    return "\n".join(lines)


def append_config(source: str, profile: TaskProfile, active_case: str) -> str:
    if ":perturbation_config" in source:
        raise ValueError(f"Source already has perturbation_config: {profile.task_name}")
    source = _final_review_rules().apply_published_structural_overrides(
        source, profile.suite, profile.task_id, active_case
    )
    source = source.rstrip()
    if not source.endswith(")"):
        raise ValueError(f"Source BDDL is not closed: {profile.task_name}")
    # Keep one complete `(define ...)` expression by inserting the contract
    # before the source problem's final closing parenthesis.
    return source[:-1].rstrip() + "\n\n" + perturbation_config(profile, active_case) + "\n)\n"


def canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def build(
    output: Path,
    manifest_path: Path,
    *,
    replace_new_cases: bool = False,
) -> Dict[str, Any]:
    if output.exists() and not output.is_dir():
        raise FileExistsError(f"Dataset path is not a directory: {output}")
    profiles = [
        load_profile(suite, task_id, task_name)
        for suite in SUITES
        for task_id, task_name in enumerate(SUITE_TASKS[suite])
    ]
    for asset_id in {profile.s06_asset for profile in profiles} | {profile.s11_asset for profile in profiles}:
        catalog_path = ASSET_ROOT / "asset_catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if not any(item.get("id") == asset_id for item in catalog.get("assets", [])):
            raise ValueError(f"Replacement asset is not in catalog: {asset_id}")

    tasks: List[Dict[str, Any]] = []
    for profile in profiles:
        source_path = ORIGINAL_ROOT / profile.suite / f"{profile.task_name}.bddl"
        source = source_path.read_text(encoding="utf-8")
        for case_id in CASES:
            folder = "00_base" if case_id == "BASE" else "01_static" if case_id.startswith("S") else "02_dynamic"
            target = output / profile.suite / folder / f"{case_id}__{profile.task_name}.bddl"
            if _final_review_rules().is_excluded(
                profile.suite, profile.task_id, case_id
            ):
                if target.is_file():
                    target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            is_new_case = case_id in {"S22", "D20"}
            if not target.exists() or (is_new_case and replace_new_cases):
                target.write_text(
                    append_config(source, profile, case_id), encoding="utf-8"
                )
            tasks.append(
                {
                    "suite": profile.suite,
                    "base_task_id": profile.task_id,
                    "case_id": case_id,
                    "case_kind": "base" if case_id == "BASE" else "static" if case_id.startswith("S") else "dynamic",
                    "bddl_path": (Path("bddl") / output.name / profile.suite / folder / target.name).as_posix(),
                    "bddl_sha256": canonical_hash(target),
                    "task_version": PUBLISHED_MANIFEST_VERSION,
                    "max_steps": PI0_MAX_STEPS_BY_SUITE[profile.suite],
                    "reset_stabilization_steps": 10,
                    "observation_schema_version": "libero_standard_v1",
                    "action_schema_version": "libero_action_v1",
                }
            )
    tasks.sort(key=lambda item: (item["suite"], int(item["base_task_id"]), item["case_id"]))
    manifest = {
        "manifest_version": PUBLISHED_MANIFEST_VERSION,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return {"dataset": str(output), "manifest": str(manifest_path), "task_count": len(tasks)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--replace-new-cases",
        action="store_true",
        help="Regenerate only S22 and D20 if those extension files already exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            build(
                args.output.resolve(),
                args.manifest.resolve(),
                replace_new_cases=args.replace_new_cases,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
