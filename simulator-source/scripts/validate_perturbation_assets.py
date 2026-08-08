from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = (
    REPO_ROOT / "libero" / "libero" / "assets" / "perturbation_assets"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_vendor_manifest(root: Path, errors: list[str]) -> int:
    manifest_path = root / "vendor_manifest.json"
    if not manifest_path.is_file():
        errors.append("Missing vendor_manifest.json")
        return 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.is_file():
            errors.append(f"Missing vendor file: {record['path']}")
            continue
        if path.stat().st_size != record["bytes"]:
            errors.append(f"Size mismatch: {record['path']}")
        if sha256(path) != record["sha256"]:
            errors.append(f"SHA256 mismatch: {record['path']}")
    return len(manifest["files"])


def validate_asset_catalog(root: Path, errors: list[str]) -> tuple[int, int]:
    catalog_path = root / "asset_catalog.json"
    if not catalog_path.is_file():
        errors.append("Missing asset_catalog.json")
        return 0, 0

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = catalog.get("assets", [])
    asset_ids = [record.get("id") for record in assets]
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("Duplicate asset ID in asset_catalog.json")
    known_asset_ids = set(asset_ids)
    for record in assets:
        asset_id = record.get("id", "<missing-id>")
        relative_path = record.get("path")
        if not relative_path or not (root / relative_path).is_file():
            errors.append(f"Missing catalog asset file for {asset_id}: {relative_path}")

    expected_coverage = {
        *(f"S{index:02d}" for index in range(1, 22)),
        *(f"D{index:02d}" for index in range(1, 22)),
    }
    coverage = catalog.get("perturbation_coverage", [])
    coverage_ids = [record.get("id") for record in coverage]
    if set(coverage_ids) != expected_coverage:
        missing = sorted(expected_coverage - set(coverage_ids))
        extra = sorted(set(coverage_ids) - expected_coverage)
        errors.append(f"Perturbation coverage mismatch; missing={missing}, extra={extra}")
    if len(coverage_ids) != len(set(coverage_ids)):
        errors.append("Duplicate perturbation ID in asset_catalog.json")

    for record in coverage:
        perturbation_id = record.get("id", "<missing-id>")
        if not record.get("mechanism"):
            errors.append(f"Missing mechanism for {perturbation_id}")
        if not record.get("note"):
            errors.append(f"Missing coverage note for {perturbation_id}")
        for asset_id in record.get("asset_ids", []):
            if asset_id not in known_asset_ids:
                errors.append(
                    f"Unknown asset {asset_id} referenced by {perturbation_id}"
                )
        for relative_path in record.get("local_resources", []):
            if not (REPO_ROOT / relative_path).exists():
                errors.append(
                    f"Missing local resource {relative_path} for {perturbation_id}"
                )
    return len(assets), len(coverage)


def validate_mjcf_shape(path: Path, errors: list[str]) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"Invalid XML {path}: {exc}")
        return
    object_body = root.find("./worldbody/body/body[@name='object']")
    if object_body is None:
        errors.append(f"Missing LIBERO object body: {path}")
    else:
        collision_geoms = 0
        for geom in object_body.iter("geom"):
            group = geom.get("group")
            if group not in {"0", "1"}:
                errors.append(f"Invalid or missing geom group in {path}: {group}")
            if group == "0":
                collision_geoms += 1
        if collision_geoms == 0:
            errors.append(f"No collision geom (group 0) in {path}")
    for site_name in ("bottom_site", "top_site", "horizontal_radius_site"):
        site = root.find(f"./worldbody/body/site[@name='{site_name}']")
        if site is None:
            errors.append(f"Missing {site_name}: {path}")
        elif len((site.get("pos") or "").split()) != 3:
            errors.append(f"Invalid {site_name} position: {path}")


def validate_mujoco(paths: list[Path], errors: list[str]) -> bool:
    try:
        import mujoco
    except ImportError:
        print("MuJoCo not installed; skipped engine compilation.")
        return False
    for path in paths:
        try:
            mujoco.MjModel.from_xml_path(str(path))
        except Exception as exc:  # MuJoCo raises several binding-specific exceptions.
            errors.append(f"MuJoCo compile failure {path}: {exc}")
    return True


def validate_robosuite(paths: list[Path], errors: list[str]) -> bool:
    try:
        from robosuite.models.objects import MujocoXMLObject
    except ImportError:
        print("robosuite not installed; skipped MujocoXMLObject loading.")
        return False
    for index, path in enumerate(paths):
        try:
            MujocoXMLObject(
                str(path),
                name=f"validation_{index}",
                joints=[{"type": "free", "damping": "0.0005"}],
                obj_type="all",
                duplicate_collision_geoms=False,
            )
        except Exception as exc:
            errors.append(f"robosuite load failure {path}: {exc}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate downloaded perturbation assets.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--require-engines", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    vendor_files = validate_vendor_manifest(root, errors)
    catalog_assets, perturbations = validate_asset_catalog(root, errors)
    paths = sorted((root / "adapted").rglob("*.xml")) + sorted(
        (root / "generated").rglob("*.xml")
    )
    for path in paths:
        validate_mjcf_shape(path, errors)
    mujoco_checked = validate_mujoco(paths, errors)
    robosuite_checked = validate_robosuite(paths, errors)
    if args.require_engines and not (mujoco_checked and robosuite_checked):
        errors.append("--require-engines was set but an engine dependency is missing")

    summary = {
        "vendor_files_verified": vendor_files,
        "catalog_assets_verified": catalog_assets,
        "perturbation_directions_verified": perturbations,
        "mjcf_files_verified": len(paths),
        "mujoco_compilation_checked": mujoco_checked,
        "robosuite_loading_checked": robosuite_checked,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
