# 用户模型 Adapter 接入契约

## 结论

LIBERO-Pro2.0 远程评测平台不固定模型。xVLA 和 Pi0 是验证过的客户端参考 adapter，
不是服务端依赖、默认模型或允许列表。用户可使用任意模型，只需在用户端实现 `AgentAdapter`。

```text
任意模型/策略
  -> 用户 AgentAdapter
  -> 标准 observation / action
  -> RemoteRunClient
  -> 远程 LIBERO 环境
```

服务端不接收 checkpoint，不导入模型框架，也不执行模型预处理。模型名称和版本只用于用户侧记录，
不能改变服务端任务、调度、成功判定或重试规则。

## 最小接口

```python
from libero_remote.runner import AgentContext


class AgentAdapter:
    def reset(self, context: AgentContext) -> None:
        """开始独立 attempt，清空历史状态并固定模型侧随机性。"""

    def act(self, observation):
        """将平台标准 observation 映射为符合 action_schema 的 action。"""

    def close(self) -> None:
        """释放模型侧资源。"""
```

这是结构化接口，不要求继承基类。adapter 可以封装 PyTorch、JAX、TensorFlow、ONNX、
远端私有推理 API、传统规划器或人工控制逻辑。

## Adapter 负责的语义

- 根据模型训练约定处理相机方向、裁剪、resize、颜色空间和归一化。
- 将标准机器人状态映射为模型需要的 proprio 表示和坐标系。
- 使用 `context.language_instruction` 构造 prompt。
- 维护或清空 action chunk、历史帧、缓存和循环状态。
- 将模型输出反归一化为服务端声明的 action schema。
- 固定 checkpoint、processor、模型 RNG 和确定性算法设置。
- 检查 action shape、数值范围和 NaN/Inf，异常时显式失败。

服务端负责固定 BDDL、资产、init state、环境 seed、扰动计划、MuJoCo 状态、任务成功谓词和
环境侧结果。服务端不应包含任何具体模型的图像翻转、tokenizer、proprio 或 action 转换。

## AgentContext

调度 runner 在每个 attempt 开始时传入：

| 字段 | 作用 |
| --- | --- |
| `run_id/job_id/job_index` | 稳定定位任务和结果 |
| `episode_spec` | 服务端锁定的 suite、task、init state、seed、相机和控制模式 |
| `reproducibility` | job、runtime、MuJoCo 初态、首帧 observation 和扰动 plan 的五个指纹 |
| `language_instruction` | 当前任务语言指令 |
| `action_schema` | action 形状、范围、控制模式、坐标系与旋转表示 |
| `observation_schema_version` | 标准 observation 的版本 |

失败重试会创建新 attempt 和 lease generation，但 `episode_spec` 与五个复现指纹必须不变：
`job_fingerprint`、`runtime_fingerprint`、`initial_state_fingerprint`、
`initial_observation_fingerprint` 和 `perturbation_plan_fingerprint`。
adapter 的 `reset()` 必须使用其中的固定 seed 清空模型状态。若模型生成还包含随机性，用户应从该 seed
稳定派生 policy seed，不能使用领取时间、进程 ID 或 attempt 编号。

## 最小示例

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
    "task_id": 0,
    "init_state_id": 0,
    "seed": 142,
    "variant": "base",
    "control_mode": "relative",
    "camera_height": 256,
    "camera_width": 256,
    "max_steps": 300,
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

## 并发与隔离

- 每个账户使用独立 API key，客户端提交的 `owner_id` 不能覆盖认证身份。
- 每个 runner 进程只持有自己的 adapter 实例；不同账户不得共享有状态模型对象。
- 同一账户可以启动多个 runner，但每个 `runner_id` 必须唯一，并受单账户 Slot 配额限制。
- heartbeat 在独立线程运行，模型推理阻塞不会让有效 lease 静默过期。
- 陈旧 `lease_id + lease_generation` 无法 step、heartbeat 或提交结果。
- 服务端仅记录环境侧权威结果；用户侧模型日志是补充证据，不能覆盖 success。

## Adapter 验收

接入新模型前至少验证：

1. 固定 observation 黄金样本经 adapter 后的模型输入与该模型本地官方 pipeline 一致。
2. action 经后处理后与服务端 `action_schema` 的 shape、范围、控制模式和坐标系一致。
3. 相同 episode spec 和模型 seed 重复两次时，首个 action 以及完整 action hash 链一致。
4. `reset()` 确实清空 action queue、历史帧和模型缓存。
5. adapter 异常、超时和进程退出后 lease 被回收，不影响其他账户。
6. adapter 只依赖轻量客户端协议；服务端即使未安装该模型框架也能正常启动。
