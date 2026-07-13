---
name: picker-rtl-binding
description: Generates Python simulation bindings from NutShell Cache RTL using the Picker tool. Invoke when user needs to compile RTL to a Python-driven DUT module, fix Picker/SWIG build errors, inspect generated signal maps, or rebind to a real NutShell Cache DUT.
---

# Picker RTL Binding

Picker performs the "dimensional reduction" of RTL: it compiles NutShell Cache Verilog into a high-performance Python driver module, breaking the wall between HDL and a general-purpose language. This skill covers generating, inspecting, and debugging Picker bindings.

## When to Invoke

- Need to generate a Python DUT module from `rtl/NutShellCache.v` or `rtl/dut_gen/NutShellCache.v`
- Picker/SWIG/Verilator build fails or produces missing symbols
- Generated `signals.json` does not match expected CPU/Memory interface
- Need to rebind `ToffeeCacheAdapter` to a freshly generated DUT
- `tests/test_real_dut_smoke.py` fails on import or signal access
- Need to update `configs/signal_map.yaml` after a DUT regeneration

## Project Binding Layout

```
rtl/
├── NutShellCache.v                  # Source RTL (precompiled Verilog)
├── dut_gen/                         # Picker generation template + Makefile
│   ├── UT_NutShellCache/
│   │   ├── dut_base.hpp / dut_type.hpp / dut.i
│   │   ├── libDPINutShellCache.a / libUTNutShellCache.so
│   │   └── __init__.py
│   ├── NutShellCache.v / NutShellCache_top.sv
│   ├── dut_base.cpp / signals.json / pli.tab / filelist.f
│   └── mk/{python,cpp,golang,...}.mk
├── generated/                       # Mock/sim Python DUT package
│   ├── _UT_NutShellCache.so
│   ├── libUT_NutShellCache.py
│   └── example.py
└── generated_real/                  # Real NutShell DUT Python package
    ├── _UT_RealNutShellCache.so
    ├── libUTRealNutShellCache.py
    └── signals.json
```

## Standard Build Flow

1. Confirm RTL is present: `rtl/NutShellCache.v` (precompiled Verilog from NutShell Chisel).
2. Use the project's compile script (WSL2):
   ```bash
   cd /mnt/d/UCagent
   bash install_and_compile.sh        # or install_and_compile_cn.sh
   ```
3. The script invokes Picker → SWIG → produces `rtl/generated_real/_UT_RealNutShellCache.so` + `libUTRealNutShellCache.py`.
4. Inspect `rtl/generated_real/signals.json` to confirm port names; update `configs/signal_map_real.yaml` to match.
5. Smoke test:
   ```bash
   PYTHONPATH=src:. python -m pytest tests/test_real_dut_smoke.py -v --asyncio-mode=auto
   ```

## Signal Map Contract

`configs/signal_map.yaml` (and `signal_map_real.yaml`) maps logical names → physical DUT signals. Required fields consumed by `SignalMap` in `src/cache_vip/toffee_adapter.py`:

| Logical | Required | Notes |
| --- | --- | --- |
| `clock`, `reset` | yes | |
| `cpu_req_valid/ready/addr/wdata/wmask` | yes | |
| `cpu_req_write` OR `cpu_req_cmd` | one of | NutShell uses `cmd` encoding |
| `cpu_resp_valid/ready/rdata` | yes | |
| `cpu_req_size`, `cpu_resp_cmd`, `cpu_req_user` | optional | |
| `mem_req_*`, `mem_resp_*` | optional | memory-side |
| `mmio_req_*`, `mmio_resp_*` | optional | MMIO path |
| `coh_req_*`, `coh_resp_*` | optional | coherence |
| `flush`, `empty` | optional | |

## Common Build Failures & Fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ImportError: _UT_RealNutShellCache` | .so not built / wrong PYTHONPATH | Run `install_and_compile.sh`; set `PYTHONPATH=src:.` |
| SWIG wrap error on multi-dim port | Picker type inference | Declare width manually in `dut.i` / `dut_type.hpp` |
| `signals.json` missing a port | RTL port pruned by Verilator | Ensure port is driven/read in `NutShellCache_top.sv` |
| Signal width mismatch in adapter | Map points to wrong field | Cross-check `signals.json` width vs `SignalMap` |
| NutShell `cmd` vs boolean `write` | NutShell encodes op in `cmd` | Set `cpu_req_cmd` in map; adapter decodes |

## Hand-off to Toffee

Once the Python DUT imports cleanly and `signal_map_real.yaml` is consistent with `signals.json`, hand off to `toffee-env-builder` to wire `ToffeeCacheAdapter` and `MemoryAgent` around the generated DUT object.

## Reference

- Picker is part of the 万众一芯 (Wanzhongyixin) base toolchain documented at https://ucagent.open-verify.cc
- Real DUT adapter implementation: [src/cache_vip/real_dut_adapter.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/real_dut_adapter.py)
- Signal map loader: [src/cache_vip/toffee_adapter.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/toffee_adapter.py)
