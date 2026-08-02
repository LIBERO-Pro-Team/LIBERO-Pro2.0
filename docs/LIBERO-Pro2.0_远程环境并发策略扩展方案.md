# LIBERO-Pro2.0 远程环境并发策略扩展方案

> 历史设计背景。任务数量、鉴权、确定性重试和结果语义以 2026-08-02 的
> `LIBERO-Pro2.0_远程评测可靠性与多用户并发修复方案.md` 为准。

## 1. 前提

- 模型在用户端加载和推理，服务器不保存模型权重。
- 用户可以使用公开模型，也可以使用未发布的私有模型。
- 平台不固定 xVLA、Pi0 或任何模型；二者只可作为客户端参考 adapter。
- 服务器只负责 BDDL、LIBERO/MuJoCo 环境、离屏渲染、session 管理和结果记录。
- 用户通过统一的 `AgentAdapter` 将自己的模型接入平台。

## 2. 现有并发策略

当前 Phase 1 使用：

```text
max_sessions = 1
一个 session -> 一个 EnvWorker -> 一个独立 LIBERO 环境
```

同一 session 内的 `step`、`reset` 和 `close` 严格串行。第二个 session 请求在容量已满时返回 `503 SESSION_CAPACITY_REACHED`。

现有策略已经解决：

- 防止不同用户串用环境状态。
- 防止 `step/reset/close` 并发破坏环境。
- 通过 request ID 和 step index 防止 action 重复执行。
- 拒绝旧 episode、乱序 step 和非法 action。
- Worker 崩溃只影响所属 session。
- session 关闭或超时后能够回收资源。

现有策略的重点是保证一次远程测试正确，但还不能高效支持多用户和批量任务。

## 3. 现有策略还未解决的问题

- 同一时间只能有一个用户测试。
- 第二个用户只能收到 `503`，需要自行重试。
- 筛选后的 169 个有效任务组合没有统一的任务队列和断点续测。
- 一个用户可能长期占用服务器，缺少公平调度。
- 私有模型推理时间未知，服务器无法区分“仍在推理”和“已经断线”。
- session 容量固定，不能根据 CPU、内存、EGL 和网络负载调整。

## 4. 新并发策略

在现有 SessionManager 之上增加任务调度层：

```text
任意用户模型
    -> AgentAdapter
    -> 通用 Runner
    -> RunScheduler
    -> EnvWorker Slot
    -> 独立 LIBERO 环境
```

### 4.1 Episode 任务队列

将当前 169 个有效任务组合拆成 169 个独立 episode job：

```text
QUEUED -> LEASED -> RUNNING -> COMPLETED
                         -> FAILED / EXPIRED / CANCELLED
```

每个 job 对应一个新的 session 和 EnvWorker。失败任务可以单独重试，已完成任务不重复执行。

### 4.2 多环境 Slot

- 允许多个独立 session 同时渲染。
- 每个 session 继续使用独立 EnvWorker。
- 同一 session 仍然只允许一个在途 step。
- 初始可设置 `max_active_sessions = 4`，再通过 `1/2/4/8` 并发压测确定上限。
- 容量只根据服务器渲染所需的 CPU、内存、EGL 和网络资源决定，不考虑用户模型显存。

### 4.3 公平调度

采用“用户间轮询、用户内部 FIFO”：

```text
用户 A：A1 A2 A3
用户 B：B1 B2
执行顺序：A1 -> B1 -> A2 -> B2 -> A3
```

同时限制单用户活跃 session 数，防止一个批量测试占满所有环境 Slot。

### 4.4 Lease 与心跳

Runner 获得任务后同时获得 `lease_id`，模型推理期间定期发送心跳：

```text
heartbeat_interval = 15 秒
lease_grace_period = 60 秒
```

只要心跳正常，服务器就保留 session，不要求服务器了解模型类型或推理速度。心跳超时后关闭环境，并将该 episode 从 reset 开始重新排队。

### 4.5 用户 Adapter

平台只声明统一 Interface：

```python
class AgentAdapter:
    def reset(self, context): ...
    def act(self, observation): ...
    def close(self): ...
```

用户自行在 Adapter 中完成图像变换、状态映射、prompt、action 反归一化和限幅。服务器不需要模型 profile，也不接触私有模型代码和权重。

## 5. 新方案在现有基础上新增解决的问题

| 问题 | 新方案的解决方式 |
|---|---|
| 多用户同时测试 | 多个独立 EnvWorker Slot |
| 169 个任务批量执行 | 拆分为 episode job 队列 |
| 中断后继续测试 | 只重新调度未完成或失败任务 |
| 用户之间资源竞争 | 轮询队列和单用户配额 |
| 私有模型推理时间未知 | lease 心跳，不依赖模型 profile |
| 用户断网导致资源遗留 | lease 超时后自动回收并重新排队 |
| 固定容量利用率低 | 根据渲染资源压测结果调整 Slot 数 |
| 批量结果难以汇总 | 按 run、类别和 episode 统一记录 |

## 6. 两层职责

```text
现有 SessionManager：保证一次环境执行正确
新增 RunScheduler：安排多次环境执行如何排队、分配和恢复
```

现有的 Worker 隔离、step 幂等、顺序校验和资源回收机制全部保留。新方案只增加多 session 调度，不改变 observation、action 和用户 Adapter 的稳定 Interface。

## 7. 建议实施顺序

1. 增加 run、episode job、lease 和 heartbeat 数据结构。
2. 将固定 `max_sessions=1` 改为 EnvWorker Slot 管理。
3. 增加多用户公平队列和单用户配额。
4. 增加失败任务重新入队和断点续测。
5. 压测 2、4、8 个同时渲染的真实 session。
6. 根据 CPU、内存、EGL、网络和延迟确定正式容量。

该方案只扩展服务器的远程环境并发，不调度、不识别也不限制用户端模型。
