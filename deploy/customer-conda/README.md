# LIBERO-PRO v1.0.0：普通 Conda 部署

这个目录是 Docker 交付之外的本地 Linux 运行方式。服务进程和模型客户端都由普通用户启动；日常运行不需要 root、sudo 或 Docker。NVIDIA 驱动、宿主机 EGL 驱动库和 Conda 本身属于主机前置条件，驱动首次安装可能需要管理员完成。

完整交付件发布在 GitHub release `v1.0.0-conda-r2`，文件名为
`libero-pro-conda-bundle-1.0.0.tar.gz`。`r2` 只表示同一 `1.0.0` 产品版本的发布修订，
不改变 bundle、Python 包或服务版本。下载 tar.gz 和同名 `.sha256` 后先校验摘要，再解压安装。

## 固定基线

本包的 Python 依赖来自已验收的 Docker `v1.0.0` 运行环境，详见 `requirements-lock.txt`：Python `3.8.10`、Torch `1.11.0+cpu`、MuJoCo `3.2.3`、robosuite `1.4.0`、FastAPI `0.103.2`、Uvicorn `0.23.2` 等均为精确版本。源码提交固定为：

- 服务：`a71b3e07dd7609daa1c108e813f25d0c42f83fdf`
- 模拟器：`c02ee2c8255db1c36664fad978197c47e495f178`
- Docker 参考镜像摘要（仅用于对照，不是 Conda 运行时镜像）：`sha256:969cdf6bc1a3a9f50ce5529bfd7aab6e746d53f9b3d03333bbe793636ba4f933`

`SOURCE_BASELINE.json`、`VERSION.json` 和两个 SHA-256 清单用于核对，不要替换 `service-source/` 或 `simulator-source/` 中的文件。

## 主机条件

- Ubuntu 20.04/22.04 x86_64，普通用户可写目标 Conda 前缀和本包目录。
- Conda 或 Miniconda/Miniforge，并能创建 Python 3.8 环境。
- NVIDIA 驱动可由当前用户执行 `nvidia-smi`。驱动必须提供 `libEGL_nvidia.so`；不要用 CPU OSMesa 结果替代 GPU/EGL 评测。
- 运行时不需要 Docker、Docker Compose、NVIDIA Container Toolkit 或 root 权限。

## 安装

从发布包解压后，在本目录执行：

```bash
conda --version
conda create -p /data/user/envs/libero-pro2 python=3.8.10
bash install.sh /data/user/envs/libero-pro2
```

`install.sh` 会使用 `environment.yml` 同步 Conda 的编译工具和 EGL 运行库，再使用 `requirements-lock.txt` 安装精确 Python 依赖，最后以 editable 方式安装两棵固定源码。也可以省略参数，默认使用 `$HOME/.conda/envs/libero-pro2`。安装脚本不会调用 sudo 或 Docker。

## 配置、启动与检查

首次配置会随机生成账户 key。服务端只保存 key 的 SHA-256，客户端明文 key 写入 `client.env`；两份文件均为 `0600`，不要提交或发送它们。

```bash
bash configure.sh /data/user/envs/libero-pro2
bash start.sh
bash status.sh
bash healthcheck.sh
/data/user/envs/libero-pro2/bin/python smoke_test.py
```

停止服务：

```bash
bash stop.sh
bash status.sh
```

`configure.sh` 默认只监听 `127.0.0.1:8000`。同机模型直接读取客户端配置：

```bash
set -a
source client.env
set +a
/data/user/envs/libero-pro2/bin/python your_model_client.py
```

跨机器测试时，在配置前显式设置服务监听地址和客户端 URL，并用防火墙只允许指定模型机来源；不要把明文 HTTP 8000 暴露到公网：

```bash
export LIBERO_REMOTE_HOST=0.0.0.0
export LIBERO_REMOTE_PORT=8000
export LIBERO_REMOTE_PUBLIC_URL=http://LIBERO_SERVER_LAN_IP:8000
bash configure.sh /data/user/envs/libero-pro2
```

多个账户并发测试时，在首次配置前设置总容量，然后为每个账户生成独立客户端文件。账户变更要求服务处于停止状态：

```bash
export LIBERO_REMOTE_MAX_SESSIONS=2
bash configure.sh /data/user/envs/libero-pro2
bash add_account.sh team-b
bash start.sh
```

`client.env` 与 `client-team-b.env` 必须分别交给对应用户，不能共享。服务内部仍按账户隔离 session、run、lease 和 result；单账户默认最多一个活动会话。

## 模型接入

服务端只提供环境 reset/step/result 接口，不加载模型权重。客户端可以实现自己的 `AgentAdapter`，也可以直接使用 `RemoteLiberoEnv`；xVLA、Pi0 或其他模型都不被服务固定。模型端应固定自己的推理随机源、processor 版本和动作序列，才能复现完整轨迹。

## 复测口径

`smoke_test.py` 使用已发布的 `libero_goal/task 9/BASE/init state 0/seed 142`，执行一次零动作，只验证服务链路，不代表模型任务成功。要得到逐字节一致的环境初态，复测必须保持相同 suite、task、variant、init state、seed、相机尺寸、控制模式和扰动计划；要得到相同完整轨迹，还必须保持模型、processor、模型 seed 和动作序列一致。失败重测应复用同一 episode spec，而不是重新随机选择任务或 seed。

## 运行文件

`runtime/` 保存 scheduler 数据库和 PID 元数据，`logs/` 保存服务日志。不要删除正在运行服务的数据库或 PID 文件；正常停止请使用 `bash stop.sh`。如需更换 key，先停止服务、备份并删除 `server.env`/`client.env`，再重新执行 `configure.sh`。

详细 EGL、MuJoCo 和宿主驱动检查见 [`EGL_HEADLESS.md`](EGL_HEADLESS.md)。
