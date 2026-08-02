ARG BASE_IMAGE=ubuntu:20.04
FROM ${BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ARG LIBERO_PRO_REPOSITORY=https://github.com/Zxy-MLlab/LIBERO-PRO.git
ARG LIBERO_PRO_COMMIT=c02ee2c8255db1c36664fad978197c47e495f178
ARG LIBERO_PRO_SOURCE=remote
ARG LIBERO_REMOTE_COMMIT=unknown

LABEL org.opencontainers.image.title="LIBERO-PRO Remote Service" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.revision="${LIBERO_REMOTE_COMMIT}"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LIBERO_PRO_ROOT=/opt/libero-pro \
    LIBERO_PRO_COMMIT=${LIBERO_PRO_COMMIT} \
    LIBERO_REMOTE_COMMIT=${LIBERO_REMOTE_COMMIT} \
    LIBERO_REMOTE_TASK_MANIFEST=/opt/libero-remote/assets/task_manifest.json \
    LIBERO_REMOTE_BDDL_ROOT=/opt/libero-remote/assets/bddl/libero-pro2.0-169-v1 \
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

COPY simulator-source /tmp/libero-pro-source
RUN if [ "${LIBERO_PRO_SOURCE}" = "local" ]; then \
        test -f /tmp/libero-pro-source/setup.py \
        && cp -a /tmp/libero-pro-source "${LIBERO_PRO_ROOT}"; \
    else \
        rm -rf /tmp/libero-pro-source \
        && git clone "${LIBERO_PRO_REPOSITORY}" "${LIBERO_PRO_ROOT}" \
        && git -C "${LIBERO_PRO_ROOT}" checkout "${LIBERO_PRO_COMMIT}"; \
    fi \
    && python3.8 -m pip install \
        torch==1.11.0+cpu \
        --extra-index-url https://download.pytorch.org/whl/cpu \
    && python3.8 -m pip install -r "${LIBERO_PRO_ROOT}/requirements.txt" \
    && python3.8 -m pip install -e "${LIBERO_PRO_ROOT}"

WORKDIR /opt/libero-remote
COPY pyproject.toml README.md ./
COPY libero_remote ./libero_remote
COPY assets ./assets
RUN python3.8 -m pip install . \
    && mkdir -p "${LIBERO_CONFIG_PATH}" \
    && printf '%s\n' \
        "assets: ${LIBERO_PRO_ROOT}/libero/libero/assets" \
        "bddl_files: ${LIBERO_REMOTE_BDDL_ROOT}" \
        "benchmark_root: ${LIBERO_PRO_ROOT}/libero/libero" \
        "datasets: ${LIBERO_PRO_ROOT}/libero/datasets" \
        "init_states: ${LIBERO_PRO_ROOT}/libero/libero/init_files" \
        > "${LIBERO_CONFIG_PATH}/config.yaml"

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["python3.8", "-m", "libero_remote.server.healthcheck"]

CMD ["libero-remote-server"]
