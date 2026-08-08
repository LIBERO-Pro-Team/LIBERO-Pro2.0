# prl_assets

Reusable manipulation objects (cans, bins, tableware, containers) for MuJoCo simulation.

![Assets Preview](docs/assets_preview.png)

This package provides simulation models and metadata for common manipulation objects like cans, bottles, tableware, and containers. Objects follow the `asset_manager` metadata format for compatibility with perception and planning pipelines.

## Installation

```bash
uv add prl_assets
```

For development:
```bash
git clone https://github.com/personalrobotics/prl_assets.git
cd prl_assets
uv sync --dev
```

## Quick Start

Use with `asset_manager` to load objects:

```python
from asset_manager import AssetManager
from prl_assets import OBJECTS_DIR

# Initialize asset manager with prl_assets objects
assets = AssetManager(OBJECTS_DIR)

# List available objects
print(assets.list())
# ['can', 'cracker_box', 'fuze_bottle', 'gelatin_box', 'herring_tin',
#  'lunchbox', 'notebook', 'plastic_bowl', 'plastic_glass', 'plastic_plate',
#  'pocky_box', 'pop_tarts_case', 'spam_can', 'recycle_bin', 'sugar_box',
#  'wicker_tray', 'yellow_tote']

# Get path to simulation model
can_path = assets.get_path("can", "mujoco")

# Load in MuJoCo
import mujoco
model = mujoco.MjModel.from_xml_path(can_path)

# Get object metadata
meta = assets.get("can")
print(meta["dimensions"])  # [0.066, 0.066, 0.123]
print(meta["mass"])        # 0.05 kg

# Find objects by category
containers = assets.by_category("container")
```

## Available Objects

| Object | Description | Collision |
|--------|-------------|-----------|
| `can` | Aluminum soda/beer can | cylinder |
| `cracker_box` | Cheez-It crackers box | box |
| `fuze_bottle` | Beverage bottle with texture | cylinder |
| `gelatin_box` | Jell-O gelatin box | box |
| `herring_tin` | MW Polar herring tin | box + 2 cylinders |
| `lunchbox` | Wildkin insulated lunch box | box |
| `notebook` | Amazon Basics hardcover notebook | box |
| `plastic_bowl` | Tableware bowl (nestable) | mesh |
| `plastic_glass` | Drinking glass | cylinder |
| `plastic_plate` | Dinner plate (stackable) | mesh |
| `pocky_box` | Pocky biscuit sticks box | box |
| `pop_tarts_case` | Pop-Tarts food box | box |
| `spam_can` | SPAM canned meat | box |
| `recycle_bin` | Open-top recycling bin (hollow) | 5 boxes |
| `sugar_box` | Domino sugar box | box |
| `wicker_tray` | Serving tray (hollow) | 5 boxes |
| `yellow_tote` | Storage tote (hollow) | 5 boxes |

## Object Structure

Each object follows a standardized directory structure:

```
objects/
└── object_name/
    ├── meta.yaml          # Object metadata
    ├── object_name.xml    # MuJoCo model
    └── *_visual.obj       # Visual mesh (optional)
```

### Metadata Format

The `meta.yaml` file contains all object properties:

```yaml
name: can
description: Standard aluminum soda/beer can
category: [container, recyclable, graspable]

# Physical properties
mass: 0.05  # kg
dimensions: [0.066, 0.066, 0.123]  # meters [X, Y, Z] in resting pose; Z = height
material: aluminum

# Geometric properties for grasp planning
geometric_properties:
  type: cylinder
  radius: 0.033
  height: 0.123

# Simulator-specific configuration
mujoco:
  xml_path: can.xml
  scale: 1.0
  friction: [0.6, 0.005, 0.0001]

# Perception aliases for detection systems
perception:
  aliases: ["can", "soda can", "beer can"]

# Manipulation policy hints
policy:
  grasping:
    affordances: [lift, pour]
    preferred_grasp_type: side_grasp
    difficulty: easy
```

## Adding New Objects

1. Create a new directory under `src/prl_assets/objects/`
2. Add a `meta.yaml` with required fields (see format below)
3. Add MuJoCo XML model following the conventions below
4. Add visual mesh (`.obj` file) if needed
5. Verify with scripts:
   ```bash
   # Check coordinate frame and collision alignment
   uv run python scripts/inspect_object.py your_object

   # Validate against standards
   uv run python scripts/validate_objects.py your_object
   ```
6. Update the objects table in this README

### MuJoCo Model Requirements

Objects used with `mj_environment` must follow these conventions:

```xml
<mujoco model="object_name">
  <worldbody>
    <body name="object_name" pos="0 0 {half_height}">
      <freejoint name="object_name_joint"/>  <!-- Required for positioning -->
      <!-- geoms, sites, etc. -->
    </body>
  </worldbody>
</mujoco>
```

- **freejoint**: Required for `registry.activate()` to set object position/orientation
- **body name**: Should match the object type (becomes `{type}_{index}` when loaded)

### Coordinate Frame Standard

All objects must follow this coordinate frame convention:

1. **Origin at bottom center**: The body origin is at the center of the object's base (bottom surface) in its canonical resting pose
2. **Z-up orientation**: The object's primary axis is aligned with +Z
3. **Rests on z=0**: When placed at position (x, y, 0), the object sits on a z=0 surface
4. **Canonical resting pose**: The stable pose the object would naturally rest in (e.g., can upright, box on largest face)
5. **Dimensions in resting frame**: The `dimensions` field in meta.yaml is [X, Y, Z] in the canonical resting pose, where **Z is always the height when resting**. For a flat object (e.g., herring tin) that rests on its largest face, Z is the thin dimension.

**Implementation**: The body `pos` attribute should offset the origin by half the object's height (dimensions[2]/2):
```xml
<!-- For a cylinder of height 0.123m -->
<body name="can" pos="0 0 0.0615">
```

**Collision and visual alignment**: Collision geoms must be aligned with visual meshes. Both should be centered at the body origin with matching dimensions.

**Verification**: Run visualization scripts to verify object geometry:

```bash
# Inspect a single object with collision overlay
uv run python scripts/inspect_object.py can

# Visualize all objects in a grid
uv run python scripts/viz_all_objects.py

# Physics demo with stacking
uv run python scripts/viz_stacking_demo.py

# Validate all objects against standards
uv run python scripts/validate_objects.py
```

## Scripts

| Script | Description |
|--------|-------------|
| `inspect_object.py` | Visualize single object with collision overlay and coordinate axes |
| `viz_all_objects.py` | Display all 17 objects in a grid with collision geometry |
| `viz_stacking_demo.py` | Physics demo: stacked dishes on tray, objects in tote |
| `validate_objects.py` | Check objects against coordinate frame and collision standards |
| `recenter_mesh.py` | Utility to re-center mesh origin to centroid |

## License

MIT License - see LICENSE file for details.
