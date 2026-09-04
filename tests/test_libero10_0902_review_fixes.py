from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBERO10 = (
    ROOT
    / "assets"
    / "bddl"
    / "libero-pro2.0-1680-v1"
    / "libero_10"
)
TASK2_NAME = "KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it.bddl"


def _case_block(text: str, case_id: str) -> str:
    marker = f"      ({case_id}\n"
    start = text.index(marker) + 6
    depth = 0
    for index in range(start, len(text)):
        depth += text[index] == "("
        depth -= text[index] == ")"
        if depth == 0:
            return text[start : index + 1]
    raise AssertionError(f"unterminated {case_id} block")


def test_task2_d05_obstacle_overlaps_the_transport_corridor() -> None:
    path = LIBERO10 / "02_dynamic" / f"D05__{TASK2_NAME}"
    text = path.read_text(encoding="utf-8")
    block = _case_block(text, "D05")

    assert "(:active_cases D05)" in text
    assert "(:lateral_offset_m 0.030)" in block
    assert "(:physical_collision true)" in block
    assert "(:visual_only_asset false)" in block


def test_task2_s11_uses_only_the_reviewed_same_class_distractor() -> None:
    path = LIBERO10 / "01_static" / f"S11__{TASK2_NAME}"
    text = path.read_text(encoding="utf-8")
    active = _case_block(text, "S11")
    inactive_s06 = _case_block(text, "S06")

    assert "(:active_cases S11)" in text
    assert "(:asset_id libero/yellow_moka_pot)" in active
    assert "(:asset_scale 1.0)" in active
    assert "(:movable_asset true)" in active
    assert "(:physical_collision true)" in active
    assert "(:clear_of_task_entities true)" in active
    assert "(:asset_id prl/gelatin_box)" in inactive_s06
    assert "(:asset_scale 0.7)" in inactive_s06
