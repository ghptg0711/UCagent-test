---
name: toffee-env-builder
description: Builds a structured, reusable Toffee verification environment around the NutShell Cache DUT. Invoke when user wires the DUT adapter, drives clock/reset/requests, samples responses, integrates the memory agent, or refactors UCAgent-generated fragments into the Toffee framework.
---

# Toffee Environment Builder

Toffee is UCAgent's framework for building modern, reusable, maintainable verification environments — analogous to agile software test harnesses. This skill covers assembling the DUT integration layer and protocol adapter layer so that the DUT-independent verification core stays decoupled from concrete signals.

## When to Invoke

- Wire `ToffeeCacheAdapter` to a Picker-generated DUT object
- Drive clock/reset and CPU-side request handshake (valid/ready)
- Sample CPU-side response and translate to `CacheResponse`
- Integrate `MemoryAgent` / `ScriptedMemoryAgent` for fill + writeback + latency + backpressure
- Refactor UCAgent-generated code fragments into the structured Toffee layer
- Diagnose protocol translation bugs (cmd encoding, mask mapping, ordering)

## Layered Contract (must preserve)

```
┌─────────────────────────────────────────────┐
│ Verification Core (DUT-independent)         │  src/cache_vip/{generator,reference_model,
│  CacheTxn / CacheResponse / Coverage / ...  │   scoreboard,coverage,faults,regression}.py
├─────────────────────────────────────────────┤
│ Protocol Adapter (translates signals)       │  src/cache_vip/transactions.py
├─────────────────────────────────────────────┤
│ DUT Integration (Toffee + Picker)           │  src/cache_vip/toffee_adapter.py
│                                              │  src/cache_vip/real_dut_adapter.py
│                                              │  configs/signal_map*.yaml
└─────────────────────────────────────────────┘
```

**Rule**: All signal names live ONLY in `SignalMap` + the adapter. Generator, reference model, scoreboard, coverage must never reference DUT signals directly.

## ToffeeCacheAdapter Responsibilities

Implemented in [src/cache_vip/toffee_adapter.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/toffee_adapter.py):

1. **reset** — hold reset asserted for N cycles, then deassert.
2. **drive_request(txn)** — translate `CacheTxn` → DUT `cpu_req_*` pins, honor valid/ready backpressure.
3. **sample_response()** — sample `cpu_resp_*`, build `CacheResponse` (data, hit/miss, eviction, writeback, error).
4. **memory-side hook** — if DUT exposes `mem_req_*`, delegate to `MemoryAgent`; drive `mem_resp_*` with fill data / writeback ack.
5. **timeout** — `response_timeout` (default 1000 cycles) guards hung handshakes.

## Memory Agent Contract

`ScriptedMemoryAgent` ([src/cache_vip/memory_agent.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/memory_agent.py)) is protocol-agnostic:

- Accepts `MemoryRequest` (read/write, addr, wdata, wmask).
- Returns `MemoryResponse` with configurable latency (fixed or per-request).
- Supports ready/backpressure patterns and `drain_to_idle()`.
- On real DUT, the adapter only needs to translate `mem_req_*` → `MemoryRequest` and `MemoryResponse` → `mem_resp_*`.

## Transaction Model

From [src/cache_vip/transactions.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/transactions.py):

`CacheTxn` fields: `op` (read/write), `addr` (byte), `size` (1/2/4/8), `data`, `mask`, `txn_id`, `uncached`.
`CacheResponse` fields: `data`, `hit`, `evicted`, `evicted_dirty`, `writeback_addr`, `writeback_data`, `error`, `txn_id`.

## NutShell cmd Encoding Note

NutShell Cache encodes the request opcode in `cpu_req_cmd` rather than a boolean `cpu_req_write`. When binding a real DUT:
- Set `cpu_req_cmd` in `signal_map_real.yaml`.
- In the adapter, decode/encode between `CacheOp` and the NutShell cmd value (read = cmd ScratchFetch/LD, write = cmd ST).
- If only a boolean `write` exists on a mock DUT, leave `cpu_req_cmd` as `null` and use `cpu_req_write`.

## Refactoring UCAgent Snippets

When integrating AI-generated code into Toffee:
1. Strip any hard-coded signal names; route through `SignalMap`.
2. Move transaction construction into `CacheTxn`/`CacheResponse` dataclasses.
3. Keep comparison logic in `Scoreboard`, not in the adapter.
4. Keep coverage sampling in `Coverage`, invoked via `Scoreboard.push_request`.
5. Add a directed unit test under `tests/` for each new adapter behavior.

## Smoke Sequence (after wiring)

```python
from cache_vip.toffee_adapter import ToffeeCacheAdapter, load_signal_map
from cache_vip.generator import CacheGenerator
from cache_vip.scoreboard import Scoreboard

dut = ...  # Picker-generated DUT object
smap = load_signal_map("configs/signal_map_real.yaml")
adapter = ToffeeCacheAdapter(dut, smap)
adapter.reset()

gen = CacheGenerator(seed=1)
sb = Scoreboard()
for txn in gen.random_stream(50):
    adapter.drive_request(txn)
    resp = adapter.sample_response()
    sb.observe_transaction(txn, resp)   # raises ScoreboardMismatch on bug
```

## Hand-off

Once the env drives and samples correctly through a smoke run, hand off to `cache-crv-designer` to expand stimulus and to `coverage-analysis` to confirm bins close.
