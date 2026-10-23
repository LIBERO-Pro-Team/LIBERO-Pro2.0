# Model Adapter Contract

## Overview

The LIBERO-Pro2.0 remote evaluation platform is model-independent. xVLA and Pi0 are validated
client-side reference adapters, not server dependencies, default models, or an allowlist.
Any model can be used by implementing an `AgentAdapter` on the client.

```text
Any model/policy
  -> User AgentAdapter
  -> Standard observation / action
  -> RemoteRunClient
  -> Remote LIBERO environment
```

The server does not receive checkpoints, import model frameworks, or preprocess model inputs.
Model names and versions are client-side metadata; they cannot change server tasks, scheduling,
success criteria, or retry rules.

The public `libero_remote.runner` entry point exports only the model-independent adapter contract
and runner functions. Reference implementations must be imported explicitly from
`libero_remote.runner.xvla` or `libero_remote.runner.pi0`. Other models do not need to install,
import, or inherit either reference implementation.

## Minimal interface

```python
from libero_remote.runner import AgentContext


class AgentAdapter:
    def reset(self, context: AgentContext) -> None:
        """Start an independent attempt, clear history, and fix model-side randomness."""

    def act(self, observation):
        """Map a standard platform observation to an action matching action_schema."""

    def close(self) -> None:
        """Release model-side resources."""
```

This is a structural interface; no base-class inheritance is required. An adapter can wrap PyTorch,
JAX, TensorFlow, ONNX, a private remote inference API, a traditional planner, or manual control logic.

## Adapter responsibilities

- Apply the camera orientation, crop, resize, color-space, and normalization conventions used in training.
- Map standard robot state to the model's proprioceptive representation and coordinate frame.
- Construct prompts from `context.language_instruction`.
- Maintain or clear action chunks, frame history, caches, and recurrent state.
- Unnormalize model outputs into the server's declared action schema.
- Fix the checkpoint, processor, model RNG, and deterministic algorithm settings.
- Validate action shape, numeric range, and NaN/Inf values; fail explicitly on invalid output.

The server fixes BDDL, assets, initial state, environment seed, perturbation plan, MuJoCo state,
task success predicates, and environment-side results. It must not contain model-specific image
flips, tokenizers, proprioceptive mappings, or action conversions.

## AgentContext

The scheduled runner supplies the following at the start of each attempt:

| Field | Purpose |
| --- | --- |
| `run_id/job_id/job_index` | Stable task and result identifiers |
| `episode_spec` | Server-locked suite, task, initial state, seed, cameras, and control mode |
| `reproducibility` | Five fingerprints for the job, runtime, initial MuJoCo state, first observation, and perturbation plan |
| `language_instruction` | Current task instruction |
| `action_schema` | Action shape, range, control mode, coordinate frame, and rotation representation |
| `observation_schema_version` | Standard observation schema version |

A retry creates a new attempt and lease generation, but `episode_spec` and these five reproducibility
fingerprints must remain unchanged:
`job_fingerprint`, `runtime_fingerprint`, `initial_state_fingerprint`,
`initial_observation_fingerprint`, and `perturbation_plan_fingerprint`.
The adapter's `reset()` must clear model state using the fixed seed in the spec. If generation is
stochastic, derive a stable policy seed from that seed, not from claim time, process ID, or attempt number.

## Minimal example

```python
import numpy as np

from libero_remote import RemoteRunClient
from libero_remote.runner import AgentContext, run_scheduled_run


class MyModelAdapter:
    def __init__(self, checkpoint):
        self.policy = load_my_policy(checkpoint)

    def reset(self, context: AgentContext) -> None:
        self.instruction = context.language_instruction
        self.action_schema = context.action_schema
        self.policy.reset(seed=int(context.episode_spec["seed"]))

    def act(self, observation):
        model_input = my_preprocess(observation, self.instruction)
        action = my_postprocess(self.policy.predict(model_input), self.action_schema)
        return np.asarray(action, dtype=np.float32)

    def close(self) -> None:
        self.policy.close()


episodes = [{
    "suite": "libero_goal",
    "task_id": 9,
    "init_state_id": 0,
    "seed": 142,
    "variant": "base",
    "control_mode": "relative",
    "camera_height": 256,
    "camera_width": 256,
}]

with RemoteRunClient(
    "https://libero.example.com",
    api_key="ACCOUNT_API_KEY",
) as client:
    run = client.submit_run(episodes)
    result = run_scheduled_run(
        client,
        run_id=run["run_id"],
        runner_id="host-a-gpu-0",
        adapter=MyModelAdapter("/models/my-checkpoint"),
    )
```

By default, the server manifest resolves `max_steps` to the official PI0 limit for the suite;
the submission record stores the resolved integer. Explicitly override it in the episode only
when intentionally departing from the official protocol.

## Concurrency and isolation

- Each account uses a separate API key; a client-supplied `owner_id` cannot override authenticated identity.
- Each runner process owns its adapter instance; accounts must not share stateful model objects.
- An account can start multiple runners with unique `runner_id` values, subject to its slot quota.
- Heartbeats run in a separate thread so blocking model inference does not silently expire a valid lease.
- A stale `lease_id + lease_generation` cannot step, send heartbeats, or submit results.
- The server records authoritative environment results; client model logs are supplementary and cannot override success.

## Adapter acceptance checks

Before integrating a model, verify at least the following:

1. Given a fixed golden observation, the adapter produces model inputs matching the model's official local pipeline.
2. Postprocessed actions match the server `action_schema` in shape, range, control mode, and coordinate frame.
3. Repeating an episode spec and model seed twice produces the same first action and full action hash chain.
4. `reset()` clears the action queue, frame history, and model caches.
5. Adapter exceptions, timeouts, and process exits release the lease without affecting other accounts.
6. The adapter depends only on the lightweight client protocol; the server starts without the model framework installed.
