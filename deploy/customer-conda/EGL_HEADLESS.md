# EGL / MuJoCo Headless Rendering Guide

## Required runtime variables

`configure.sh` writes these variables to `server.env`; keep them consistent when starting manually:

```bash
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
export LIBERO_PRO_ROOT=/path/to/libero-pro-conda-bundle-1.0.0/simulator-source
export LIBERO_CONFIG_PATH=/path/to/libero-pro-conda-bundle-1.0.0/runtime/libero-config
export LIBERO_REMOTE_TASK_MANIFEST=/path/to/libero-pro-conda-bundle-1.0.0/service-source/assets/task_manifest.json
export LIBERO_REMOTE_BDDL_ROOT=/path/to/libero-pro-conda-bundle-1.0.0/service-source/assets/bddl/libero-pro2.0-1680-v1
export CUDA_VISIBLE_DEVICES=0
export MUJOCO_EGL_DEVICE_ID=0
```

`CUDA_VISIBLE_DEVICES` and `MUJOCO_EGL_DEVICE_ID` are optional device selectors. On a multi-GPU host,
select an explicit device for each independent service instance. Do not combine `MUJOCO_GL=egl`
with `PYOPENGL_PLATFORM=osmesa` in the same instance.

## Host checks

As a regular user, first run:

```bash
nvidia-smi
ldconfig -p | grep -E 'libEGL_nvidia|libGLX_nvidia|libOpenGL'
/data/user/envs/libero-pro2/bin/python -c 'import mujoco; print(mujoco.__version__)'
```

If `nvidia-smi` is unavailable or `libEGL_nvidia.so` is absent from the dynamic linker path, ask an
administrator to repair the NVIDIA driver first. Do not work around this by installing another
model package or changing BDDL. Driver libraries normally come from NVIDIA drivers; Conda should
not copy the host's proprietary drivers.

## Conda libraries

`environment.yml` provides build and compatibility libraries: `cmake`, `make`, C/C++ compilers,
`pkg-config`, `libegl`, `libgl`, `libglvnd`, `libglib`, `mesalib`, `openmpi`, `xorg-libx11`, and
`xorg-libxext`. These packages satisfy user-environment ABI dependencies; the proprietary NVIDIA
EGL implementation still comes from the host driver.

## Docker v1.0.0 reference system versions

These system package versions come from the Ubuntu 20.04 Docker image used to pin Python
dependencies. They provide an auditable ABI baseline, not a requirement to install identical apt
version strings on Ubuntu 22.04. Use compatible distribution-provided versions on other Ubuntu releases.

| Component | Reference version |
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

## Troubleshooting

- `EGL_NOT_INITIALIZED`: check drivers, `libEGL_nvidia.so`, and `CUDA_VISIBLE_DEVICES`, then confirm `MUJOCO_GL` is `egl`.
- OSMesa-only operation supports CPU code smoke tests but does not establish successful GPU/EGL evaluation.
- When multiple user services share one GPU, give each service a separate port, runtime directory, Conda prefix, and `MUJOCO_EGL_DEVICE_ID`. Do not share `scheduler.sqlite3`.
- Missing write access to system directories is not a blocker if the user can write to their Conda prefix, bundle, runtime, and logs.
