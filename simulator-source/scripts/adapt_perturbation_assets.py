from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = (
    REPO_ROOT / "libero" / "libero" / "assets" / "perturbation_assets"
)


def vector(text: str | None, length: int = 3) -> list[float]:
    values = [float(value) for value in (text or "").split()]
    return values if len(values) == length else [0.0] * length


def add_boundary_sites(outer: ET.Element, bounds: tuple[list[float], list[float]]) -> None:
    lower, upper = bounds
    horizontal_radius = max(
        math.hypot(x, y)
        for x in (lower[0], upper[0])
        for y in (lower[1], upper[1])
    )
    sites = (
        ("bottom_site", [0.0, 0.0, lower[2]]),
        ("top_site", [0.0, 0.0, upper[2]]),
        ("horizontal_radius_site", [horizontal_radius, 0.0, 0.0]),
    )
    for name, position in sites:
        ET.SubElement(
            outer,
            "site",
            {
                "name": name,
                "pos": " ".join(f"{value:.8g}" for value in position),
                "size": "0.005",
                "rgba": "0 0 0 0",
            },
        )


def indent_and_write(root: ET.Element, destination: Path) -> None:
    ET.indent(root, space="  ")
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="unicode", xml_declaration=False)
    with destination.open("a", encoding="utf-8") as stream:
        stream.write("\n")


def rebase_asset_files(asset: ET.Element | None, source_dir: Path, destination: Path) -> None:
    if asset is None:
        return
    for element in asset:
        file_name = element.get("file")
        if file_name is None:
            continue
        source_path = (source_dir / file_name).resolve()
        relative = source_path.relative_to(REPO_ROOT).as_posix()
        target_parent = destination.parent.resolve()
        target_depth = len(target_parent.relative_to(REPO_ROOT).parts)
        element.set("file", "../" * target_depth + relative)


def dimensions_from_meta(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^dimensions:\s*\[([^]]+)]", text, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing dimensions in {path}")
    return [float(value.strip()) for value in match.group(1).split(",")]


def adapt_prl_assets(root: Path, output: Path) -> list[dict]:
    source_root = root / "vendor" / "prl_assets" / "src" / "prl_assets" / "objects"
    records = []
    for source_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        xml_files = sorted(source_dir.glob("*.xml"))
        meta_path = source_dir / "meta.yaml"
        if len(xml_files) != 1 or not meta_path.exists():
            continue
        name = source_dir.name
        destination = output / "prl_objects" / name
        destination.mkdir(parents=True, exist_ok=True)

        tree = ET.parse(xml_files[0])
        source_body = tree.getroot().find("./worldbody/body")
        if source_body is None:
            raise ValueError(f"No world body in {xml_files[0]}")
        dimensions = dimensions_from_meta(meta_path)
        body_position = vector(source_body.get("pos"))
        lower = [
            body_position[0] - dimensions[0] / 2,
            body_position[1] - dimensions[1] / 2,
            body_position[2] - dimensions[2] / 2,
        ]
        upper = [
            body_position[0] + dimensions[0] / 2,
            body_position[1] + dimensions[1] / 2,
            body_position[2] + dimensions[2] / 2,
        ]

        root_element = tree.getroot()
        adapted_xml = destination / f"{name}.xml"
        rebase_asset_files(root_element.find("asset"), source_dir, adapted_xml)
        worldbody = root_element.find("worldbody")
        assert worldbody is not None
        worldbody.clear()
        outer = ET.SubElement(worldbody, "body")
        inner = ET.SubElement(outer, "body", {"name": "object"})
        for key, value in source_body.attrib.items():
            if key != "name":
                inner.set(key, value)
        for child in source_body:
            if child.tag in {"freejoint", "joint"}:
                continue
            if child.tag == "geom":
                visual = child.get("contype") == "0" or "visual" in child.get("name", "")
                child.set("group", "1" if visual else "0")
            inner.append(child)
        add_boundary_sites(outer, (lower, upper))
        indent_and_write(root_element, adapted_xml)
        records.append(
            {
                "id": f"prl/{name}",
                "format": "mjcf",
                "path": adapted_xml.relative_to(root).as_posix(),
                "source_asset": f"vendor/prl_assets/src/prl_assets/objects/{name}",
                "license": "MIT",
                "dimensions_m": dimensions,
                "readiness": "ready_mjcf",
            }
        )
    return records


def obj_bounds(path: Path, offset: list[float]) -> tuple[list[float], list[float]]:
    lower = [math.inf, math.inf, math.inf]
    upper = [-math.inf, -math.inf, -math.inf]
    with path.open("r", encoding="utf-8", errors="ignore") as stream:
        for line in stream:
            if not line.startswith("v "):
                continue
            values = [float(value) for value in line.split()[1:4]]
            for index, value in enumerate(values):
                value += offset[index]
                lower[index] = min(lower[index], value)
                upper[index] = max(upper[index], value)
    if not all(math.isfinite(value) for value in lower + upper):
        raise ValueError(f"No vertices in {path}")
    return lower, upper


def adapt_ycb_assets(root: Path, output: Path) -> list[dict]:
    source_root = (
        root / "vendor" / "pybullet_ycb" / "pybullet_object_models" / "ycb_objects"
    )
    records = []
    for source_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        urdf_path = source_dir / "model.urdf"
        if not urdf_path.exists():
            continue
        urdf = ET.parse(urdf_path).getroot()
        visual_mesh = urdf.find("./link/visual/geometry/mesh")
        collision_mesh = urdf.find("./link/collision/geometry/mesh")
        if visual_mesh is None or collision_mesh is None:
            continue
        visual_file = visual_mesh.get("filename")
        collision_file = collision_mesh.get("filename")
        if visual_file is None or collision_file is None:
            continue
        origin = urdf.find("./link/visual/origin")
        offset = vector(origin.get("xyz") if origin is not None else None)
        mass_element = urdf.find("./link/inertial/mass")
        mass = float(mass_element.get("value", "0.1")) if mass_element is not None else 0.1

        name = source_dir.name
        destination = output / "ycb_objects" / name
        destination.mkdir(parents=True, exist_ok=True)
        texture_candidates = sorted(source_dir.glob("*.png"))
        adapted_xml = destination / f"{name}.xml"

        relative_source = source_dir.relative_to(REPO_ROOT).as_posix()
        target_depth = len(adapted_xml.parent.relative_to(REPO_ROOT).parts)
        source_prefix = "../" * target_depth + relative_source + "/"

        mjcf = ET.Element("mujoco", {"model": name})
        ET.SubElement(mjcf, "compiler", {"angle": "radian"})
        asset = ET.SubElement(mjcf, "asset")
        ET.SubElement(
            asset,
            "mesh",
            {"name": "visual_mesh", "file": source_prefix + visual_file},
        )
        ET.SubElement(
            asset,
            "mesh",
            {"name": "collision_mesh", "file": source_prefix + collision_file},
        )
        material_attributes = {"name": "visual_material"}
        if texture_candidates:
            texture_file = source_prefix + texture_candidates[0].name
            ET.SubElement(
                asset,
                "texture",
                {"name": "visual_texture", "type": "2d", "file": texture_file},
            )
            material_attributes["texture"] = "visual_texture"
        ET.SubElement(asset, "material", material_attributes)
        worldbody = ET.SubElement(mjcf, "worldbody")
        outer = ET.SubElement(worldbody, "body")
        inner = ET.SubElement(outer, "body", {"name": "object"})
        position = " ".join(str(value) for value in offset)
        ET.SubElement(
            inner,
            "geom",
            {
                "name": "visual",
                "type": "mesh",
                "mesh": "visual_mesh",
                "material": "visual_material",
                "pos": position,
                "group": "1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
        ET.SubElement(
            inner,
            "geom",
            {
                "name": "collision",
                "type": "mesh",
                "mesh": "collision_mesh",
                "pos": position,
                "group": "0",
                "mass": str(mass),
                "friction": "0.8 0.005 0.0001",
                "rgba": "0.8 0.8 0.8 0.3",
            },
        )
        bounds = obj_bounds(source_dir / visual_file, offset)
        add_boundary_sites(outer, bounds)
        indent_and_write(mjcf, adapted_xml)
        dimensions = [bounds[1][index] - bounds[0][index] for index in range(3)]
        records.append(
            {
                "id": f"ycb/{name}",
                "format": "mjcf",
                "path": adapted_xml.relative_to(root).as_posix(),
                "source_asset": (
                    "vendor/pybullet_ycb/pybullet_object_models/ycb_objects/" + name
                ),
                "license": "LGPL-2.1-only",
                "dimensions_m": dimensions,
                "readiness": "ready_mjcf",
            }
        )
    return records


def adapt_robocasa_handles(root: Path, output: Path) -> list[dict]:
    source_root = (
        root
        / "vendor"
        / "robocasa_fixtures"
        / "robocasa"
        / "models"
        / "assets"
        / "fixtures"
        / "handles"
    )
    records = []
    handle_specs = {
        "bar_handle": ([0.06, 0.08, 0.40], [-0.03, -0.08, -0.20], [0.03, 0.0, 0.20]),
        "boxed_handle": ([0.06, 0.08, 0.40], [-0.03, -0.08, -0.20], [0.03, 0.0, 0.20]),
        "knob_handle": ([0.04, 0.04, 0.04], [-0.02, -0.04, -0.02], [0.02, 0.0, 0.02]),
    }
    for name, (dimensions, lower, upper) in handle_specs.items():
        source_xml = source_root / f"{name}.xml"
        tree = ET.parse(source_xml)
        source_object = tree.getroot().find("./worldbody/body/body[@name='object']")
        if source_object is None:
            raise ValueError(f"No object body in {source_xml}")
        mjcf = ET.Element("mujoco", {"model": name})
        ET.SubElement(mjcf, "compiler", {"angle": "radian"})
        worldbody = ET.SubElement(mjcf, "worldbody")
        outer = ET.SubElement(worldbody, "body")
        inner = ET.SubElement(outer, "body", {"name": "object"})
        for child in source_object:
            if child.tag != "geom":
                continue
            attributes = dict(child.attrib)
            attributes.pop("material", None)
            attributes.pop("class", None)
            attributes["group"] = "0"
            attributes["rgba"] = "0.55 0.42 0.18 1"
            inner.append(ET.Element("geom", attributes))
        add_boundary_sites(outer, (lower, upper))
        destination = output / "robocasa_handles" / name / f"{name}.xml"
        indent_and_write(mjcf, destination)
        records.append(
            {
                "id": f"robocasa/{name}",
                "format": "mjcf",
                "path": destination.relative_to(root).as_posix(),
                "source_asset": (
                    "vendor/robocasa_fixtures/robocasa/models/assets/fixtures/handles/"
                    f"{name}.xml"
                ),
                "license": "CC-BY-4.0",
                "dimensions_m": dimensions,
                "readiness": "ready_mjcf",
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt pinned perturbation assets to LIBERO-compatible MJCF."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = root / "adapted"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    records = []
    records.extend(adapt_prl_assets(root, output))
    records.extend(adapt_ycb_assets(root, output))
    records.extend(adapt_robocasa_handles(root, output))
    (root / "adapted_catalog.json").write_text(
        json.dumps({"format_version": 1, "assets": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Adapted {len(records)} assets into {output}")


if __name__ == "__main__":
    main()
