# LIBERO-Pro perturbation assets

This directory contains the asset bundle selected for the 21 static and 21
dynamic non-physical perturbation directions. The bundle is deliberately
smaller than the upstream repositories: it includes the reusable manipulation
objects and fixture parts needed by the benchmark, plus generated structures
for clearance, occlusion, and approach-path tests.

## Ready-to-use inventory

- 17 PRL manipulation objects plus one table model (MIT): containers,
  tableware, boxes, bottles, clutter objects, and a support-surface reference.
- 16 textured YCB object models from `pybullet-object-models`
  (LGPL-2.1-only in the selected repository): visual meshes, simplified
  collision meshes, textures, and inertial metadata.
- 3 RoboCasa handle geometries (CC BY 4.0 assets): bar, boxed, and knob handle.
- 5 locally generated parameterized MJCF structures (MIT): barrier panel,
  occlusion screen, opening frame, slotted receiver, and support riser.

All 42 adapted/generated MJCF files use LIBERO's expected nested
`body name="object"` layout and include `bottom_site`, `top_site`, and
`horizontal_radius_site`. See `asset_catalog.json` for dimensions, paths,
asset sets, and the S01-S21/D01-D21 coverage mapping.

## Provenance and licenses

The exact repository URLs and commit hashes are in `vendor_manifest.json`.
Each vendor directory retains its upstream `LICENSE` and `README.md`; the
bundle-specific attribution and modification record is in
`THIRD_PARTY_NOTICES.md`. Review the upstream terms before publishing or
redistributing a benchmark bundle.

RoboCasa's complete kitchen asset download is about 10 GB and is not required
by the three self-contained adapted handle variants. The bundle therefore
pins only the handle geometry files; use the entries marked `ready_mjcf` in
`asset_catalog.json`.

## Reproduce and validate

Run from the repository root:

```powershell
python scripts/fetch_perturbation_assets.py
python scripts/generate_perturbation_primitives.py
python scripts/adapt_perturbation_assets.py
python scripts/build_perturbation_asset_catalog.py
python scripts/validate_perturbation_assets.py
```

`fetch_perturbation_assets.py` replaces only the `vendor` subdirectories with
the pinned upstream content. The generated and adapted directories can always
be rebuilt from the scripts and vendor manifest.

Asset availability does not by itself make a perturbation valid. Scene
generation must still enforce collision-free initialization, task semantic
equivalence, reachability, full-path feasibility, and recoverability gates as
specified in the benchmark document.
