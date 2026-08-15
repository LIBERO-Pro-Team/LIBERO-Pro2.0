# LIBERO-Pro2.0 远程评测可靠性与多用户并发修复方案

> **版本**：1.0  
> **日期**：2026-08-02  
> **状态**：协议与本机回归已实现；真实服务器容量与 MuJoCo/EGL 验收待最终部署执行

## 1. 范围与文档优先级

本文只规定 LIBERO-Pro2.0 远程评测方案的运行语义、数据模型和验收标准。GitHub 仓库是方案文档库，不是服务器部署包；服务器代码和部署目录是否出现在本仓库中，不属于方案缺陷。

当现有文档互相冲突时，按以下顺序解释：

1. 有明确版本号或更新时间时，以版本号更高或更新时间更晚的文档为准。
2. 同一提交且无法根据时间区分时，Session、Worker、并发和请求重放以 `LIBERO_PRO_Agent_SOP.md` 为准。
3. 具体参考模型的图像、proprio、坐标系和 action 适配以对应 adapter 的实测文档为准；这些结论不能写入通用服务端协议。
4. 多用户队列、Slot、Lease 和公平调度以本文为准。
5. 任务数量统一以版本化任务清单为准。当前有效集合为 1680 个任务组合，不再使用旧文档中的 320 个 BDDL 笛卡尔积。

## 2. 保留的基础设计

以下设计已经能够保证单个远程 Episode 的状态连续性，应继续保留：

- 一个 Session 始终绑定一个独立 `EnvWorker` 和一个 `OffScreenRenderEnv`。
- MuJoCo、EGL 和 OpenGL 只在 `spawn` 创建的 Worker 进程中初始化。
- 同一 Session 的 `reset`、`step` 和 `close` 严格串行，不同 Session 之间不共享环境对象。
- 每个 step 使用 `episode_id + expected_step_index + request_id + action_hash` 防止重复执行和乱序执行。
- Worker 超时或崩溃后当前 Episode 失败，禁止在新环境中继续旧 Episode 或重放不确定是否执行过的 action。
- 模型在用户侧运行，服务器只运行任务、仿真、扰动、渲染、调度和结果记录。
- 平台不固定 xVLA 或任何其他模型。用户通过 `AgentAdapter` 接入任意策略；xVLA、Pi0 仅是可选参考实现。
- `SessionManager` 负责一次环境执行的正确性；`RunScheduler` 负责多任务、多账户之间的排队、分配、恢复和结果汇总，两者职责不得混合。

## 3. 当前问题与解决方案

### 3.1 任务集合没有唯一事实来源

**问题**：旧并发方案按 suite 与扰动做笛卡尔积，仍描述为 320 个 BDDL。当前发布为 1680 个有效组合，D20 仍不属于本版本 active case。若 readiness、任务目录和批量调度分别生成任务，会重新暴露已删除组合或错误报告服务未就绪。

**解决方案**：发布版本化 `task_manifest.json`，逐项列出全部 1680 个有效 job。以下模块只能读取该清单，不得自行构造笛卡尔积：

- `/v1/health` readiness 检查；
- `/v1/tasks` 任务目录；
- Run 创建和 job 展开；
- BDDL、init state 和资产完整性校验；
- 批量进度和成功率统计。

每个条目至少包含：

```text
suite, base_task_id, perturbation_id, bddl_path, bddl_sha256,
init_state_set, task_version, max_steps, reset_stabilization_steps,
observation_schema_version, action_schema_version
```

服务启动时必须校验条目唯一、路径存在、hash 一致，并拒绝不在清单中的 suite/case 组合。

### 3.2 调度状态只存在于内存

**问题**：服务重启后，Run、job、重试次数、租约和完成结果会丢失，无法可靠断点续测。

**解决方案**：单机部署使用 SQLite WAL 模式持久化，未来需要多个 API 实例时使用 PostgreSQL。至少保存：

```text
accounts
runs
jobs
attempts
leases
results
```

领取任务、创建 attempt、占用 Slot 和发放 lease 必须在一个事务中完成；完成任务、写入权威结果和释放 Slot 也必须在一个事务中完成。进程重启后，未过期 lease 恢复为等待确认状态，已过期 lease 按错误分类决定是否重新排队。

### 3.3 多账户身份和资源隔离不足

**问题**：如果客户端可自行提交 `user_id`，就能读取、推进或关闭其他用户的 Session；仅隔离 MuJoCo 进程也不能保证任务目录、租约、结果和配额隔离。

**解决方案**：

- 每个账户使用独立 API key；服务端只保存 key 的强哈希。
- `account_id` 只能由认证中间件从 key 解析，业务请求不得接受客户端声明的账户身份。
- Session、Run、job、attempt、lease 和 result 全部带不可变 `account_id`。
- 读取、step、reset、heartbeat、complete、close 等操作必须同时匹配资源 ID 和所有者账户，否则统一返回不可枚举其他账户资源的错误。
- 每个 Session 使用独立 Worker、随机数状态、扰动状态、请求缓存和输出目录。
- 使用“账户间轮询、账户内 FIFO”，并限制单账户活跃 Session 数，防止一个账户占满全部 Slot。
- 日志包含内部 account ID，但不得记录明文 API key。

### 3.4 Lease 缺少防陈旧提交机制

**问题**：仅使用 `lease_id` 和心跳时，超时 Runner 可能在 job 已重新分配后恢复并提交 step 或结果。

**解决方案**：每次重新分配 job 时递增 `lease_generation`。以下请求必须携带 `lease_id + lease_generation`：

- heartbeat；
- Session 创建和 reset；
- step；
- job 完成或失败；
-结果提交。

服务端只接受当前 generation。旧 Runner 即使持有旧 lease ID，也必须收到 `STALE_LEASE`，不能推进环境、更新结果或延长租约。

心跳由 Runner 的独立后台线程发送，不能依赖同步模型推理循环。除 heartbeat interval 和 grace period 外，还必须设置单步最大推理时间、Episode 墙钟上限和 Lease 总寿命。

### 3.5 失败分类和重试语义不明确

**问题**：“失败任务重新排队”会把模型正常失败也当作系统故障重测，改变统计权重并浪费资源。

**解决方案**：失败至少分成：

| 类别 | 示例 | 自动重试 |
|---|---|---|
| `TASK_FAILURE` | Episode 正常结束但目标未完成 | 否 |
| `AGENT_TIMEOUT` | 模型超过单步或 Episode 时限 | 默认否 |
| `INVALID_ACTION` | shape、NaN/Inf、范围或 schema 错误 | 否 |
| `ENVIRONMENT_FAILURE` | BDDL、reset、EGL 或 MuJoCo 初始化失败 | 是，受最大次数限制 |
| `WORKER_FAILURE` | Worker 崩溃或 IPC 失效 | 是，受最大次数限制 |
| `LEASE_EXPIRED` | Runner 失联且心跳过期 | 是，受最大次数限制 |
| `USER_CANCELLED` | 用户取消 Run | 否 |

自动重试创建新的 attempt，但复用同一个不可变 job specification。达到 `max_attempts` 后转为终态，禁止无限重排。

### 3.6 复测和失败重测不够确定

**问题**：只记录一个 `seed` 不能复现环境。扰动随机采样、Python/NumPy RNG、init state、任务文件版本、环境依赖或客户端策略随机性任一变化，都可能产生不同初态或轨迹。

**解决方案**：Run 创建时将任务展开成不可变 `JobSpec`，并计算 `job_fingerprint`。至少固定并记录：

```text
manifest_version
suite + base_task_id + perturbation_id
bddl_sha256 + asset_manifest_sha256
init_state_id + init_state_sha256
environment_seed + perturbation_seed
python_seed + numpy_seed
task_version + perturbation_config
LIBERO/robosuite/MuJoCo/Python versions
observation/action schema versions
camera configuration + max_steps + reset stabilization steps
```

种子必须由稳定 job 身份和 repetition 编号通过固定算法派生，禁止根据队列顺序、领取时间或 attempt 编号派生。失败重试只增加 `attempt_id` 和 `lease_generation`，不能改变 `JobSpec`、任何 seed 或扰动计划。

动态扰动不得在重试时使用新的随机来源。第一次成功 reset 时从环境导出已解析的
`perturbation_plan`，其中包含触发窗口、目标对象、幅度/参数、资产和 `perturbation_seed`，并持久化其
规范化 JSON 与 SHA-256。运行期的确定性采样只能从该 seed 派生；对应 LIBERO-PRO 提交和运行时指纹也被锁定。

每次 reset 后，Worker 计算并返回：

```text
initial_state_fingerprint
initial_observation_fingerprint
perturbation_plan_fingerprint
job_fingerprint
runtime_fingerprint
```

同一 job 的所有 attempt 必须具有相同的五个指纹，否则在执行模型前以
`REPRODUCIBILITY_MISMATCH` 终止。固定部署基线要求首帧 observation 逐字节一致；MuJoCo 扁平数值状态
使用规范化 little-endian float64 字节计算 SHA-256。若最终硬件/驱动无法满足该约束，必须形成新 runtime
版本和独立基线，不能静默放宽同一 Run 的比较标准。

服务器能够保证环境初态和扰动计划一致。若要求整条轨迹也完全一致，客户端还必须固定 checkpoint、adapter、processor、PyTorch/CUDA RNG、确定性算法设置和 policy seed，并产生相同 action 序列。服务器记录逐步 `action_hash`，用于区分环境差异和模型非确定性。

### 3.7 结果不是服务器权威记录

**问题**：客户端 JSONL 可以遗漏、覆盖或篡改，不能作为多账户正式评测的唯一结果。

**解决方案**：服务器在 Episode 终态原子写入：

```text
account_id, run_id, job_id, attempt_id, lease_generation,
job_fingerprint, environment/version hashes, seed bundle,
initial_state_fingerprint, initial_observation_fingerprint,
perturbation_plan_fingerprint, action_chain_hash,
success, reward, steps, terminated, truncated, failure_class,
timings, created_at
```

写入后返回稳定 `result_receipt`；相同 attempt 的相同结果幂等返回相同 receipt，不同内容返回 `RESULT_CONFLICT`。客户端 JSONL 只是服务器结果的本地副本。

### 3.8 Observation 坐标语义与模型适配边界

**问题**：`libero_standard_v1` 返回 site-frame `robot0_eef_quat_xyzw`，而 xVLA 使用 controller-frame rotation matrix。直接转换会造成已验证的姿态错误和假低成功率。

**解决方案**：

- `libero_standard_v1` 保持 site-frame 四元数语义，避免静默改变已有协议。
- 需要 controller-frame 的模型由其用户端 Adapter 完成显式转换；例如 xVLA 参考 Adapter 使用已经实测的 site-to-controller 变换 `[-Y, X, Z]`。
- conformance test 提供固定四元数、期望 controller rotation matrix 和图像方向黄金样本。
- 若未来协议需要原生同时返回两种坐标表示，应新增 `libero_standard_v2`，字段名显式包含 frame，不能改变 v1 字段含义。
- 通用 runner 只校验 schema 和 action，不得根据模型名称选择预处理或控制模式。

### 3.9 终态资源和容量管理不足

**问题**：终态 Session 长期留在进程内 registry 会持续增长；静态 `max_active_sessions` 也无法反映真实 CPU、内存、EGL 和 GPU 占用。

**解决方案**：

- 终态审计数据写入数据库后立即关闭环境和 Worker。
- registry 中只保留有界 TTL/LRU 摘要，完整历史从持久化结果查询。
- Slot 数是部署配置，不写死在协议中。
- 以 `1/2/4/8` 个真实 Session 压测后确定容量，同时检查 GPU 显存、Worker RSS、CPU、文件描述符、EGL context、step 延迟和清理后资源回落。
- 调度层不把用户侧模型显存计入服务器环境 Slot，但用户 Runner 自身必须遵循一张模型 GPU 一个独立进程，禁止多个账户共享同一个有状态 AgentAdapter 实例。

## 4. 建议数据模型

```text
Account 1 --- N Run 1 --- N Job 1 --- N Attempt 1 --- 1 Lease
                                      |
                                      +--- 0..1 Result

Job -> immutable JobSpec -> job_fingerprint
Attempt -> lease_generation + execution status
Session -> account_id + attempt_id + EnvWorker
```

关键约束：

- `(run_id, job_key, repetition)` 唯一；
- `(job_id, attempt_number)` 唯一；
- 每个 job 同时最多一个有效 Lease；
- 每个 attempt 最多一个权威 Result；
- Session 的 `account_id` 必须等于 Run、Job、Attempt 和 Lease 的 `account_id`；
- Result 中保存的 fingerprint 必须等于 JobSpec fingerprint。

## 5. 推荐运行流程

```text
账户认证
  -> 创建 Run 并锁定 manifest 版本
  -> 展开 1680 个或用户选择的 JobSpec
  -> 账户间轮询领取 Job，事务创建 Attempt 和 Lease
  -> 创建独立 Session/EnvWorker
  -> reset 并校验初态、扰动计划和 job fingerprint
  -> 后台 heartbeat + 前台模型推理/step
  -> 服务器形成权威结果并返回 receipt
  -> 关闭 Worker、释放 Slot
  -> 基础设施失败时以原 JobSpec 创建新 Attempt
```

## 6. 验收标准

### 6.1 清单与服务就绪

- 清单恰好包含 1680 个唯一有效组合。
- `/v1/tasks` 不再发布三个已删除的 D20 组合。
- readiness 只校验清单内条目，不要求不存在的矩形组合。
- 所有 BDDL、init state、资产和 hash 校验通过。

### 6.2 账户隔离

使用账户 A 和 B 同时执行不同任务：

- 两者获得不同 Session、Worker、Run、Job、Lease 和输出记录。
- A 无法读取、step、heartbeat、complete 或 close B 的资源，反之亦然。
- A 的 reset、step、超时、取消和 Worker 崩溃不改变 B 的 step index、observation、结果或租约。
- 并发执行的结果与两个任务分别串行执行的结果一致。

### 6.3 幂等、租约和恢复

- 相同 step 请求重复发送只执行一次 action。
- 旧 `lease_generation` 的 heartbeat、step 和结果提交全部被拒绝。
- API 进程重启后，已完成结果仍存在，未完成任务可按规则恢复。
- 同一 attempt 重复提交相同结果返回同一 receipt，提交不同结果被拒绝。

### 6.4 确定性复测

对静态扰动和动态扰动各选代表任务，至少执行首次运行、手工复测、Worker 失败重测和服务重启后重测：

- 五个复现指纹与规范化扰动 plan 完全一致。
- reset 后 MuJoCo 数值状态相同；固定部署基线下 initial observation hash 相同。
- 输入同一 action sequence 时，每一步状态、reward、success 和终态一致。
- 更换 attempt、账户调度顺序或并发数量不能改变任务初态。

### 6.5 资源与并发

- 完成、失败、超时、取消和进程退出后均无遗留 EnvWorker。
- 资源占用在 Session 关闭后回落，无持续增长。
- 分别压测 1、2、4、8 个 Slot；只有满足内存、显存、EGL 和延迟阈值的最大值才能配置为正式容量。
- 单账户配额和账户间轮询在持续批量提交下仍能防止饥饿。

## 7. 实施顺序

1. 建立 1680 项版本化任务清单，统一 readiness、catalog 和批量展开逻辑。
2. 引入持久化 RunScheduler 和账户所有权校验。
3. 实现 lease generation、防陈旧写入、错误分类和最大重试次数。
4. 固化 JobSpec、全套 seed、动态扰动计划和初态指纹。
5. 改为服务器权威结果和稳定 receipt。
6. 补充 adapter conformance 黄金样本和坐标系验证。
7. 完成双账户并发隔离、故障恢复、确定性重测和容量压测后再开放多账户使用。

## 8. 当前验证边界

本机自动化测试覆盖任务清单、API key 账户隔离、双账户独立 Worker、轮询和单账户配额、step 幂等、
lease generation、防陈旧写入、结果持久化与 receipt、重试上限、服务重启恢复、三类环境指纹以及
任意用户 adapter 接口。xVLA 和 Pi0 只作为客户端参考实现，不进入服务端镜像或调度判断。

尚未在本机宣称完成的项目是最终公共服务器上的真实 LIBERO/MuJoCo/EGL 回归和 `1/2/4/8` Slot
资源压测。这些结果依赖最终 GPU、驱动、EGL 和容器运行时，只能在实际部署后验收。GitHub 中的代码和
文档不会自动发布到服务器。

上述顺序不能颠倒：如果没有不可变任务清单和持久化身份，先增加并发只会把错误任务、陈旧租约和不可复现结果放大。
