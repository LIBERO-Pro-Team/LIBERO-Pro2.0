import os

import numpy as np

from libero_remote import RemoteLiberoEnv

with RemoteLiberoEnv(
    base_url=os.environ.get("LIBERO_REMOTE_URL", "http://127.0.0.1:8000"),
    api_key=os.environ["LIBERO_REMOTE_API_KEY"],
    timeout=120.0,
) as env:
    observation, info = env.reset(
        suite="libero_goal",
        task_id=0,
        init_state_id=0,
        seed=42,
        variant="base",
        camera_height=64,
        camera_width=64,
        max_steps=1,
    )
    action = np.zeros(info["action_schema"]["shape"], dtype=np.float32)
    env.step(action, request_id="customer-smoke-step-0")
    result = env.result()

print(
    {
        "status": "passed",
        "session_id": info["session_id"],
        "observation_keys": sorted(observation),
        "result": result,
    }
)
