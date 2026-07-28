# 远程环境并发调度

## 结构

```text
用户私有模型 -> AgentAdapter -> RemoteRunClient
              -> RunScheduler -> SessionManager -> EnvWorker -> LIBERO/MuJoCo/EGL
```

- `SessionManager` 只负责一个环境执行的顺序、幂等、校验和资源释放。
- `RunScheduler` 负责 episode 队列、用户公平性、Slot 分配、lease、心跳和恢复。
- 模型、checkpoint、显存和私有推理代码始终在用户端。
- SQLite 只保存 run、episode spec、attempt 和服务器结果，不保存 observation、模型或权重。

## 用户端 Interface

平台固定声明：

```python
class AgentAdapter:
    def reset(self, context): ...
    def act(self, observation): ...
    def close(self): ...
```

用户在 Adapter 内处理图像翻转、resize、prompt、proprio 映射、action
反归一化和限幅。服务器不识别模型类型。

```python
import numpy as np

from libero_remote import RemoteRunClient
from libero_remote.runner.scheduled import AgentContext, run_scheduled_run


class MyAdapter:
    def __init__(self):
        self.model = load_private_model()

    def reset(self, context: AgentContext) -> None:
        self.instruction = context.language_instruction
        self.model.reset()

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
        "max_steps": 300,
    }
    for task_id in range(10)
]

with RemoteRunClient("http://SERVER:8000") as client:
    run = client.submit_run("user-id", episodes)
    result = run_scheduled_run(
        client,
        run_id=run["run_id"],
        runner_id="machine-1-worker-1",
        adapter=MyAdapter(),
    )
    episode_records = client.get_episodes(run["run_id"])
```

同一用户可启动多个进程，每个进程使用不同 `runner_id`。每个 runner 只执行自己
run 中的任务，不会执行其他用户的 episode。

## 调度行为

- 一套 320 BDDL 被保存为 320 个独立 episode job。
- claim 成功时，调度器原子创建一个新 session 和独立 EnvWorker。
- 用户间按活跃 claim intent 轮询，用户内部按 episode FIFO。
- `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` 限制单用户占用。
- 模型推理期间，通用 runner 在线程中独立发送 heartbeat。
- heartbeat 超时、Adapter 异常或服务器重启时，未完成 episode 从 reset 重新排队。
- completed episode 和服务器结果写入 SQLite，重启后不会重复执行。
- `complete` 不接受客户端 success；成功状态只从服务器最后一次 committed step 读取。

## 主要配置

| 环境变量 | 默认值 | 作用 |
| --- | ---: | --- |
| `LIBERO_REMOTE_MAX_SESSIONS` | `1` | 服务器环境 Slot 总数 |
| `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` | `1` | 单用户活跃 Slot 上限 |
| `LIBERO_REMOTE_SCHEDULER_QUEUE_CAPACITY` | `4096` | 未完成 episode 总上限 |
| `LIBERO_REMOTE_HEARTBEAT_INTERVAL_SECONDS` | `15` | runner 心跳间隔 |
| `LIBERO_REMOTE_LEASE_GRACE_PERIOD_SECONDS` | `60` | lease 失联回收时间 |
| `LIBERO_REMOTE_CLAIM_INTENT_TTL_SECONDS` | `30` | 等待 runner 的活跃时间 |
| `LIBERO_REMOTE_SCHEDULER_DB_PATH` | `runtime/scheduler.sqlite3` | 调度状态数据库 |
| `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS` | `true` | 旧 session 接口兼容开关 |

部署迁移完成后将 `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS=false`，防止客户端绕过公平队列。
Docker Compose 已将 `runtime/` 挂载到容器内，重建容器不会丢失 run 进度。

## 运维约束

- API 保持单进程；当前 session registry 在进程内，不能启动多个 Uvicorn worker。
- `owner_id` 在未接入鉴权前只用于公平调度，不能作为安全身份。
- 服务只放在可信内网、VPN 或 SSH 隧道后。
- 真实容量必须依次压测 `1/2/4/8` 个 EGL 环境，根据 CPU、内存、显存、网络和延迟确定。
- `/v1/health` 返回 session 容量、队列占用、活跃 lease、等待 runner 和单用户配额。
