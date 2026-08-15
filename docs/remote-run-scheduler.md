# 远程环境并发调度

## 结构

```text
任意用户模型 -> AgentAdapter -> RemoteRunClient
              -> RunScheduler -> SessionManager -> EnvWorker -> LIBERO/MuJoCo/EGL
```

- `SessionManager` 只负责一个环境执行的顺序、幂等、校验和资源释放。
- `RunScheduler` 负责 episode 队列、用户公平性、Slot 分配、lease、心跳和恢复。
- 模型、checkpoint、显存和私有推理代码始终在用户端。
- SQLite 只保存 run、episode spec、attempt 和服务器结果，不保存 observation、模型或权重。
- 平台不要求或识别 xVLA、Pi0 等具体模型；仓库中的模型 adapter 仅是参考实现。

## 用户端 Interface

平台固定声明：

```python
class AgentAdapter:
    def reset(self, context): ...  # 每个 attempt 清空模型状态并固定模型侧 RNG
    def act(self, observation): ...
    def close(self): ...
```

用户在 Adapter 内处理图像翻转、resize、prompt、proprio 映射、action
反归一化和限幅。`context.episode_spec` 是服务端锁定的任务配置，
`context.reproducibility` 包含 job、runtime、MuJoCo 初态、首帧 observation 和扰动 plan
五个指纹。服务器不识别模型类型，也不加载模型依赖。

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
        "max_steps": 300,
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

`AgentAdapter` 是结构化协议：只要对象实现上述三个方法即可，不要求继承平台类。
用户可以连接任意 VLA、强化学习策略、规划器或自定义控制器。adapter 返回的 action 必须符合
服务端 `action_schema`，否则本次 attempt 明确失败，不会静默转换成其他控制语义。

同一用户可启动多个进程，每个进程使用不同 `runner_id`。每个 runner 只执行自己
run 中的任务，不会执行其他用户的 episode。

## 调度行为

- 当前筛选后的 1680 个有效任务组合被保存为 1680 个独立 episode job；调度器必须直接读取版本化 manifest，不得自行重构 suite、task 和扰动 case 的笛卡尔积。
- claim 成功时，调度器原子创建一个新 session 和独立 EnvWorker。
- 用户间按活跃 claim intent 轮询，用户内部按 episode FIFO。
- `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` 限制单用户占用。
- 模型推理期间，通用 runner 在线程中独立发送 heartbeat。
- heartbeat 超时或基础设施故障时，未完成 episode 以同一不可变 job spec 从 reset 重试；模型正常失败不自动重试。
- 第一次 reset 后持久化规范化扰动 plan；重试时 MuJoCo 初态、首帧 observation 或 plan 任一指纹变化都拒绝执行。
- completed episode 和服务器结果写入 SQLite，重启后不会重复执行。
- `complete` 不接受客户端 success；成功状态只从服务器最后一次 committed step 读取。

## 主要配置

| 环境变量 | 默认值 | 作用 |
| --- | ---: | --- |
| `LIBERO_REMOTE_MAX_SESSIONS` | `1` | 服务器环境 Slot 总数 |
| `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` | `1` | 单用户活跃 Slot 上限 |
| `LIBERO_REMOTE_SCHEDULER_QUEUE_CAPACITY` | `4096` | 未完成 episode 总上限 |
| `LIBERO_REMOTE_MAX_ATTEMPTS` | `3` | 基础设施类失败的最大 attempt 数 |
| `LIBERO_REMOTE_HEARTBEAT_INTERVAL_SECONDS` | `15` | runner 心跳间隔 |
| `LIBERO_REMOTE_LEASE_GRACE_PERIOD_SECONDS` | `60` | lease 失联回收时间 |
| `LIBERO_REMOTE_CLAIM_INTENT_TTL_SECONDS` | `30` | 等待 runner 的活跃时间 |
| `LIBERO_REMOTE_SCHEDULER_DB_PATH` | `runtime/scheduler.sqlite3` | 调度状态数据库 |
| `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS` | `false` | 旧 session 接口兼容开关 |

部署迁移完成后将 `LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS=false`，防止客户端绕过公平队列。
Docker Compose 已将 `runtime/` 挂载到容器内，重建容器不会丢失 run 进度。

## 运维约束

- API 保持单进程；当前 session registry 在进程内，不能启动多个 Uvicorn worker。
- 正式部署必须启用 API key 鉴权；账户身份只由服务端从 key 哈希映射得出。
- 不同账户不能读取、推进、续租、完成或关闭彼此的 Run、Session 和 Lease。
- 真实容量必须依次压测 `1/2/4/8` 个 EGL 环境，根据 CPU、内存、显存、网络和延迟确定。
- `/v1/health` 返回 session 容量、队列占用、活跃 lease、等待 runner 和单用户配额。
