FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG LIBERO_PRO_REPOSITORY=https://github.com/Zxy-MLlab/LIBERO-PRO.git
ARG LIBERO_PRO_COMMIT=eafdb809426b13153aa1e4c42d6601844217dfec

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LIBERO_PRO_ROOT=/opt/libero-pro \
    LIBERO_CONFIG_PATH=/root/.libero \
    MUJOCO_GL=egl \
    PYOPENGL_PLATFORM=egl \
    LIBERO_REMOTE_HOST=0.0.0.0 \
    LIBERO_REMOTE_PORT=8000 \
    LIBERO_REMOTE_BACKEND=libero

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        ca-certificates \
        curl \
        libegl1 \
        libgl1 \
        libglib2.0-0 \
        libglvnd0 \
        libglx0 \
        libopenmpi-dev \
        libosmesa6 \
        libosmesa6-dev \
        libx11-6 \
        libxext6 \
        python3.8 \
        python3.8-dev \
    && curl -fsSL https://bootstrap.pypa.io/pip/3.8/get-pip.py -o /tmp/get-pip.py \
    && python3.8 /tmp/get-pip.py "pip<25" "setuptools<76" wheel \
    && rm -f /tmp/get-pip.py \
    && rm -rf /var/lib/apt/lists/*

RUN git clone "${LIBERO_PRO_REPOSITORY}" "${LIBERO_PRO_ROOT}" \
    && git -C "${LIBERO_PRO_ROOT}" checkout "${LIBERO_PRO_COMMIT}" \
    && python3.8 -m pip install \
        torch==1.11.0+cu113 \
        torchvision==0.12.0+cu113 \
        torchaudio==0.11.0 \
        --extra-index-url https://download.pytorch.org/whl/cu113 \
    && python3.8 -m pip install -r "${LIBERO_PRO_ROOT}/requirements.txt" \
    && python3.8 -m pip install -e "${LIBERO_PRO_ROOT}"

WORKDIR /opt/libero-remote
COPY pyproject.toml README.md ./
COPY libero_remote ./libero_remote
RUN python3.8 -m pip install . \
    && mkdir -p "${LIBERO_CONFIG_PATH}" \
    && printf '%s\n' \
        "assets: ${LIBERO_PRO_ROOT}/libero/libero/assets" \
        "bddl_files: ${LIBERO_PRO_ROOT}/libero/libero/bddl_files" \
        "benchmark_root: ${LIBERO_PRO_ROOT}/libero/libero" \
        "datasets: ${LIBERO_PRO_ROOT}/libero/datasets" \
        "init_states: ${LIBERO_PRO_ROOT}/libero/libero/init_files" \
        > "${LIBERO_CONFIG_PATH}/config.yaml"

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["python3.8", "-m", "libero_remote.server.healthcheck"]

CMD ["libero-remote-server"]
