from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from cache_vip.real_dut_adapter import create_real_dut_adapter
from cache_vip.transactions import CacheOp, CacheTxn


async def main() -> None:
    adapter = await create_real_dut_adapter()
    txn = CacheTxn(op=CacheOp.READ, addr=0x1000, size=8, txn_id=1)
    print("drive:start", flush=True)
    await asyncio.wait_for(adapter.drive_cpu_request(txn), timeout=5)
    print("drive:done", flush=True)
    print("sample:start", flush=True)
    resp = await asyncio.wait_for(adapter.sample_cpu_response(), timeout=5)
    print(f"sample:done {resp}", flush=True)
    adapter.finish()


asyncio.run(main())
