# LIBERO-PRO 客户本地部署技术方案

版本：v1.0

适用场景：客户下载 LIBERO-PRO 部署包，在自己的服务器上运行环境服务，并通过 Python SDK 调用。

## 一、总体方案

最合理的部署方式是：

将完整的 LIBERO Service 封装为 Docker 部署包，将环境调用接口封装为轻量级 Python SDK。

不建议把 LIBERO、MuJoCo、robosuite 和客户的模型强行安装到同一个 Python 环境中。这些组件对 Python、CUDA、OpenGL/EGL 和其他依赖的版本要求较多，容易与客户模型环境产生冲突。

整体结构如下：

```text
客户模型程序
    |
    | Python SDK 调用
    v
libero_remote.RemoteLiberoEnv
    |
    | HTTP 请求
    v
LIBERO-PRO Docker Service
    |
    |-- LIBERO
    |-- MuJoCo
    |-- robosuite
    |-- 任务资源
    `-- 扰动配置
```

服务实际运行在客户自己的机器上，因此：

- 模型与服务在同一台机器时，使用 `127.0.0.1` 访问。
- 模型与服务在不同机器时，使用客户内网 IP 访问。
- 客户不需要连接我方服务器。
- 客户机器不需要具备公网入口。

## 二、交付包结构

建议交付包采用以下结构：

```text
libero-pro-bundle-v1.0.0/
|-- images/
|   `-- libero-pro-server-v1.0.0.tar
|-- wheels/
|   `-- libero_remote-1.0.0-py3-none-any.whl
|-- assets/
|   |-- tasks/
|   |-- bddl/
|   |-- init_states/
|   `-- perturbations/
|-- docker-compose.yml
|-- .env.example
|-- install.sh
|-- healthcheck.sh
|-- SHA256SUMS
|-- README.md
`-- LICENSE
```

各部分作用如下：

| 内容 | 作用 |
| --- | --- |
| Docker 镜像 | 完整运行 LIBERO、MuJoCo 和环境服务 |
| Python wheel | 提供 `RemoteLiberoEnv` 客户端接口 |
| Docker Compose | 配置 GPU、端口、并发数、资源目录和日志目录 |
| Assets | 保存任务、BDDL、初始状态和扰动配置 |
| 安装脚本 | 检查环境、加载镜像并启动服务 |
| 健康检查脚本 | 检查服务是否能够正常访问 |
| SHA256SUMS | 验证交付文件是否完整 |
| README | 提供部署、使用和故障排查说明 |

任务资源可以直接放入 Docker 镜像，也可以作为独立目录挂载。建议采用独立挂载方式，便于后续单独更新任务和扰动配置。

## 三、客户机器要求

第一版建议只支持 Linux，避免同时维护 Windows、macOS 和不同图形渲染环境。

推荐要求如下：

- 操作系统：Ubuntu 22.04，x86_64
- 容器环境：Docker + Docker Compose
- GPU 驱动：NVIDIA Driver
- GPU 容器支持：NVIDIA Container Toolkit
- CPU：8 核以上
- 内存：16-32 GB
- GPU：NVIDIA GPU，4 GB 以上显存
- 磁盘：50 GB 以上可用空间

推荐配置为：

- CPU：16 核
- 内存：32 GB
- GPU：8 GB 以上显存
- 磁盘：100 GB 以上 SSD

客户不需要单独安装指定版本的 Python、MuJoCo、robosuite 或 LIBERO，这些依赖均固定在 Docker 容器内部。

## 四、Docker Compose 配置

建议提供可直接启动的 `docker-compose.yml`：

```yaml
services:
  libero-service:
    image: libero-pro-server:1.0.0
    container_name: libero-pro-service
    restart: unless-stopped
    gpus: all
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      MUJOCO_GL: egl
      NVIDIA_VISIBLE_DEVICES: "${GPU_ID:-all}"
      LIBERO_MAX_SESSIONS: "${MAX_SESSIONS:-1}"
      LIBERO_API_TOKEN: "${API_TOKEN}"
    volumes:
      - ./assets:/opt/libero/assets:ro
      - ./logs:/opt/libero/logs
    shm_size: "2gb"
```

同时提供 `.env.example`：

```env
GPU_ID=7
MAX_SESSIONS=1
API_TOKEN=replace-with-random-token
```

客户复制该文件并根据自己的机器修改 GPU、并发数和访问令牌。

## 五、客户安装流程

1. 解压部署包

```bash
tar -xzf libero-pro-bundle-v1.0.0.tar.gz
cd libero-pro-bundle-v1.0.0
```

2. 校验交付文件

```bash
sha256sum -c SHA256SUMS
```

3. 加载服务镜像

```bash
docker load -i images/libero-pro-server-v1.0.0.tar
```

4. 配置运行参数

```bash
cp .env.example .env
```

客户需要在 `.env` 中设置使用的 GPU、最大并发环境数量和 API Token。

5. 启动服务

```bash
docker compose up -d
```

6. 检查服务

```bash
curl http://127.0.0.1:8000/v1/health
```

正常情况下应返回：

```json
{
  "status": "ok"
}
```

7. 安装 Python 客户端

客户在自己的模型环境中安装：

```bash
pip install wheels/libero_remote-1.0.0-py3-none-any.whl
```

Python 客户端只负责网络通信和数据转换，不应依赖 LIBERO、MuJoCo 或 robosuite。

## 六、客户模型调用示例

```python
from libero_remote import RemoteLiberoEnv

env = RemoteLiberoEnv(
    base_url="http://127.0.0.1:8000",
    api_key="replace-with-random-token",
    timeout=60.0,
)

obs, info = env.reset(
    suite="libero_goal",
    task_id=0,
    init_state_id=0,
    seed=42,
)

terminated = False
truncated = False

while not (terminated or truncated):
    action = model.predict(
        obs,
        instruction=info["language_instruction"],
    )

    obs, reward, terminated, truncated, info = env.step(action)

env.close()
```

客户端接口应尽量接近 Gym/Gymnasium 的使用方式，使客户可以直接将其接入现有模型评测代码。

## 七、模型和服务不在同一台机器

客户可能使用两台服务器：

```text
模型服务器 -> 客户内网 -> LIBERO 服务器
```

此时需要将 Docker 端口配置修改为：

```yaml
ports:
  - "0.0.0.0:8000:8000"
```

模型服务器通过 LIBERO 服务器的内网 IP 访问：

```python
env = RemoteLiberoEnv(
    base_url="http://192.168.1.20:8000",
    api_key="replace-with-random-token",
    timeout=60.0,
)
```

内网部署时必须：

- 设置 API Token。
- 配置服务器防火墙。
- 只允许指定的客户内网地址访问。
- 不要将 8000 端口直接暴露到公网。
- 如需跨公网使用，应通过 VPN、内网穿透平台或 HTTPS 网关访问。

## 八、下载和交付方式

建议同时提供在线安装和离线安装两种方式。

### 1. 在线安装

客户从镜像仓库下载：

```bash
docker pull your-registry/libero-pro-server:1.0.0
```

Python 客户端可以从私有 PyPI、对象存储或交付平台下载。

在线安装的优点是：

- 下载方便。
- 更新简单。
- 可以按版本管理。
- 不需要传输完整离线包。

### 2. 离线安装

向客户提供完整压缩包：

```text
libero-pro-bundle-v1.0.0.tar.gz
```

离线包中已经包含 Docker 镜像、Python wheel、任务资源和部署配置，适合无法访问镜像仓库或处于封闭网络中的客户。

## 九、版本管理要求

每个交付版本必须明确记录：

- 服务版本。
- Python SDK 版本。
- API 协议版本。
- Benchmark 版本。
- Docker 镜像 digest。
- LIBERO 代码 commit。
- 任务资源版本。
- 扰动配置版本。
- 更新内容。
- 已知问题。

禁止只发布 `latest` 版本。正式交付应固定为 `1.0.0`、`1.0.1` 等明确版本。

建议 `/v1/version` 返回：

```json
{
  "service_version": "1.0.0",
  "sdk_version": "1.0.0",
  "protocol_version": "1.0",
  "benchmark_version": "libero-pro-2.0",
  "image_digest": "sha256:...",
  "task_pack_version": "2026.07",
  "perturbation_version": "2026.07"
}
```

这样客户反馈问题时，可以准确确定其使用的环境和任务版本。

## 十、服务端接口

服务端建议至少提供以下接口：

```text
GET    /v1/health
GET    /v1/version
GET    /v1/tasks
POST   /v1/sessions
POST   /v1/sessions/{id}/reset
POST   /v1/sessions/{id}/step
DELETE /v1/sessions/{id}
GET    /v1/results/{id}
```

各接口作用如下：

| 接口 | 作用 |
| --- | --- |
| `/v1/health` | 检查服务是否正常 |
| `/v1/version` | 返回服务、协议、任务和扰动版本 |
| `/v1/tasks` | 查询可使用的任务列表 |
| `/v1/sessions` | 创建环境会话 |
| `/reset` | 重置任务和初始状态 |
| `/step` | 提交动作并获得下一步观测 |
| `DELETE /sessions/{id}` | 关闭会话并释放资源 |
| `/v1/results/{id}` | 获取或导出运行结果 |

服务端还应具备：

- 会话超时自动回收。
- 最大并发数量限制。
- 错误参数检查。
- API Token 验证。
- 请求日志和错误日志。
- 防止同一个动作请求被重复执行。

## 十一、任务与扰动资源

交付的 Assets 至少应包含：

- LIBERO 任务定义。
- BDDL 文件。
- 初始状态。
- 物体和场景资源。
- 静态扰动配置。
- 动态扰动配置。
- 扰动参数说明。
- 随机种子和复现说明。

对于每次运行，服务端应记录：

- 任务集。
- 任务编号。
- 初始状态编号。
- 随机种子。
- 服务版本。
- 任务资源版本。
- 扰动类型。
- 扰动参数。
- 运行结果。

这样才能保证客户能够复现实验结果。

## 十二、日志与结果

建议默认将日志和结果保存到：

```text
logs/
results/
```

运行结果可以包含：

- Episode 配置。
- 动作序列。
- 奖励。
- 成功或失败状态。
- 运行时长。
- 扰动配置。
- 可选的视频或观测轨迹。
- 错误信息。

服务端不得默认收集或上传客户的模型代码、模型权重、密钥和其他敏感数据。

## 十三、升级方式

建议升级时只替换发生变化的部分：

| 更新内容 | 更新方式 |
| --- | --- |
| 服务代码或依赖 | 更新 Docker 镜像 |
| Python 调用接口 | 更新 wheel |
| 任务和初始状态 | 更新 Assets |
| 扰动配置 | 更新扰动资源包 |
| 部署参数 | 更新 Compose 或 `.env.example` |

升级前应保留旧版本镜像和配置，以便出现问题时能够快速回退。

## 十四、需要注意的限制

客户自己部署后，可以：

- 查看任务和扰动配置。
- 修改环境代码。
- 修改成功判定。
- 针对测试任务训练。
- 修改或伪造本地评测结果。

因此，本地部署产生的成绩无法天然证明环境未被修改。

建议区分两类服务：

| 版本 | 用途 |
| --- | --- |
| 客户本地部署版 | 开发、调试、私有评估和公开任务复现 |
| 我方公网官方版 | 隐藏任务、论文主榜和官方排行榜 |

正式排行榜或权威评测仍应通过我方控制的远程服务完成，客户不能接触隐藏任务、评测逻辑和完整测试资源。

## 十五、最终交付路线

最终建议交付：

Docker 服务镜像 + Python 客户端 SDK + 任务资源包 + Docker Compose 配置 + 安装与健康检查脚本。

其中：

- Docker 容器负责完整运行 LIBERO-PRO。
- Python SDK 负责为客户提供简单、统一的调用接口。
- 客户可以在本机或内网中使用。
- 本地成绩用于开发和自测。
- 正式成绩由我方远程评测服务产生。
