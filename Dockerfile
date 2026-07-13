FROM python:3.14-slim-bookworm

LABEL maintainer="UCagent Team"
LABEL description="NutShell Cache Verification Environment - One-click Reproducible"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/workspace/src:/workspace

RUN apt-get update && apt-get install -y \
    verilator make gcc g++ cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace/

RUN python -m pip install --no-cache-dir -e . -r requirements-dev.txt

RUN chmod +x scripts/*.sh run_wsl_tests.sh 2>/dev/null; true

# Build Verilator coverage simulation
RUN verilator --version && \
    bash scripts/build_verilator_coverage.sh 2>&1 | tail -5

# The portable image validates the core and DUT contract. Native Picker DUT
# execution is intentionally reserved for the compatible self-hosted runner.
RUN python -m pytest tests --ignore=tests/test_real_dut_smoke.py -q

# Run verification
CMD ["bash", "-lc", "python -m pytest tests --ignore=tests/test_real_dut_smoke.py -v && PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300"]

