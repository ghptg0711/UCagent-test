from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from cache_vip.real_dut_adapter import SIMPLEBUS_READ, create_real_dut_adapter


async def main() -> None:
    adapter = await create_real_dut_adapter()
    sm = adapter.signal_map
    dut = adapter.dut_wrapper

    await getattr(dut, sm.cpu_req_valid).write(1)
    await getattr(dut, sm.cpu_req_addr).write(0x1000)
    await getattr(dut, sm.cpu_req_cmd).write(SIMPLEBUS_READ)
    await getattr(dut, sm.cpu_req_size).write(3)
    await getattr(dut, sm.cpu_req_wdata).write(0)
    await getattr(dut, sm.cpu_req_wmask).write(0xFF)
    await getattr(dut, sm.cpu_req_user).write(0)
    await getattr(dut, sm.cpu_resp_ready).write(1)

    names = [
        sm.cpu_req_ready,
        sm.cpu_resp_valid,
        sm.cpu_resp_rdata,
        sm.mem_req_valid,
        sm.mem_req_addr,
        sm.mem_req_cmd,
        sm.mem_resp_ready,
        sm.mem_resp_valid,
        sm.mem_resp_cmd,
    ]
    for cycle in range(80):
        await adapter._service_external_bus()
        vals = []
        for name in names:
            vals.append(f"{name}={await getattr(dut, name).read()}")
        print(f"cycle {cycle}: " + " ".join(vals), flush=True)
        await dut.wait_cycles(1)
        if cycle == 2:
            await getattr(dut, sm.cpu_req_valid).write(0)
    adapter.finish()


asyncio.run(main())
