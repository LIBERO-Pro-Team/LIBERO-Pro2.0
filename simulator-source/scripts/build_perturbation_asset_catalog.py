from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = (
    REPO_ROOT / "libero" / "libero" / "assets" / "perturbation_assets"
)


EVERYDAY_OBJECTS = (
    "prl/can",
    "prl/cracker_box",
    "prl/fuze_bottle",
    "prl/gelatin_box",
    "prl/herring_tin",
    "prl/lunchbox",
    "prl/notebook",
    "github/object_sim_bowl",
    "prl/plastic_glass",
    "prl/plastic_plate",
    "prl/pocky_box",
    "prl/pop_tarts_case",
    "prl/recycle_bin",
    "prl/spam_can",
    "prl/sugar_box",
    "prl/wicker_tray",
    "prl/yellow_tote",
    "ycb/YcbBanana",
    "ycb/YcbChipsCan",
    "ycb/YcbCrackerBox",
    "ycb/YcbFoamBrick",
    "ycb/YcbGelatinBox",
    "ycb/YcbHammer",
    "ycb/YcbMasterChefCan",
    "ycb/YcbMediumClamp",
    "ycb/YcbMustardBottle",
    "ycb/YcbPear",
    "ycb/YcbPottedMeatCan",
    "ycb/YcbPowerDrill",
    "ycb/YcbScissors",
    "ycb/YcbStrawberry",
    "ycb/YcbTennisBall",
    "ycb/YcbTomatoSoupCan",
)

SEMANTIC_PAIRS = (
    "libero/yellow_moka_pot",
    "prl/cracker_box",
    "ycb/YcbCrackerBox",
    "prl/gelatin_box",
    "ycb/YcbGelatinBox",
    "prl/can",
    "ycb/YcbMasterChefCan",
    "ycb/YcbTomatoSoupCan",
)

TEXTURED_OBJECTS = (
    "prl/cracker_box",
    "prl/fuze_bottle",
    "prl/gelatin_box",
    "prl/pocky_box",
    "prl/pop_tarts_case",
    "prl/spam_can",
    "prl/sugar_box",
    "ycb/YcbBanana",
    "ycb/YcbChipsCan",
    "ycb/YcbCrackerBox",
    "ycb/YcbGelatinBox",
    "ycb/YcbMasterChefCan",
    "ycb/YcbMustardBottle",
    "ycb/YcbPottedMeatCan",
    "ycb/YcbPowerDrill",
    "ycb/YcbTomatoSoupCan",
)

HANDLES = (
    "robocasa/bar_handle",
    "robocasa/boxed_handle",
    "robocasa/knob_handle",
)


def coverage(
    perturbation_id: str,
    mechanism: str,
    *,
    asset_ids: tuple[str, ...] = (),
    local_resources: tuple[str, ...] = (),
    note: str,
) -> dict:
    return {
        "id": perturbation_id,
        "mechanism": mechanism,
        "asset_ids": list(asset_ids),
        "local_resources": list(local_resources),
        "note": note,
    }


COVERAGE = (
    coverage("S01", "runtime_state", note="Sample target x, y, and yaw; no new mesh is required."),
    coverage("S02", "runtime_state", note="Sample receiver x, y, and yaw; reuse the task receiver."),
    coverage(
        "S03",
        "parametric_asset",
        asset_ids=("generated/support_riser",),
        note="Vary support or receiver height with collision geometry enabled.",
    ),
    coverage("S04", "runtime_state", note="Change target-receiver relative layout with existing task bodies."),
    coverage(
        "S05",
        "parametric_asset",
        asset_ids=("generated/barrier_panel", "generated/opening_frame"),
        note="Constrain approach corridors while retaining a validated collision-free solution.",
    ),
    coverage(
        "S06",
        "external_asset",
        asset_ids=("libero/yellow_moka_pot",) + EVERYDAY_OBJECTS,
        note="Use category-compatible LIBERO, PRL, and YCB instances after graspability screening.",
    ),
    coverage(
        "S07",
        "external_and_parametric_assets",
        asset_ids=HANDLES + ("generated/opening_frame",),
        note="Swap handle families or vary the true collision opening geometry.",
    ),
    coverage(
        "S08",
        "external_asset",
        asset_ids=EVERYDAY_OBJECTS,
        note="Use recorded dimensions for discrete scale/aspect variants; continuous variants scale both visual and collision geometry.",
    ),
    coverage(
        "S09",
        "parametric_asset",
        asset_ids=("generated/slotted_receiver", "generated/opening_frame"),
        note="Control actual X/Y/insertion clearance, not only the invisible goal site.",
    ),
    coverage(
        "S10",
        "external_asset",
        asset_ids=EVERYDAY_OBJECTS,
        note="Populate clutter from dimensioned objects and reject initial collisions.",
    ),
    coverage(
        "S11",
        "external_asset",
        asset_ids=("libero/yellow_cabinet",) + SEMANTIC_PAIRS,
        note=(
            "Use same-category and highly similar LIBERO, PRL, and YCB candidates "
            "for grounding distractors."
        ),
    ),
    coverage(
        "S12",
        "parametric_asset",
        asset_ids=("generated/occlusion_screen", "generated/barrier_panel"),
        note="Place persistent occluders by measured image-space coverage.",
    ),
    coverage(
        "S13",
        "external_and_existing_assets",
        asset_ids=TEXTURED_OBJECTS,
        local_resources=("libero/libero/assets/textures",),
        note="Use textured objects plus material parameter variants without changing collision geometry.",
    ),
    coverage(
        "S14",
        "existing_asset",
        local_resources=("libero/libero/assets/textures", "libero/libero/assets/scenes"),
        note="LIBERO already contains table, floor, wall, and scene-style texture variants.",
    ),
    coverage("S15", "runtime_configuration", note="Change camera extrinsics and calibration; no mesh asset is required."),
    coverage("S16", "observation_wrapper", note="Change FOV, resolution, crop, or lens distortion in the observation path."),
    coverage("S17", "runtime_state", note="Sample a collision-free robot initial configuration."),
    coverage("S18", "runtime_configuration", note="Inject base, TCP, joint-zero, or gripper-center calibration offsets."),
    coverage("S19", "observation_wrapper", note="Apply deterministic RGB/depth degradation; no 3D asset is required."),
    coverage("S20", "runtime_configuration", note="Configure fixed frequencies, delays, and action windows."),
    coverage("S21", "language_manifest", note="Use audited, goal-equivalent instruction candidates rather than a 3D asset."),
    coverage("D01", "runtime_state", note="Move the existing target before contact and forward simulation afterward."),
    coverage("D02", "runtime_state", note="Move the existing loose receiver at a scheduled task phase."),
    coverage(
        "D03",
        "external_or_parametric_asset",
        asset_ids=("generated/slotted_receiver",) + EVERYDAY_OBJECTS,
        note="Occupy the receiving region with a collision-enabled object while retaining recovery options.",
    ),
    coverage(
        "D04",
        "parametric_asset",
        asset_ids=("generated/occlusion_screen",),
        note="Move a screen into and out of the relevant camera frustum on a fixed schedule.",
    ),
    coverage(
        "D05",
        "parametric_asset",
        asset_ids=("generated/barrier_panel", "generated/opening_frame"),
        note="Insert collision geometry into the nominal path while preserving a validated detour.",
    ),
    coverage(
        "D06",
        "external_asset",
        asset_ids=("libero/red_coffee_mug",) + EVERYDAY_OBJECTS,
        note="Move non-task objects from the common clutter pool without teleport overlap.",
    ),
    coverage("D07", "runtime_configuration", note="Schedule camera shake, drift, or a permanent pose jump."),
    coverage("D08", "observation_wrapper", note="Drop and restore one camera stream; no 3D asset is required."),
    coverage("D09", "runtime_configuration", note="Change MuJoCo lights and exposure during rollout."),
    coverage("D10", "observation_wrapper", note="Drop, repeat, or freeze deterministic image frame indices."),
    coverage("D11", "observation_wrapper", note="Offset modality timestamps or freeze state observations."),
    coverage("D12", "runtime_configuration", note="Inject inference or observation latency peaks."),
    coverage("D13", "runtime_configuration", note="Inject control delay, timing jitter, or gripper desynchronization."),
    coverage("D14", "action_wrapper", note="Drop or duplicate predetermined action command indices."),
    coverage("D15", "action_wrapper", note="Invalidate stale action chunks or interrupt replanning queues."),
    coverage("D16", "runtime_state", note="Apply a bounded takeover trajectory or reachable state displacement."),
    coverage("D17", "runtime_state", note="Inject a recoverable failed-grasp result state."),
    coverage("D18", "runtime_state", note="Place the carried object at a prevalidated reachable drop state."),
    coverage("D19", "runtime_state", note="Inject a recoverable misplacement or incomplete insertion state."),
    coverage("D21", "language_manifest", note="Update an equivalent instruction only when the policy exposes a runtime language API."),
)


def generated_assets(root: Path) -> list[dict]:
    records = []
    for metadata_path in sorted((root / "generated").glob("*/metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        name = metadata["name"]
        xml_path = metadata_path.with_name(f"{name}.xml")
        records.append(
            {
                "id": f"generated/{name}",
                "format": "mjcf",
                "path": xml_path.relative_to(root).as_posix(),
                "source_asset": "scripts/generate_perturbation_primitives.py",
                "license": "MIT",
                "parameters": metadata["parameters"],
                "perturbations": metadata["perturbations"],
                "readiness": "ready_mjcf",
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the unified perturbation asset and coverage catalog."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    vendor_manifest = json.loads(
        (root / "vendor_manifest.json").read_text(encoding="utf-8")
    )
    adapted_catalog = json.loads(
        (root / "adapted_catalog.json").read_text(encoding="utf-8")
    )
    assets = adapted_catalog["assets"] + generated_assets(root)
    catalog = {
        "format_version": 1,
        "summary": {
            "ready_mjcf_assets": len(assets),
            "external_adapted_assets": len(adapted_catalog["assets"]),
            "generated_parametric_assets": len(assets) - len(adapted_catalog["assets"]),
            "perturbation_directions_covered": len(COVERAGE),
        },
        "sources": vendor_manifest["sources"],
        "asset_sets": {
            "everyday_objects": list(EVERYDAY_OBJECTS),
            "semantic_distractor_pairs": list(SEMANTIC_PAIRS),
            "textured_objects": list(TEXTURED_OBJECTS),
            "affordance_handles": list(HANDLES),
        },
        "assets": assets,
        "perturbation_coverage": list(COVERAGE),
    }
    destination = root / "asset_catalog.json"
    with destination.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(catalog, indent=2) + "\n")
    print(
        f"Cataloged {len(assets)} ready assets and {len(COVERAGE)} perturbations in {destination}"
    )


if __name__ == "__main__":
    main()
