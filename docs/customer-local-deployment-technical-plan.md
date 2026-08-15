# LIBERO-PRO 客户本地部署技术方案

版本：1.0.0（2026-08-03）

本方案对应离线交付包 `libero-pro-bundle-1.0.0.tar.gz`。客户在自己的 Ubuntu/NVIDIA
主机运行 LIBERO-PRO 环境服务，在自己的模型环境中安装轻量 Python SDK。GitHub 不是客户部署来源；
客户安装和运行不需要 clone 仓库、Git LFS、PyPI 或外部部署服务器。

## 1. 部署边界

```text
任意客户模型或策略
  -> 用户端 AgentAdapter / RemoteLiberoEnv
  -> HTTP + MessagePack
  -> LIBERO-PRO Docker Service
  -> 独立 EnvWorker -> LIBERO / MuJoCo / 扰动运行时
```

- 模型、checkpoint、processor 和模型显存都位于用户端。
- 服务端不固定 xVLA、Pi0 或任何模型，也不加载模型权重。
- 服务端负责固定 BDDL、init state、环境 seed、扰动计划、成功判定和权威结果。
- 一个 Session 绑定一个独立 Worker 和一个独立 MuJoCo 环境；不同账户不共享环境对象。
- 客户本地结果适合开发、私有评测和公开复现，不是不可篡改的排行榜证明。

## 2. 交付内容

```text
libero-pro-bundle-1.0.0/
|-- images/libero-pro-server-1.0.0.tar
|-- wheels/                         # CPython 3.8-3.12 Linux x86_64 离线依赖闭包
|-- assets/                         # 1680 项 manifest、BDDL 与扰动资产
|-- docs/                           # 本方案、adapter 契约、调度和可靠性方案
|-- compose.yaml
|-- configure.sh
|-- add_account.sh
|-- install.sh
|-- healthcheck.sh
|-- smoke_test.py
|-- VERSION.json
|-- SHA256SUMS
|-- README.md
`-- LICENSE
```

Docker 镜像内固定 LIBERO-PRO、MuJoCo、robosuite、Python 和完整模型资产。客户主机只通过
NVIDIA Container Toolkit 注入驱动与 EGL 能力。交付目录不包含服务源码、明文凭据或模型权重。

## 3. 主机要求

- Ubuntu 22.04 x86_64
- Docker Engine 和 Docker Compose v2
- NVIDIA 驱动和 NVIDIA Container Toolkit
- 推荐 16 CPU、32 GB 内存、8 GB 以上 GPU、100 GB SSD
- 客户端 Python 3.8-3.12，Linux x86_64

安装脚本会同时检查宿主 `nvidia-smi` 和容器内 `nvidia-smi`。任一检查失败都会在服务启动前明确
退出，不能跳过后继续做 GPU/EGL 测试。

## 4. 离线安装

```bash
tar -xzf libero-pro-bundle-1.0.0.tar.gz
cd libero-pro-bundle-1.0.0
bash install.sh
python3 -m pip install --no-index --find-links wheels wheels/libero_remote-1.0.0-py3-none-any.whl
set -a && source client.env && set +a
python3 smoke_test.py
```

`install.sh` 会执行以下步骤：

1. 检查 Docker、Compose、NVIDIA 驱动和 Container Toolkit。
2. 调用 `configure.sh` 生成随机 API key 与结果签名密钥。
3. 校验 `SHA256SUMS`。
4. 从 `images/` 加载固定 Docker 镜像并记录实际 image ID。
5. 启动 Compose 服务并等待 `/v1/health` 就绪。

`.env` 只保存 API key 的 SHA-256；明文 key 位于权限为 0600 的 `client.env`。不得共享
`.env`、`client*.env` 或 `runtime/scheduler.sqlite3`。

## 5. 任务范围

当前发布 manifest 包含 1680 个有效任务组合：四个 suite 各有 10 个官方 base task，
每个 base task 包含 1 个 BASE、21 个静态扰动和 20 个动态扰动，共 420 项。

`GET /v1/tasks` 是有效 suite、task ID 与 variant 组合的唯一
事实来源；客户端不得自行构造 suite 与 case 的笛卡尔积。请求 manifest 外组合会稳定返回
`INVALID_TASK`/404，而不是启动错误任务。

## 6. 模型接入

直接使用 Gym 风格环境：

```python
from libero_remote import RemoteLiberoEnv

env = RemoteLiberoEnv(
    base_url="http://127.0.0.1:8000",
    api_key="client.env 中的 LIBERO_REMOTE_API_KEY",
    timeout=120.0,
)
obs, info = env.reset(
    suite="libero_goal",
    task_id=9,
    init_state_id=0,
    seed=142,
    variant="S10",
)
terminated = truncated = False
while not (terminated or truncated):
    action = model.predict(obs, instruction=info["language_instruction"])
    obs, reward, terminated, truncated, info = env.step(action)
result = env.result()
env.close()
```

批量评测使用模型无关的 `AgentAdapter`：

```python
class AgentAdapter:
    def reset(self, context):
        self.model.reset(seed=context.episode_spec["seed"])

    def act(self, observation):
        return self.model.predict(observation)

    def close(self):
        self.model.close()
```

Adapter 可以封装 PyTorch、JAX、TensorFlow、ONNX、私有推理 API、强化学习策略、规划器或人工
控制。用户端负责图像方向、resize、prompt、proprio 坐标映射、action 反归一化和模型随机性；服务端只
按 `action_schema` 校验动作，不按模型名称选择预处理。完整契约见 `docs/model-adapter-contract.md`。

## 7. 多账户并发

新增独立账户：

```bash
bash add_account.sh team-b
docker compose up -d --force-recreate
```

脚本生成 `client-team-b.env`。每个账户必须使用自己的 API key。Session、Run、Job、Lease、Result
和 Worker 都按账户隔离；账户 A 无法读取、推进或关闭账户 B 的资源。

`.env` 中的主要容量参数：

| 参数 | 作用 |
| --- | --- |
| `LIBERO_REMOTE_MAX_SESSIONS` | 全服务器同时存在的环境 Slot 总数 |
| `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` | 单账户可占用的 Slot 上限 |
| `LIBERO_REMOTE_WORKER_TIMEOUT_SECONDS` | 环境 Worker 操作超时 |
| `LIBERO_REMOTE_SESSION_IDLE_TIMEOUT_SECONDS` | 空闲 Session 回收时间 |

总 Slot 数必须在目标 GPU 服务器上按 1/2/4/8 个真实 EGL 环境压测后确定，不能仅根据 API 并发测试
直接设置。用户端每个 runner 应持有独立的有状态 adapter 实例。

## 8. 固定 seed、复测与失败重试

服务端固定并记录 BDDL、init state、环境 seed、相机、控制模式、扰动计划及运行时版本，并返回：

```text
job_fingerprint
runtime_fingerprint
initial_state_fingerprint
initial_observation_fingerprint
perturbation_plan_fingerprint
```

失败重试只增加 attempt 和 lease generation，不改变 episode spec、seed 或上述五个指纹。若指纹
不一致，任务会以 `REPRODUCIBILITY_MISMATCH` 终止。完整轨迹要完全相同，用户还必须固定 checkpoint、
processor、policy seed、确定性算法并产生相同 action 序列；服务端会记录 action hash chain。

## 9. 网络部署

默认 Compose 只监听 `127.0.0.1:8000`。模型在另一台客户内网机器时，可将端口映射改为
`0.0.0.0:8000:8000`，并同时配置防火墙或反向代理，只允许指定来源。不要直接把 8000 端口暴露到
公网，也不要在 URL、日志或命令历史中传递 API key。

## 10. 运维接口

| 接口 | 用途 |
| --- | --- |
| `GET /v1/health` | readiness、容量和调度状态 |
| `GET /v1/version` | 服务、协议、镜像和模拟器版本 |
| `GET /v1/tasks` | 1680 项有效任务目录 |
| `POST /v1/sessions` | 创建直接环境 Session |
| `POST /v1/sessions/{id}/reset` | 使用固定 init state 与 seed 重置 |
| `POST /v1/sessions/{id}/step` | 幂等提交动作 |
| `DELETE /v1/sessions/{id}` | 关闭环境并释放 Worker |
| `GET /v1/results/{id}` | 查询服务端权威结果 |

批量 Run/Lease 接口由 `RemoteRunClient` 封装，说明见 `docs/remote-run-scheduler.md`。多账户、Lease、
失败分类和确定性约束见 `docs/LIBERO-Pro2.0_远程评测可靠性与多用户并发修复方案.md`。

## 11. 已验证与部署后验收

1.0.0 离线产物已验证：

- 528 项内部 SHA-256 与外层 tar.gz SHA-256 全部匹配。
- 镜像内 1680 个 BDDL 哈希全部匹配，完整包含资产与 init states。
- CPython 3.8 和 3.12 可在无网络、无索引模式安装正式 SDK wheelhouse。
- fake backend 下认证、非法任务 404、双账户隔离、同 seed 初态复现、跨账户结果隐藏、通用 adapter、
  签名结果和失败重试指纹一致均通过。
- CPU OSMesa 下真实 LIBERO 的 base、S10 静态扰动和 D01 动态扰动均可 reset 并 step。

客户目标服务器仍必须完成 NVIDIA GPU/EGL 验收：

1. 执行 `bash install.sh` 并确认容器内 `nvidia-smi` 成功。
2. 对 base、至少一个静态扰动和一个动态扰动执行真实 reset/step。
3. 依次压测 1/2/4/8 个环境，记录 GPU 显存、主存、step 延迟和关闭后的资源回落。
4. 只有通过压力测试的最大值才能写入 `LIBERO_REMOTE_MAX_SESSIONS`。

本地 OSMesa 通过不等同于客户 NVIDIA/EGL 和最终容量通过；这两项必须在实际部署硬件上验收。
