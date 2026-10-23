# Remote Environment Scheduling

## Architecture

```text
Any user model -> AgentAdapter -> RemoteRunClient
              -> RunScheduler -> SessionManager -> EnvWorker -> LIBERO/MuJoCo/EGL
```

- `SessionManager` handles execution order, idempotency, validation, and resource release for one environment.
- `RunScheduler` manages episode queues, fairness across users, slot allocation, leases, heartbeats, and recovery.
- Models, checkpoints, model GPU memory, and private inference code remain on the client.
- SQLite stores runs, episode specs, attempts, and server results, not observations, models, or weights.
- The platform does not require or identify specific models such as xVLA or Pi0; the included model adapters are reference implementations.

## Client interface

The platform defines this interface:

```python
class AgentAdapter:
    def reset(self, context): ...  # Clear model state and fix model-side RNG for each attempt.
    def act(self, observation): ...
    def close(self): ...
```

The user's adapter handles image flips, resizing, prompts, proprioceptive mappings, action
unnormalization, and clipping. `context.episode_spec` is the server-locked task configuration.
`context.reproducibility` contains five fingerprints for the job, runtime, initial MuJoCo state,
first observation, and perturbation plan. The server does not identify model types or load model dependencies.

```python
import numpy as np

from libero_remote import RemoteRunClient
from libero_remote.runner import AgentContext, run_scheduled_run


class MyAdapter:
    def __init__(self):
        self.model = load_private_model()

    def reset(self, context: AgentContext) -> None:
        self.instruction = context.language_instruction
        self.model.reset(seed=context.episode_spec["seed"])

    def act(self, observation):
        action = self.model.predict(observation, self.instruction)
        return np.asarray(action, dtype=np.float32)

    def close(self) -> None:
        self.model.close()


episodes = [
    {
        "suite": "libero_goal",
        "task_id": task_id,
        "init_state_id": 0,
        "seed": 42,
        "variant": "base",
        "camera_height": 256,
        "camera_width": 256,
    }
    for task_id in range(10)
]

with RemoteRunClient("http://SERVER:8000", api_key="ACCOUNT_API_KEY") as client:
    run = client.submit_run(episodes)
    result = run_scheduled_run(
        client,
        run_id=run["run_id"],
        runner_id="machine-1-worker-1",
        adapter=MyAdapter(),
    )
    episode_records = client.get_episodes(run["run_id"])
```

When `max_steps` is omitted, the scheduler reads the manifest before storing the job and fixes
the selected task's official PI0 suite limit: Spatial 220, Object 280, Goal 300, or LIBERO-10 520.
Pass `max_steps` explicitly only when intentionally overriding the evaluation protocol.

`AgentAdapter` is a structural protocol: implementing the three methods is sufficient, with no
platform base-class inheritance required. Users can connect any VLA, reinforcement learning policy,
planner, or custom controller. Returned actions must match the server's `action_schema`;
otherwise the attempt fails explicitly instead of silently changing control semantics.

A user can start multiple processes with distinct `runner_id` values. Each runner executes
only jobs in its own run, never another user's episodes.

## Scheduling behavior

- The filtered 1701 valid task combinations are stored as 1701 independent episode jobs. The scheduler must read the versioned manifest directly rather than reconstructing a Cartesian product of suites, tasks, and perturbation cases.
- A successful claim atomically creates a new session and a separate EnvWorker.
- Active claim intents are served round-robin across users, with episode FIFO within each user.
- `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` limits each user's occupancy.
- The generic runner sends heartbeats in a separate thread during model inference.
- On heartbeat timeout or infrastructure failure, an unfinished episode retries from reset using the same immutable job spec. Normal policy failures do not retry automatically.
- The normalized perturbation plan is persisted after the first reset. A retry is rejected if any fingerprint of the initial MuJoCo state, first observation, or plan changes.
- Completed episodes and server results are written to SQLite and are not executed again after a restart.
- `complete` does not accept client-reported success; success is read only from the server's last committed step.

## Main configuration

| Environment variable | Default | Purpose |
| --- | ---: | --- |
| `LIBERO_REMOTE_MAX_SESSIONS` | `1` | Total server environment slots |
| `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` | `1` | Maximum active slots per user |
| `LIBERO_REMOTE_SCHEDULER_QUEUE_CAPACITY` | `4096` | Maximum unfinished episodes |
| `LIBERO_REMOTE_MAX_ATTEMPTS` | `3` | Maximum attempts for infrastructure failures |
| `LIBERO_REMOTE_HEARTBEAT_INTERVAL_SECONDS` | `15` | Runner heartbeat interval |
| `LIBERO_REMOTE_LEASE_GRACE_PERIOD_SECONDS` | `60` | Lease reclamation delay after disconnection |
| `LIBERO_REMOTE_CLAIM_INTENT_TTL_SECONDS` | `30` | Activity window for a waiting runner |
| `LIBERO_REMOTE_SCHEDULER_DB_PATH` | `runtime/scheduler.sqlite3` | Scheduling state database |
| `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS` | `false` | Compatibility switch for the legacy session interface |

After deployment migration, set `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS=false` to prevent clients
from bypassing the fair queue. Docker Compose mounts `runtime/` into the container so rebuilding
the container preserves run progress.

## Operational constraints

- Keep the API single-process; the session registry is process-local and cannot support multiple Uvicorn workers.
- Production deployments must enable API key authentication; only the server maps key hashes to account identities.
- Accounts cannot read, advance, renew, complete, or close one another's Runs, Sessions, or Leases.
- Determine actual capacity by load-testing `1/2/4/8` EGL environments in sequence, considering CPU, RAM, GPU memory, network, and latency.
- `/v1/health` reports session capacity, queue occupancy, active leases, waiting runners, and per-user quotas.
