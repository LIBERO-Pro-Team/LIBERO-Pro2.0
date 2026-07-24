# Remote Environment Session Design Open Issues

> Scope: LIBERO-PRO remote evaluation service, phase 1 design review.

本文整理远程环境服务在第一阶段实现前必须明确的设计问题。核心原则是：服务端通过 `session_id` 持续维护唯一环境实例，客户端只通过 `reset()`、`step()` 和 `close()` 推进环境，任何请求都不能导致同一个 action 被重复执行或导致环境状态被意外重建。

## 1. 环境进程的运行方式

当前方案计划将 `OffScreenRenderEnv` 直接保存在 FastAPI 服务进程中，但 MuJoCo、EGL 和 OpenGL 渲染上下文可能存在进程或线程绑定问题。如果环境直接驻留在 API 进程中，单个渲染上下文崩溃可能导致整个服务退出，`env.step()` 超时后也难以中断正在执行的底层 MuJoCo 操作。

建议第一阶段就采用独立 worker 进程：

```text
FastAPI
-> SessionManager
-> EnvWorker
-> OffScreenRenderEnv
-> LIBERO / MuJoCo
```

需要明确以下约束：

- `OffScreenRenderEnv` 只在 `EnvWorker` 进程内创建、reset、step 和 close。
- MuJoCo、EGL 和 OpenGL 渲染上下文也只在 `EnvWorker` 进程内初始化。
- FastAPI 进程不直接持有 MuJoCo 环境对象，只持有 session 元数据、worker 句柄和请求缓存。
- 同一个 session 的所有环境操作都通过同一个 worker 串行执行。
- 不允许不同请求在线程池中的不同线程直接操作同一个环境。
- `env.step()` 超时后，API 进程不能假设底层操作已停止；应将 worker 标记为不可恢复，终止 worker 进程，并将当前 episode 标记为 `FAILED`。
- 环境或渲染上下文崩溃时，只影响对应 session 的 worker，不应导致 FastAPI 主进程退出。
- `EnvWorker` 启动方式建议使用 `spawn`，避免 `fork` 继承已初始化的 CUDA、EGL、OpenGL 或 MuJoCo 状态。

第一阶段即使只支持一个活跃 session，也不应把环境设计成 API 进程内的全局单例。

## 2. Session、Episode 和 Reset 的关系

当前接口同时存在：

```text
POST /v1/sessions
POST /v1/sessions/{session_id}/reset
```

需要明确区分两个概念：

```text
Session: 一次环境资源占用周期
Episode: Session 中的一次完整任务执行
```

建议语义如下：

- `POST /v1/sessions` 创建 session、启动 `EnvWorker`、创建环境并执行第一次 reset。
- `POST /v1/sessions` 成功时返回 `session_id`、`episode_id`、initial observation、任务信息、action schema 和 observation schema。
- 客户端第一次调用 `reset()` 时只调用 `POST /v1/sessions`，不需要先创建 session 再额外 reset。
- `POST /v1/sessions/{session_id}/reset` 用于同一个 session 中开启新的 episode。
- 一个 session 可以连续运行多个 episode，但同一时间只能有一个 active episode。
- 每次 reset 都生成新的 `episode_id`，并将 step index 归零。
- reset 后，旧 `episode_id` 的 step 请求全部返回 `STALE_EPISODE`。
- `task`、`init_state_id`、`seed` 可以作为 episode 参数；第一阶段可限制同一 session 内 reset 时必须使用相同 task，也可以允许 reset 时显式覆盖，但协议必须固定。
- episode 结束后，环境资源继续保留在 session 中，直到客户端 reset、close、session 超时或 worker 失败。

推荐状态流：

```text
CREATING
-> READY(episode active, step_index = 0)
-> STEPPING
-> READY
-> TERMINATED | TRUNCATED
-> READY(after reset) | CLOSED
```

只有环境完整初始化并成功生成 initial observation 后，session 才能进入 `READY`。

## 3. 通过 Session ID 持续维护环境状态

服务端必须保证同一个 `session_id` 在整个 episode 中始终对应同一个环境实例：

```text
session_id
-> EnvWorker
-> OffScreenRenderEnv
-> 当前 MuJoCo 状态
```

不能在每次 `step()` 请求时重新创建环境。以下状态应持续保存在服务端环境中：

- 机器人关节状态。
- 末端执行器状态。
- 夹爪状态。
- 物体位置与姿态。
- MuJoCo `qpos` 和 `qvel`。
- 当前仿真时间。
- 当前 episode 进度与 step index。
- 环境随机数状态。
- 动态扰动状态。

客户端发送 action 后，服务端在同一个环境实例上执行 `env.step(action)`，并将下一步 observation、reward、success、terminated 和 truncated 返回给客户端。客户端不应也不能承担保存 MuJoCo 状态的职责。

## 4. 同一 Session 的操作顺序

同一个环境不能同时执行多个操作，需要防止：

```text
两个 step 同时执行
reset 与 step 同时执行
close 与 step 同时执行
两个 reset 同时执行
```

同一 session 内的合法顺序为：

```text
reset
-> step 0
-> step 1
-> ...
-> terminated / truncated
-> reset 或 close
```

建议实现 session 级锁，而不是全局锁：

- 每个 session 拥有独立异步锁或互斥队列。
- `step`、`reset` 和 `close` 必须获取 session 锁。
- 锁必须通过 `try/finally` 释放，请求异常不能遗留锁。
- `step` 执行期间继续持有锁，直到结果、错误或 worker 失败状态确定。
- 如果 worker 崩溃，SessionManager 应释放锁，将 session 状态置为 `FAILED`，并拒绝后续 step。
- `GET /v1/sessions/{id}` 可以读取快照状态；是否允许与 step 并发需要明确。如果允许并发，返回的只能是上一条已提交 step 的快照，不能读取半更新状态。
- `close` 与正在执行的 `step` 竞争时，应等待锁；如果 step 超时导致 worker 被终止，close 应执行幂等清理。

锁保护的是服务端状态提交边界，不只是 HTTP handler 的临界区。

## 5. 避免 Action 被重复执行

当服务端已经执行 action，但响应因网络问题丢失时，客户端可能重复发送同一个 `step()` 请求。仅使用 `request_id` 不足以处理请求重复、乱序和旧 episode 请求。

建议每个 step 请求同时携带：

```text
episode_id
expected_step_index
request_id
action
```

服务端处理规则：

| 条件 | 处理 |
| --- | --- |
| `episode_id` 不匹配 | 返回 `STALE_EPISODE` |
| 相同 `request_id` + 相同 action | 返回缓存结果 |
| 相同 `request_id` + 不同 action | 返回 `REQUEST_ID_CONFLICT` |
| `expected_step_index` 小于当前 step | 返回 `DUPLICATE_OR_EXPIRED_STEP`，如缓存仍存在则可返回缓存结果 |
| `expected_step_index` 大于当前 step | 返回 `OUT_OF_ORDER_STEP` |
| 当前 episode 已 terminated/truncated | 返回 `EPISODE_NOT_ACTIVE` |
| action 校验失败 | 返回 `INVALID_ACTION`，且不得推进环境 |

缓存内容至少包含：

- `request_id`
- `episode_id`
- `expected_step_index`
- action 的稳定 hash
- step 响应或稳定错误
- 响应产生时间

如果 worker 在执行 action 过程中崩溃，服务端无法证明 action 是否完成，应将当前 episode 标记为 `FAILED`。同一 `request_id` 重放时返回失败状态，而不是在新环境中重新执行 action。

## 6. Observation Schema

当前设计要求返回两路图像和机器人本体状态，但接口示例只包含图像字段。需要定义固定且版本化的 observation schema。

建议第一阶段至少支持：

```text
libero_standard_v1
libero_vision_only_v1
libero_full_state_v1
```

`libero_standard_v1` 建议包含：

| 字段 | shape | dtype | 说明 |
| --- | --- | --- | --- |
| `agentview_image` | `[H, W, 3]` | `uint8` | RGB, HWC |
| `robot0_eye_in_hand_image` | `[H, W, 3]` | `uint8` | RGB, HWC |
| `robot0_joint_pos` | `[N]` | `float32` | 关节位置 |
| `robot0_joint_vel` | `[N]` | `float32` | 关节速度 |
| `robot0_eef_pos` | `[3]` | `float32` | 末端位置 |
| `robot0_eef_quat_xyzw` | `[4]` | `float32` | 末端四元数，固定为 `xyzw` |
| `robot0_gripper_qpos` | `[M]` | `float32` | 夹爪位置 |

协议约束：

- 图像固定为 RGB，不使用 BGR。
- 图像固定为 HWC，不使用 CHW。
- 服务端不做上下翻转，除非 LIBERO 原始输出本身已是最终约定格式。
- 四元数顺序必须在字段名或 schema 中显式标出，推荐 `xyzw`。
- 状态值默认不归一化，保持 LIBERO / robosuite 原始物理量。
- 字段名称应尽量与原始 LIBERO observation key 对齐，但协议字段必须稳定。
- 第一阶段默认不返回 depth 和 segmentation；如支持，应通过 schema 或 observation subset 显式请求。
- 允许客户端选择相机和 observation 子集，但服务端必须在 session 创建响应中返回最终确认的 schema。

协议编解码层必须保留 dtype、shape、字节序和 C-contiguous 布局信息。

## 7. Action Schema

Action 维度不能在协议中固定写成 7，应从实际环境中读取并返回给客户端。

需要明确：

- action shape。
- action dtype，建议传输层接受 `float32`，服务端内部按环境需要转换。
- action low/high。
- action 是绝对控制还是增量控制。
- 平移和旋转所使用的坐标系。
- 旋转表示方式。
- gripper action 的语义，例如打开、关闭或连续控制。
- 一个 action 对应多少 MuJoCo control step。
- 是否存在 action repeat。
- 是否允许服务端自动裁剪越界 action。
- 如何处理 NaN、Inf 和非法 shape。
- 不同 task 是否具有完全相同的 action space。

建议规则：

- 服务端在 `POST /v1/sessions` 响应中返回实际 `action_space` 和 `action_schema_version`。
- shape 不匹配、NaN、Inf 直接返回 `INVALID_ACTION`，不得推进环境。
- 越界 action 第一阶段建议直接拒绝，而不是自动裁剪；如果未来允许裁剪，必须在响应 `info` 中显式记录。
- action 解码后应计算稳定 hash，用于 request id 幂等检查。

## 8. 本地环境和远程环境一致性验证

第一阶段需要证明，在相同条件下：

```text
task
init state
seed
action sequence
```

本地 LIBERO 环境与远程环境产生一致的状态转移。

建议分三层测试：

```text
协议编解码一致性
EnvironmentAdapter 一致性
独立本地与远程环境一致性
```

需要比较：

- observation keys。
- observation shape 和 dtype。
- observation 原始字节。
- reward。
- success。
- terminated 和 truncated。
- 机器人状态。
- 物体状态。
- 渲染图像。
- step index。

建议阈值：

- 同一个 observation 的协议编码和解码必须逐字节一致。
- 同进程同环境 adapter 包装前后的数值状态应逐元素一致或满足极小浮点误差。
- 独立本地与远程 MuJoCo 实例的状态向量可使用 `rtol` / `atol` 阈值，具体值需在固定依赖和硬件后测定。
- 渲染图像不能只比较任务成功率，应使用像素级指标，例如最大绝对误差、平均绝对误差和不一致像素比例。

一致性测试必须记录服务端代码 commit、LIBERO 版本、MuJoCo 版本、robosuite 版本、Python 版本、操作系统、GPU/驱动和 EGL 配置。

## 9. 环境创建失败和资源清理

环境创建涉及：

```text
读取 task 和 BDDL
创建 OffScreenRenderEnv
初始化 MuJoCo 和 EGL
reset
加载 init state
生成 observation
编码 observation
```

任何一步失败都可能遗留环境或渲染资源。需要保证以下情况都能正确释放资源：

- task id 非法。
- init state id 非法。
- BDDL 文件异常。
- MuJoCo 初始化失败。
- EGL 初始化失败。
- reset 失败。
- `set_init_state()` 失败。
- observation 生成失败。
- observation 编码失败。
- step 异常。
- 客户端主动关闭。
- session 超时。
- API 服务退出。
- EnvWorker 崩溃。

建议创建流程：

```text
SessionManager 创建 session 占位
-> 启动 EnvWorker
-> worker 创建 OffScreenRenderEnv
-> worker reset
-> worker set_init_state
-> worker 生成 initial observation
-> API 编码 observation
-> session 进入 READY
```

如果任意步骤失败：

- 调用 `env.close()`，如果 env 已经创建。
- 终止 EnvWorker。
- 删除未完成 session 或将其短暂标记为 `FAILED` 供查询。
- 返回稳定错误码。
- 不返回可用于 step 的 `session_id`。

只有完整初始化成功后，session 才能进入 `READY`。

## 10. 多个 Session 之间的状态隔离

即使第一阶段只计划支持一个活跃环境，也需要提前明确多 session 扩展时的状态隔离方式。

每个 `session_id` 必须绑定独立环境实例：

```text
session_A -> EnvWorker_A -> env_A
session_B -> EnvWorker_B -> env_B
session_C -> EnvWorker_C -> env_C
```

不同 session 不能共享同一个 `OffScreenRenderEnv`，否则一个 session 执行 action 后产生的机器人和物体状态变化会影响其他 session 的 observation。

不同 session 之间需要隔离：

- MuJoCo 仿真状态。
- 机器人和物体状态。
- episode 进度与 step index。
- 环境随机数状态。
- 扰动随机数状态。
- 请求幂等缓存。
- 渲染上下文。
- 异常状态。
- 资源回收状态。

当前阶段不需要引入用户身份，状态隔离的基本单位是：

```text
session_id
```

系统需要维护：

```text
session_id
-> worker_id
-> independent environment instance
```

即使第一阶段只运行一个 session，也不应将系统设计成全局唯一环境，否则后续支持多个 session 时，需要重新修改 SessionManager、环境生命周期和请求路由逻辑。

## Recommended Phase 1 Decision

建议第一阶段采用以下固定决策作为实现基线：

- 环境从第一阶段开始运行在独立 `EnvWorker` 进程中。
- `EnvWorker` 使用 `spawn` 启动，并在 worker 内初始化 MuJoCo、EGL 和 `OffScreenRenderEnv`。
- `POST /v1/sessions` 创建 session 并立即完成第一次 reset，返回 initial observation 和 `episode_id`。
- `POST /v1/sessions/{session_id}/reset` 在同一 session 中开启新 episode，并生成新 `episode_id`。
- 每个 step 必须携带 `episode_id`、`expected_step_index`、`request_id` 和 action。
- 同一 session 使用 session 级锁串行化 `step`、`reset` 和 `close`。
- observation 和 action 都使用版本化 schema，不在协议中硬编码 action 维度。
- worker step 超时或崩溃后，当前 episode 标记为 `FAILED`，不尝试在新环境中重放 action。
- 初始化失败时不产生可用 session，并确保 worker 和环境资源被清理。
- 第一阶段可以限制一个活跃 session，但内部数据结构仍按 `session_id -> worker_id -> env` 设计。
