# LIBERO-Pro2.0 用户端与服务器远程测试流程

## 1. 平台组成

平台采用用户端模型推理、服务器端仿真渲染的结构：

```text
用户端 Windows
  -> WSL 中运行 VLA 模型
  -> SSH 隧道
  -> 服务器远程环境 API
  -> LIBERO 环境进程
  -> MuJoCo、BDDL 和相机渲染
```

- 用户端负责加载 VLA 模型，根据图像、机器人状态和语言指令生成动作。
- 服务器负责读取 BDDL、创建 LIBERO/MuJoCo 环境、执行动作并返回下一步 observation。
- 用户端不需要安装或运行服务器端的 MuJoCo 渲染环境。

## 2. 测试前准备

用户端需要准备：

- Windows、WSL 和可用的 NVIDIA GPU 环境。
- VLA 模型权重及模型对应的 Python 环境。
- LeRobot 源码和 LIBERO-Pro2.0 客户端代码。
- 可用于登录服务器的 SSH 凭据。

服务器需要准备：

- LIBERO-Pro2.0 服务端代码及 Python 环境。
- LIBERO、MuJoCo、robosuite 和离屏渲染依赖。
- 集中存放的 BDDL 和 init state 资产。
- 正在运行的 `libero-remote.service` 用户级服务。

正式测试前，用户端和服务器端应使用同一版本的远程评测协议。

## 3. 启动服务器

登录服务器：

```bash
ssh zhouxueyang@222.20.126.33
```

启动或重启服务：

```bash
systemctl --user restart libero-remote.service
systemctl --user status libero-remote.service --no-pager
```

服务默认监听服务器本机：

```text
127.0.0.1:8000
```

检查健康状态：

```bash
curl http://127.0.0.1:8000/v1/health
```

## 4. 连接用户端与服务器

用户端通过 SSH 本地转发访问服务器 API。推荐直接使用项目提供的 PowerShell 启动脚本，它会：

1. 检查 WSL 和模型客户端依赖。
2. 获取 WSL 可访问的 Windows 网关地址。
3. 检查已有隧道是否可用。
4. 在需要时建立到服务器 `127.0.0.1:8000` 的 SSH 隧道。
5. 启动 WSL 中的 Python runner。
6. 测试结束后清理由本次命令创建的隧道。

## 5. 运行 xVLA 测试

在 Windows PowerShell 中执行：

```powershell
Set-Location D:\LIBERO-Pro2.0\.claude-manager\worktrees\task-build-platform

.\scripts\Start-XvlaRemoteEval.ps1 `
  -Suite libero_goal `
  -TaskId 0 `
  -InitStateId 0 `
  -Episodes 1 `
  -Seed 42 `
  -MaxSteps 300
```

主要参数：

| 参数 | 作用 |
| --- | --- |
| `Suite` | 选择 LIBERO task suite |
| `TaskId` | 选择 suite 中的任务 |
| `InitStateId` | 选择任务初始状态 |
| `Episodes` | 设置测试 episode 数量 |
| `Seed` | 设置可复现随机种子 |
| `MaxSteps` | 设置单个 episode 最大步数 |

xVLA 使用绝对末端位姿控制。runner 会请求 `control_mode="absolute"`，服务器在环境中设置对应控制器模式。

## 6. 单个 Episode 的运行过程

一次完整测试按照以下顺序执行：

```text
用户端创建远程 session
  -> 服务器加载指定 BDDL 和 init state
  -> 服务器返回两路图像、机器人状态和语言指令
  -> 用户端 xVLA 生成 7 维 LIBERO action
  -> action 通过远程 API 发送到服务器
  -> 服务器执行 env.step(action)
  -> 服务器渲染并返回下一步 observation
  -> 重复推理和 step
  -> success、terminated 或 truncated
  -> 关闭 session 并释放环境资源
```

服务器在同一个 session 中持续维护 MuJoCo 状态，不会在每个 step 重新创建环境。

## 7. 数据内容

服务器返回的标准 observation 包含：

- `agentview_image`
- `robot0_eye_in_hand_image`
- `robot0_eef_pos`
- `robot0_eef_quat_xyzw`
- `robot0_gripper_qpos`
- 语言任务指令

用户端将 observation 转换为 LeRobot/xVLA 输入格式，并将模型输出转换为：

```text
末端位置 3 维 + axis-angle 旋转 3 维 + gripper 1 维
```

## 8. 测试结果

测试结果默认保存为：

```text
results/xvla_remote_eval.jsonl
```

每个 episode 对应一行 JSON，主要记录：

- suite、task ID、init state ID 和 seed
- session ID 和 episode ID
- 执行步数和累计 reward
- success、terminated 和 truncated
- episode 开始时间和总耗时

多 episode 测试会连续追加结果，便于后续统计成功率和性能指标。

## 9. 主要程序

| 程序 | 作用 |
| --- | --- |
| `scripts/Start-XvlaRemoteEval.ps1` | 建立连接并启动完整测试 |
| `scripts/run_xvla_remote_eval.py` | 加载模型、运行 episode、保存结果 |
| `libero_remote/runner/xvla.py` | observation 转换、模型推理和动作后处理 |
| `libero_remote/client/remote_env.py` | 远程环境的 reset、step 和 close 接口 |
| `libero_remote/server/session_manager.py` | 管理服务器 session、episode 和动作顺序 |
| `libero_remote/environment/libero.py` | 创建并控制服务器端 LIBERO/MuJoCo 环境 |
