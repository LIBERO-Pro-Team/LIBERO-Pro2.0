# Third-party asset notices

The source URLs, pinned commits, copied files, sizes, and SHA-256 hashes are
recorded in `vendor_manifest.json`. The adapted MJCF files preserve a
`source_asset` field in `asset_catalog.json`.

## object_sim bowl

- Project: `vikashplus/object_sim`
- Source: <https://github.com/vikashplus/object_sim/tree/main/bowl>
- License: Apache-2.0, retained in
  `adapted/github_objects/object_sim_bowl/LICENSE`
- Changes: the upstream visual mesh and twelve contact meshes were wrapped in
  a LIBERO-compatible MJCF object with explicit geom groups, a 0.15 kg total
  collision mass, and placement boundary sites. The published task scale is
  `0.70` so the resulting bowl remains close to the original LIBERO bowl size.

## Personal Robotics Lab assets

- Project: `personalrobotics/prl_assets`
- Commit: `c7c474e74961c773f6adc44249ed33599fbf510a`
- License: MIT, retained in `vendor/prl_assets/LICENSE`
- Changes: XML body layout and relative asset paths were adapted for LIBERO;
  boundary sites and explicit geom groups were added.

## pybullet object models / YCB models

- Project: `eleramp/pybullet-object-models`
- Commit: `57cc4007607f6bcbb0a5364ccab7636faf7a91e4`
- Repository license: LGPL-2.1-only, retained in
  `vendor/pybullet_ycb/LICENSE`
- Changes: the selected URDF metadata, visual mesh, simplified collision
  mesh, and texture are referenced by newly generated LIBERO MJCF wrappers.

The selected folders reproduce object models associated with the YCB object
and video datasets. Before redistributing these files outside this research
bundle, also verify and comply with the applicable original YCB dataset terms
and attribution requirements; the repository-level LGPL notice should not be
assumed to replace third-party dataset terms.

## RoboCasa fixture assets

- Project: `robocasa/robocasa`
- Commit: `b4684e6ee37d377cc392e98302a6b916d588b415`
- Asset license: Creative Commons Attribution 4.0, as stated in the retained
  upstream README: <https://creativecommons.org/licenses/by/4.0/deed.en>
- Attribution: RoboCasa Team; see the retained README for the project papers
  and citation entries.
- Changes: bar, boxed, and knob handle geometry was extracted into
  self-contained LIBERO MJCF variants; upstream material references were
  replaced by a plain material and LIBERO boundary sites were added.

The repository's software `LICENSE` file is MIT, but its README separately
identifies assets and datasets as CC BY 4.0. The stricter asset attribution is
used in this bundle's catalog.
