# syntax=docker/dockerfile:1.4

FROM python:3.10-slim-bookworm AS builder

LABEL maintainer="UCagent Team"
LABEL description="NutShell Cache Verification Environment - Builder Stage"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/workspace/src

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ cmake \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-dev.txt /workspace/
COPY pyproject.toml /workspace/
COPY src/ /workspace/src/

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -e . -r requirements-dev.txt

FROM python:3.10-slim-bookworm AS runtime

LABEL maintainer="UCagent Team"
LABEL description="NutShell Cache Verification Environment - Runtime Stage"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/workspace/src:/workspace

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    verilator make \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . /workspace/

RUN chmod +x scripts/*.sh run_wsl_tests.sh 2>/dev/null; true

RUN verilator --version

RUN python -m pytest tests --ignore=tests/test_real_dut_smoke.py -q

CMD ["bash", "-lc", "python -m pytest tests --ignore=tests/test_real_dut_smoke.py -v && PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300"]
