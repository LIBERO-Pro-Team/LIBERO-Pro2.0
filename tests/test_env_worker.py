import numpy as np

from libero_remote.worker.process import EnvWorker


def test_spawned_worker_preserves_environment_state_across_steps() -> None:
    worker = EnvWorker.start(backend="fake", timeout_seconds=5.0)
    try:
        created = worker.create(
            {
                "suite": "libero_goal",
                "task_id": 0,
                "init_state_id": 0,
                "seed": 42,
                "camera_names": ["agentview", "robot0_eye_in_hand"],
                "camera_height": 16,
                "camera_width": 16,
                "max_steps": 10,
            }
        )
        assert created["observation"]["robot0_joint_pos"][0] == 0.0

        first = worker.step(np.array([0.25, 0.0], dtype=np.float32))
        second = worker.step(np.array([0.25, 0.0], dtype=np.float32))

        assert first["observation"]["robot0_joint_pos"][0] == 0.25
        assert second["observation"]["robot0_joint_pos"][0] == 0.5
        assert second["worker_step_index"] == 2
    finally:
        worker.close()

    assert not worker.is_alive
