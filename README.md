# LIBERO-Pro2.0

LIBERO-Pro2.0 v1.0.0 以客户本地部署包的形式交付。用户在自己的 Ubuntu/NVIDIA 服务器上运行
LIBERO-PRO 环境服务，在自己的 Python 环境中安装轻量 SDK，并通过
`http://127.0.0.1:8000` 调用环境。服务端不固定 xVLA、Pi0 或任何其他模型；用户只需为自己的模型
实现合适的 observation/action adapter。

本地部署适合开发、私有评测和公开任务复现。由于部署者可以访问并修改本地环境，它不能天然作为
不可篡改的官方排行榜凭证。

## 下载

正式交付包位于本仓库的 [v1.0.0 Release](https://github.com/Zxy-MLlab/LIBERO-Pro2.0/releases/tag/v1.0.0)。
原始压缩包略大于 GitHub 单个 Release 资产的大小上限，因此发布为两个无损分片：

```text
libero-pro-bundle-1.0.0.tar.gz.part-000
libero-pro-bundle-1.0.0.tar.gz.part-001
libero-pro-bundle-1.0.0.tar.gz.parts.sha256
libero-pro-bundle-1.0.0.tar.gz.sha256
```

在 Ubuntu 服务器上下载全部四个文件后，先校验分片，再重组并校验原包：

```bash
sha256sum -c libero-pro-bundle-1.0.0.tar.gz.parts.sha256
cat \
  libero-pro-bundle-1.0.0.tar.gz.part-000 \
  libero-pro-bundle-1.0.0.tar.gz.part-001 \
  > libero-pro-bundle-1.0.0.tar.gz
sha256sum -c libero-pro-bundle-1.0.0.tar.gz.sha256
```

原始压缩包的 SHA-256 应为：

```text
e4badb922aab9a3d01faecb22f0c3c6f77f4eec1ef054efc1e4c63344517bfe2
```

不要使用仓库源码代替 Release 部署包。正式包已包含固定 Docker 镜像、SDK wheelhouse、任务、BDDL、
init states、扰动资产、安装脚本和版本清单。

## 主机要求

- Ubuntu 22.04 x86_64
- Docker Engine 和 Docker Compose v2
- NVIDIA 驱动和 NVIDIA Container Toolkit
- 推荐 16 核 CPU、32 GB 内存、8 GB 以上 GPU 显存、100 GB SSD 可用空间
- 用户模型环境使用 Linux x86_64 CPython 3.8-3.12

安装前检查：

```bash
docker version
docker compose version
nvidia-smi
docker run --rm --gpus all ubuntu:22.04 nvidia-smi
```

最后一条命令需要拉取测试镜像。如果目标服务器完全离线，可跳过该手工命令；`install.sh` 会使用交付包
中的正式镜像检查容器 GPU 能力。

## 安装

模型与 LIBERO-PRO 服务默认运行在同一台服务器。

```bash
tar -xzf libero-pro-bundle-1.0.0.tar.gz
cd libero-pro-bundle-1.0.0
bash install.sh
```

安装脚本会依次：

1. 检查 Docker、Compose、NVIDIA 驱动和 NVIDIA Container Toolkit。
2. 生成随机 API key 和结果签名密钥。
3. 校验包内 `SHA256SUMS`。
4. 加载固定的 `libero-pro-server:1.0.0` Docker 镜像。
5. 启动服务并等待 `/v1/health` 返回就绪。

服务默认只监听：

```text
http://127.0.0.1:8000
```

`client.env` 保存本地服务地址和明文 API key，权限为 `0600`。`.env` 保存服务端配置和 API key
哈希。不要共享、上传或提交 `.env`、`client*.env`、`runtime/scheduler.sqlite3`。

## 安装 Python SDK

在用户自己的模型 Python 环境中，从部署包离线安装：

```bash
python3 -m pip install --no-index \
  --find-links wheels \
  wheels/libero_remote-1.0.0-py3-none-any.whl

set -a
source client.env
set +a
```

SDK 不安装 LIBERO、MuJoCo 或 robosuite，也不包含模型依赖和模型权重。

## 首次验证

```bash
bash healthcheck.sh
python3 smoke_test.py
```

也可以查看不含凭据的运维接口：

```bash
curl http://127.0.0.1:8000/v1/health
curl http://127.0.0.1:8000/v1/version
```

`smoke_test.py` 会使用正式 Python SDK 完成一次真实的 `reset -> step -> result -> close`。只有
healthcheck 和 smoke test 都通过，才能认为 Docker、GPU/EGL、任务资产、SDK 和会话清理链路可用。

## 可用任务

v1.0.0 发布 169 个有效任务组合：

| Suite | Base | 适用扰动 | 合计 |
| --- | ---: | ---: | ---: |
| `libero_10` | 1 | 42 | 43 |
| `libero_goal` | 1 | 41 | 42 |
| `libero_object` | 1 | 41 | 42 |
| `libero_spatial` | 1 | 41 | 42 |

后三个 suite 已移除不适用的 D20。`GET /v1/tasks` 是有效 `suite + task_id + variant` 组合的唯一
来源，用户不能自行假设所有 base 任务都支持全部扰动。使用 SDK 查询任务：

```python
import os
import httpx

tasks = httpx.get(
    f"{os.environ['LIBERO_REMOTE_URL']}/v1/tasks",
    headers={
        "Authorization": f"Bearer {os.environ['LIBERO_REMOTE_API_KEY']}"
    },
    timeout=120.0,
).json()
```

请求 manifest 外的组合会返回 `INVALID_TASK`/404，不会启动其他任务。

## 接入自己的模型

直接使用 Gym 风格接口：

```python
import os
from libero_remote import RemoteLiberoEnv

with RemoteLiberoEnv(
    base_url=os.environ.get("LIBERO_REMOTE_URL", "http://127.0.0.1:8000"),
    api_key=os.environ["LIBERO_REMOTE_API_KEY"],
    timeout=120.0,
) as env:
    observation, info = env.reset(
        suite="libero_goal",
        task_id=9,
        init_state_id=0,
        seed=142,
        variant="S10",
    )

    terminated = truncated = False
    while not (terminated or truncated):
        action = model.predict(
            observation,
            instruction=info["language_instruction"],
        )
        observation, reward, terminated, truncated, info = env.step(action)

    result = env.result()
```

用户的 adapter 负责：

- 将标准 observation 转换为模型需要的图像、语言和 proprio 输入。
- 按模型 checkpoint 对应的流程完成 resize、归一化和 prompt 构造。
- 将模型输出转换成 `info["action_schema"]` 声明的 shape、范围和控制模式。
- 在每个 episode 开始时重置模型状态、action queue 和模型随机种子。

服务端只运行环境，不加载用户模型。Adapter 可以封装 PyTorch、JAX、TensorFlow、ONNX、私有推理
API、强化学习策略、规划器或人工控制。

## 固定复测

需要复现相同环境时，固定以下字段：

- `suite`、`task_id` 和 `variant`
- `init_state_id` 和环境 `seed`
- 相机名称、尺寸和控制模式
- 服务镜像、任务包和扰动包版本

服务端会记录任务、运行时、初态、初始 observation 和扰动计划指纹。失败重试会更换 attempt 和 lease，
但保持 episode spec 和环境侧指纹不变。

若要复现完整动作轨迹，用户还必须固定模型 checkpoint、processor、模型 seed、确定性算法，并确保模型
产生相同的 action 序列。

## 多账户和并发

单台客户服务器需要多个独立账户时：

```bash
bash add_account.sh team-b
docker compose up -d --force-recreate
```

脚本会生成 `client-team-b.env`。每个账户只能获得自己的客户端文件，不能共享 API key。Session、Run、
Lease、Result 和 Worker 均按账户隔离。

默认并发数应保持保守。只有在目标服务器上完成 1/2/4/8 个真实 EGL 环境压测后，才能提高 `.env` 中的：

```text
LIBERO_REMOTE_MAX_SESSIONS
LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER
```

## 运维

```bash
docker compose ps
docker compose logs --tail=200
docker compose stop
docker compose start
bash healthcheck.sh
```

升级或重新安装前，保留当前 `.env`、`client*.env` 和 `runtime/` 的安全备份。不要把包含凭据的备份上传到
GitHub、网盘公开链接或问题报告中。

## 网络边界

v1.0.0 的默认部署保持 `127.0.0.1:8000`，只允许同一台服务器上的客户端访问。这是当前推荐方式，
不需要修改端口映射。

只有模型与环境必须部署在不同内网机器时，才应配置内网监听，并先在防火墙中只允许指定模型服务器来源。
不要直接将明文 HTTP 8000 端口暴露到公网；跨公网必须使用 VPN 或 HTTPS 网关。

## 文档

- [客户本地部署技术方案](docs/customer-local-deployment-technical-plan.md)
- [用户端与服务器远程测试流程](docs/LIBERO-Pro2.0_用户端与服务器远程测试流程.md)
- [自定义模型 Adapter 方案](docs/LIBERO_PRO_Custom_Agent_Adapter_Solution.md)
- [远程评测可靠性与多用户并发方案](docs/LIBERO-Pro2.0_远程评测可靠性与多用户并发修复方案.md)

## 已知边界

- 第一版只支持 Linux x86_64 NVIDIA 主机。
- 本地结果适合开发和复现，不是不可篡改的官方排行榜成绩。
- 用户模型、checkpoint、processor 和模型显存均位于用户侧；服务不会上传这些内容。
- `127.0.0.1` 仅适用于模型进程和 LIBERO-PRO 服务位于同一主机的情况。若模型运行在另一个容器中，
  应将两个容器加入同一 Docker 网络并通过 Compose 服务名访问，而不是使用模型容器自己的 loopback。
