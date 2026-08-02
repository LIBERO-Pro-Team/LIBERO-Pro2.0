# LIBERO-PRO 远程环境服务：Agent 研发与接入规范（SOP）

> **状态**：Phase 1、协议 `1.0` 的规范基线。本文固化
> `docs/remote-env-session-open-issues.md` 的最终决策；若 README 中的 session、worker、
> 并发或重放描述与本文冲突，以本文为准。本文只记录稳定约束，不记录易变化的部署状态。
>
> **核心原则**：`session_id` 始终绑定唯一环境实例；客户端只通过 `reset()`、`step()`、
> `close()` 推进环境。任何请求都不得重复执行 action，也不得意外重建或串用环境状态。

## 1. 环境进程

- `OffScreenRenderEnv` 及 MuJoCo/EGL/OpenGL 上下文只能在独立 `EnvWorker` 中创建、reset、step 和 close。
- Worker 必须使用 `spawn`，禁止 `fork` 继承已初始化或不安全的 CUDA/EGL/MuJoCo 状态。
- FastAPI 进程只保存 session 元数据、worker 句柄和幂等缓存；不得持有 MuJoCo 环境对象。
- 一个 session 的全部环境操作只能发往同一 worker。单个 worker 崩溃不得拖垮 API 主进程。
- worker 命令超时后不能假设底层操作已停止：必须终止 worker，并把 session 标记为 `FAILED`。
- 使用进程内 session registry 时，Uvicorn 必须保持单 API 进程，不得配置多个 Uvicorn worker。

## 2. Session、Episode 与 Reset

- Session 是环境资源生命周期；Episode 是 Session 中的一次任务执行。
- `POST /v1/sessions` 启动 worker、创建环境并完成首次 reset。只有 initial observation 编码成功后才能进入 `READY`，并返回 `session_id`、`episode_id`、observation 及两个 schema。
- 后续 `POST /v1/sessions/{id}/reset` 复用同一环境，生成新 `episode_id`，将 step index 归零；旧 episode 的 step 返回 `STALE_EPISODE`。
- Phase 1 中 suite、task、相机、schema 和 max steps 在 session 内固定；reset 只允许更新 `init_state_id` 和 `seed`。
- Episode 终止后环境继续保留，直到 reset、显式 close、idle timeout、worker 失败或 API 退出。

```text
CREATING -> READY <-> STEPPING
READY/STEPPING -> TERMINATED | TRUNCATED
TERMINATED/TRUNCATED -> READY(reset) | CLOSED
任意可用状态 -> EXPIRED | FAILED | CLOSED
```

## 3. 环境状态连续性

- 唯一映射为 `session_id -> EnvWorker -> OffScreenRenderEnv -> 当前 MuJoCo 状态`。
- 禁止在每次 step 时重建环境；关节、夹爪、物体、`qpos/qvel`、仿真时间、随机数、step index 和扰动状态都保存在服务端同一实例中。
- 客户端只保存 observation 和协议标识，不承担 MuJoCo 状态保存或恢复。

## 4. 操作顺序与并发

- 每个 session 使用独立锁串行化 `step`、`reset` 和 `close`；锁覆盖完整 worker 调用和服务端状态提交边界。
- 合法顺序为 `create/reset -> step 0..N -> terminated/truncated -> reset 或 close`。
- reset、close 与在途 step 竞争时必须等待同一把锁；异常路径必须释放锁，close 必须幂等。
- `GET /v1/sessions/{id}` 只能返回最后一次已提交状态；不得暴露半更新结果。
- 不同 session 不使用全局环境锁；容量限制由 SessionManager 单独执行。

## 5. Step 幂等与防重放

每个 step 必须携带 `episode_id`、`expected_step_index`、`request_id` 和 action。校验顺序如下：

1. episode 不匹配：`STALE_EPISODE`。
2. 相同 request ID 且 episode、expected index、action hash 全部相同：返回缓存结果，不推进环境。
3. 相同 request ID 但 expected index 或 action 不同：`REQUEST_ID_CONFLICT`。
4. expected index 过小：`DUPLICATE_OR_EXPIRED_STEP`；过大：`OUT_OF_ORDER_STEP`。
5. Episode 已结束：`EPISODE_NOT_ACTIVE`；action 非法：`INVALID_ACTION`，均不得推进环境。
6. worker 在执行期间超时或崩溃：session 进入 `FAILED`，不得在新环境中重放 action。

- 缓存至少保存 episode、expected index、request ID、解码后 action 的稳定 hash、响应或稳定错误及产生时间。
- 缓存按 episode 隔离、容量有界，并在 reset 时清空；客户端不得使用新 request ID 盲目重试超时 step。

## 6. Observation Schema

- Phase 1 只支持 `libero_standard_v1`。默认字段为两路 `uint8` RGB/HWC 图像，以及
  `robot0_joint_pos`、`robot0_joint_vel`、`robot0_eef_pos`、`robot0_eef_quat_xyzw`、
  `robot0_gripper_qpos`；数值状态在协议中统一为 `float32` 原始物理量，不归一化。
- 四元数固定为 `xyzw`。服务端不额外转置、翻转、归一化或改变颜色空间。
- Phase 1 默认不返回 depth 或 segmentation；最终相机列表和字段必须在创建响应的 schema 中确认。
- 控制请求使用 JSON；包含 observation 的响应使用 `application/x-msgpack`。
- 每个数组必须携带 dtype、shape、字节序和 C-contiguous layout；只传输白名单字段和受控标量 info。

## 7. Action Schema

- 使用版本化 `libero_action_v1`，从实际环境返回 shape、`float32` dtype 和 low/high，禁止硬编码 7 维。
- Schema 必须明确 controller、增量/绝对模式、平移与旋转坐标系、旋转表示、gripper 语义、control frequency 和 action repeat；这些值在 session 内不可变。
- Phase 1 绑定固定版本 LIBERO/robosuite 的默认 `OSC_POSE` 契约；服务端不得擅自改变 action 语义，任一上述语义变化都必须升级 schema 版本。
- action shape 不匹配、含 NaN/Inf 或越界时返回 `INVALID_ACTION`；Phase 1 禁止自动裁剪，且不得执行 `env.step()`。
- action hash 基于服务端解码后的 C-contiguous `float32` 字节计算，而不是原始 JSON 文本。

## 8. 本地与远程一致性验收

固定 task、init state、seed 和 action sequence，执行三层验证：

1. 协议层：同一 observation 经 MessagePack 往返后，键、dtype、shape 和原始字节完全一致。
2. Adapter 层：包装前后数值状态逐元素一致或满足预先声明的极小浮点误差。
3. 独立环境层：本地与远程的 reward、success、terminated/truncated、step index 和状态向量满足约定 `rtol/atol`；图像记录最大/平均绝对误差和不一致像素比例。

- 测试报告必须记录服务代码 commit、LIBERO、MuJoCo、robosuite、Python、OS、GPU、驱动和 EGL 配置。
- `/v1/health` 只证明进程和数据就绪；真实渲染必须通过 `health -> create/reset -> step -> close` smoke test。

## 9. 失败处理与资源回收

- task/BDDL/init state、MuJoCo/EGL、reset、set init state、observation 生成或编码任一步失败，都必须关闭已创建环境、终止 worker、删除占位 session，且不得返回可用 session ID。
- step 异常或超时使 worker 不可恢复：终止 worker 并标记 `FAILED`；不得自动创建新环境继续旧 episode。
- 显式 DELETE、客户端上下文退出和 API shutdown 必须 close；客户端网络连接消失本身不等于 session 结束，失联由 idle timeout 回收。
- close、timeout cleanup 和 shutdown cleanup 都必须幂等；正常结束、异常、超时均不得遗留环境进程或持续增长的 CPU/GPU 资源。

## 10. Session 隔离与 Phase 1 边界

- 每个 session 独立拥有 MuJoCo 状态、机器人/物体状态、随机数、episode 进度、幂等缓存、渲染上下文、异常状态和清理状态。
- 映射始终保持 `session_id -> worker_id -> independent environment`；禁止共享全局 `OffScreenRenderEnv`。
- Phase 1 可限制一个活跃 session；容量耗尽返回稳定的 `503`，但内部结构不得设计成全局单例。
- Phase 1 只支持 `variant="base"` 以及 `libero_goal`、`libero_spatial`、`libero_object`、`libero_10`。
- Phase 1 没有公网鉴权、配额或多用户调度，服务不得直接暴露公网；只能放在可信内网、VPN 或 SSH 隧道之后。
