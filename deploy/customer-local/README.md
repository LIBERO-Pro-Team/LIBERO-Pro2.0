# LIBERO-PRO 2.0 客户本地部署包 v1.0.0

本包用于 Ubuntu 22.04 x86_64 NVIDIA 主机。服务、LIBERO、MuJoCo、robosuite、169 个已批准
BDDL、init state 和扰动资产均随 Docker 镜像交付；客户安装时不需要访问 GitHub，也不需要安装
模拟器 Python 依赖。客户模型运行在自己的环境中，只安装轻量 `libero_remote` wheel。

## 主机要求

- Docker Engine 与 Docker Compose v2
- NVIDIA 驱动与 NVIDIA Container Toolkit
- 推荐 16 CPU、32 GB 内存、8 GB GPU、100 GB SSD
- 第一版只支持 Linux x86_64；默认仅监听 `127.0.0.1:8000`

## 安装

```bash
tar -xzf libero-pro-bundle-1.0.0.tar.gz
cd libero-pro-bundle-1.0.0
bash install.sh
python3 -m pip install wheels/libero_remote-1.0.0-py3-none-any.whl
set -a && source client.env && set +a
python3 smoke_test.py
```

`configure.sh` 会生成随机 API key 和独立结果签名密钥，只保存 API key 的 SHA-256 到服务端 `.env`。
`install.sh` 还会在启动服务前验证 Docker 容器能够访问 NVIDIA GPU；这一步失败时，应先修复
NVIDIA Container Toolkit，不能跳过后继续测试。
不要共享 `.env`、`client.env` 或 runtime 数据库。若模型在另一台内网机器，修改 Compose 端口为
`0.0.0.0:8000:8000`，同时配置防火墙，仅允许指定内网源地址；不要直接暴露到公网。

新增独立账户：

```bash
bash add_account.sh team-b
docker compose up -d --force-recreate
```

脚本会生成 `client-team-b.env`。每个账户只获得自己的文件，不能共享 API key。若要让多个账户同时运行，
将 `.env` 中的 `LIBERO_REMOTE_MAX_SESSIONS` 设置为服务器能够承载的环境总数；
`LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` 则限制单个账户可占用的环境数。不要把总并发数设置得超过
GPU 显存和主机内存容量。

## 模型接入

```python
from libero_remote import RemoteLiberoEnv

env = RemoteLiberoEnv(
    base_url="http://127.0.0.1:8000",
    api_key="client.env 中的 LIBERO_REMOTE_API_KEY",
    timeout=120.0,
)
obs, info = env.reset(
    suite="libero_goal",
    task_id=0,
    init_state_id=0,
    seed=42,
    variant="S10",
)
terminated = truncated = False
while not (terminated or truncated):
    action = model.predict(obs, instruction=info["language_instruction"])
    obs, reward, terminated, truncated, info = env.step(action)
result = env.result()
env.close()
```

模型不限于 xVLA。用户可以直接使用 Gym 风格接口，也可实现 `AgentAdapter` 接入任意 PyTorch、JAX、
TensorFlow、ONNX、私有推理 API 或传统策略。服务端只验证标准 observation/action 和权威环境结果。

## 当前任务范围

- 4 个 suite：`libero_goal`、`libero_spatial`、`libero_object`、`libero_10`
- 每个 suite 1 个固定 base 任务
- `libero_10` 有 43 个有效 case；`libero_goal`、`libero_object`、`libero_spatial` 各有 42 个
- 三个 42-case suite 均移除了经验证不适用的 `D20`；发布 manifest 合计 169 个有效 BDDL
- `/v1/tasks` 是具体 suite/task/variant 可用组合的唯一来源，客户端不得自行假设笛卡尔积
- 支持固定 `init_state_id + seed`，并返回任务、初态、首帧和扰动计划指纹
- 支持 `relative` 与 `absolute` 7D action，具体 shape/range 以 `info["action_schema"]` 为准
- 支持直接 session 和持久化 run/lease 调度两种客户端方式

## 多用户与复测

每个账户必须使用不同 API key；使用 `add_account.sh` 配置多个账户。会话、run、lease 和结果按账户
隔离，并受单账户活动 session 配额限制。重复测试必须保持 BDDL、init state、环境 seed、相机参数、控制模式、模型
checkpoint、processor 和模型 seed 一致；服务端会核对五个环境侧指纹并记录 action hash chain。

## 本地部署的边界

本地包适合开发、私有评测和公开复现。客户可以修改本地镜像和评测逻辑，因此本地结果不能作为不可篡改
排行榜证明。服务不会上传客户模型、权重或 API key。
