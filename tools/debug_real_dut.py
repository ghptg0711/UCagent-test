from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "src")

from cache_vip.real_dut_adapter import create_real_dut_adapter


async def main() -> None:
    print("create:start", flush=True)
    adapter = await create_real_dut_adapter()
    print("create:done", flush=True)
    print("reset:start", flush=True)
    await adapter.reset(2)
    print("reset:done", flush=True)
    adapter.finish()
    print("finish:done", flush=True)


asyncio.run(main())
