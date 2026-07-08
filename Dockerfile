FROM ubuntu:22.04

LABEL maintainer="UCagent Team"
LABEL description="NutShell Cache Verification Environment - One-click Reproducible"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/workspace/src:/workspace
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    verilator make gcc g++ cmake \
    openjdk-11-jdk \
    git curl wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace/

RUN pip3 install --no-cache-dir pytest pytest-asyncio pyyaml

RUN chmod +x scripts/*.sh run_wsl_tests.sh 2>/dev/null; true

# Build Verilator coverage simulation
RUN verilator --version && \
    bash scripts/build_verilator_coverage.sh 2>&1 | tail -5

# Run verification
CMD ["bash", "run_wsl_tests.sh"]

