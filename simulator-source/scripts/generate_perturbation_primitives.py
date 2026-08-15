from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "libero"
    / "libero"
    / "assets"
    / "perturbation_assets"
    / "generated"
)


ASSETS = {
    "barrier_panel": {
        "description": "Movable path barrier or persistent occluder",
        "perturbations": ["S05", "S12", "D05"],
        "parameters": {"half_extents": [0.08, 0.008, 0.10]},
    },
    "occlusion_screen": {
        "description": "Camera-side screen for controlled partial occlusion",
        "perturbations": ["S12", "D04"],
        "parameters": {"half_extents": [0.06, 0.003, 0.08]},
    },
    "slotted_receiver": {
        "description": "Four-wall slot with tunable X/Y/insertion clearance",
        "perturbations": ["S07", "S09", "D03", "D19"],
        "parameters": {
            "inner_half_width": 0.036,
            "inner_half_depth": 0.045,
            "wall_thickness": 0.004,
            "wall_height": 0.055,
        },
    },
    "opening_frame": {
        "description": "Four-sided opening for approach and insertion clearance",
        "perturbations": ["S05", "S07", "S09", "D05"],
        "parameters": {
            "inner_half_width": 0.060,
            "inner_half_height": 0.060,
            "bar_half_thickness": 0.006,
            "depth_half_extent": 0.012,
        },
    },
    "support_riser": {
        "description": "Tunable receiver or support-surface height block",
        "perturbations": ["S03"],
        "parameters": {"half_extents": [0.10, 0.10, 0.025]},
    },
}


def header(model: str) -> list[str]:
    return [
        f'<mujoco model="{model}">',
        '  <compiler angle="radian"/>',
        "  <worldbody>",
        "    <body>",
        '      <body name="object">',
    ]


def footer(lower: tuple[float, float, float], upper: tuple[float, float, float]) -> list[str]:
    radius = max(
        (x * x + y * y) ** 0.5
        for x in (lower[0], upper[0])
        for y in (lower[1], upper[1])
    )
    return [
        "      </body>",
        f'      <site name="bottom_site" pos="0 0 {lower[2]}" size="0.005" rgba="0 0 0 0"/>',
        f'      <site name="top_site" pos="0 0 {upper[2]}" size="0.005" rgba="0 0 0 0"/>',
        f'      <site name="horizontal_radius_site" pos="{radius} 0 0" size="0.005" rgba="0 0 0 0"/>',
        "    </body>",
        "  </worldbody>",
        "</mujoco>",
    ]


def box_geom(name: str, pos: tuple[float, float, float], size: tuple[float, float, float]) -> str:
    return (
        f'        <geom name="{name}" type="box" group="0" '
        f'pos="{pos[0]} {pos[1]} {pos[2]}" '
        f'size="{size[0]} {size[1]} {size[2]}" '
        'density="300" friction="0.8 0.005 0.0001" rgba="0.32 0.42 0.52 1"/>'
    )


def single_box(name: str, half_extents: list[float]) -> str:
    lines = header(name)
    lines.append(box_geom(name, (0, 0, half_extents[2]), tuple(half_extents)))
    lines.extend(
        footer(
            (-half_extents[0], -half_extents[1], 0),
            (half_extents[0], half_extents[1], 2 * half_extents[2]),
        )
    )
    return "\n".join(lines) + "\n"


def slotted_receiver(parameters: dict) -> str:
    ix = parameters["inner_half_width"]
    iy = parameters["inner_half_depth"]
    t = parameters["wall_thickness"]
    h = parameters["wall_height"]
    lines = header("slotted_receiver")
    lines.append(box_geom("floor", (0, 0, t), (ix + t, iy + t, t)))
    lines.append(box_geom("left", (-(ix + t), 0, h), (t, iy + t, h)))
    lines.append(box_geom("right", (ix + t, 0, h), (t, iy + t, h)))
    lines.append(box_geom("front", (0, -(iy + t), h), (ix, t, h)))
    lines.append(box_geom("back", (0, iy + t, h), (ix, t, h)))
    lines.extend(footer((-(ix + 2 * t), -(iy + 2 * t), 0), (ix + 2 * t, iy + 2 * t, 2 * h)))
    return "\n".join(lines) + "\n"


def opening_frame(parameters: dict) -> str:
    iw = parameters["inner_half_width"]
    ih = parameters["inner_half_height"]
    t = parameters["bar_half_thickness"]
    d = parameters["depth_half_extent"]
    lines = header("opening_frame")
    lines.append(box_geom("left", (-(iw + t), 0, ih + t), (t, d, ih + t)))
    lines.append(box_geom("right", (iw + t, 0, ih + t), (t, d, ih + t)))
    lines.append(box_geom("bottom", (0, 0, t), (iw, d, t)))
    lines.append(box_geom("top", (0, 0, 2 * ih + t), (iw, d, t)))
    lines.extend(footer((-(iw + 2 * t), -d, 0), (iw + 2 * t, d, 2 * ih + 2 * t)))
    return "\n".join(lines) + "\n"


def render_asset(name: str, spec: dict) -> str:
    if name in {"barrier_panel", "occlusion_screen", "support_riser"}:
        return single_box(name, spec["parameters"]["half_extents"])
    if name == "slotted_receiver":
        return slotted_receiver(spec["parameters"])
    if name == "opening_frame":
        return opening_frame(spec["parameters"])
    raise KeyError(name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate parametric MuJoCo perturbation assets.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name, spec in ASSETS.items():
        asset_dir = output / name
        asset_dir.mkdir(parents=True, exist_ok=True)
        (asset_dir / f"{name}.xml").write_text(render_asset(name, spec), encoding="utf-8")
        (asset_dir / "metadata.json").write_text(
            json.dumps({"name": name, **spec}, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Generated {len(ASSETS)} parametric assets in {output}")


if __name__ == "__main__":
    main()
