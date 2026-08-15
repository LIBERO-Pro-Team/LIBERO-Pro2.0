from pathlib import Path

import numpy as np
import pytest

from libero_remote.runner.video import ObservationVideoWriter, episode_video_path


def test_episode_video_path_contains_reproducibility_fields(tmp_path: Path) -> None:
    path = episode_video_path(
        tmp_path,
        model_name="pi0",
        suite="libero_goal",
        task_id=3,
        variant="D07",
        seed=42,
        init_state_id=2,
    )

    assert path == tmp_path / "pi0_libero_goal_task3_D07_seed42_init2.mp4"


def test_video_writer_rejects_missing_camera_before_loading_encoder(tmp_path: Path) -> None:
    writer = ObservationVideoWriter(tmp_path / "episode.mp4")

    with pytest.raises(ValueError, match="agentview_image"):
        writer.write({"robot0_eye_in_hand_image": np.zeros((8, 8, 3), dtype=np.uint8)})


@pytest.mark.parametrize(
    "frame",
    [
        np.zeros((8, 8), dtype=np.uint8),
        np.zeros((8, 8, 3), dtype=np.float32),
    ],
)
def test_video_writer_validates_frame_schema(tmp_path: Path, frame: np.ndarray) -> None:
    writer = ObservationVideoWriter(tmp_path / "episode.mp4")

    with pytest.raises(ValueError, match="Video frames must"):
        writer.write({"agentview_image": frame})


def test_video_writer_rejects_non_positive_fps(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="positive"):
        ObservationVideoWriter(tmp_path / "episode.mp4", fps=0)
