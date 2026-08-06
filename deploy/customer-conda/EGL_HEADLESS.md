# EGL / MuJoCo 无头渲染指南

## 必须的运行变量

`configure.sh` 会把这些变量写入 `server.env`；手动启动时也必须保持一致：

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export LIBERO_PRO_ROOT=/path/to/libero-pro-conda-bundle-1.0.0/simulator-source
export LIBERO_CONFIG_PATH=/path/to/libero-pro-conda-bundle-1.0.0/runtime/libero-config
export LIBERO_REMOTE_TASK_MANIFEST=/path/to/libero-pro-conda-bundle-1.0.0/service-source/assets/task_manifest.json
export LIBERO_REMOTE_BDDL_ROOT=/path/to/libero-pro-conda-bundle-1.0.0/service-source/assets/bddl/libero-pro2.0-169-v1
export CUDA_VISIBLE_DEVICES=0
export MUJOCO_EGL_DEVICE_ID=0
```

`CUDA_VISIBLE_DEVICES` 和 `MUJOCO_EGL_DEVICE_ID` 是可选的设备选择项；多 GPU 主机应为每个独立服务实例选择明确的设备。不要在同一实例中混用 `MUJOCO_GL=egl` 与 `PYOPENGL_PLATFORM=osmesa`。

## 主机检查

普通用户先执行：

```bash
nvidia-smi
ldconfig -p | grep -E 'libEGL_nvidia|libGLX_nvidia|libOpenGL'
/data/user/envs/libero-pro2/bin/python -c 'import mujoco; print(mujoco.__version__)'
```

如果 `nvidia-smi` 不可用，或 `libEGL_nvidia.so` 不在动态链接器路径中，先让管理员修复 NVIDIA 驱动；不要通过安装另一个模型包或修改 BDDL 绕过该问题。驱动库通常由 NVIDIA 驱动提供，Conda 不应复制宿主专有驱动。

## Conda 侧库

`environment.yml` 提供编译和兼容库：`cmake`、`make`、C/C++ compiler、`pkg-config`、`libegl`、`libgl`、`libglvnd`、`libglib`、`mesalib`、`openmpi`、`xorg-libx11` 和 `xorg-libxext`。这些包解决用户环境的 ABI 依赖；NVIDIA 专有 EGL 实现仍来自宿主驱动。

## Docker v1.0.0 参考系统版本

下表是锁定 Python 依赖时所依据的 Ubuntu 20.04 Docker 镜像系统包版本。它是可审计的 ABI 基线，不表示 Ubuntu 22.04 必须安装完全相同的 apt 字符串；在不同 Ubuntu 小版本上应安装发行版提供的兼容版本。

| 组件 | 参考版本 |
| --- | --- |
| `libegl1` | `1.3.2-1~ubuntu0.20.04.2` |
| `libgl1` | `1.3.2-1~ubuntu0.20.04.2` |
| `libglib2.0-0` | `2.64.6-1~ubuntu20.04.9` |
| `libglvnd0` | `1.3.2-1~ubuntu0.20.04.2` |
| `libglx0` | `1.3.2-1~ubuntu0.20.04.2` |
| `libopenmpi-dev` | `4.0.3-0ubuntu1` |
| `libosmesa6` / `libosmesa6-dev` | `21.2.6-0ubuntu0.1~20.04.2` |
| `libx11-6` | `2:1.6.9-2ubuntu1.6` |
| `libxext6` | `2:1.3.4-0ubuntu1` |

## 常见故障边界

- `EGL_NOT_INITIALIZED`：先检查驱动、`libEGL_nvidia.so` 和 `CUDA_VISIBLE_DEVICES`，再检查 `MUJOCO_GL` 是否为 `egl`。
- 只能在 OSMesa 下运行：这可以用于 CPU 代码烟测，但不能宣称完成 GPU/EGL 评测。
- 多个普通用户服务使用同一 GPU：为每个服务设置独立端口、runtime 目录、Conda 前缀和 `MUJOCO_EGL_DEVICE_ID`，不要共享 `scheduler.sqlite3`。
- 服务器没有写系统目录权限不是阻塞项：只要用户能写自己的 Conda 前缀、bundle、runtime 和 logs，脚本即可运行。
