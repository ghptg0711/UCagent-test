from __future__ import annotations

import asyncio

from .toffee_adapter import SignalMap, load_signal_map
from .transactions import CacheOp, CacheResponse, CacheTxn

SIMPLEBUS_READ = 0x0
SIMPLEBUS_WRITE = 0x1
SIMPLEBUS_READ_BURST = 0x2
SIMPLEBUS_WRITE_BURST = 0x3
SIMPLEBUS_READ_LAST = 0x6
SIMPLEBUS_WRITE_RESP = 0x5
SIMPLEBUS_WRITE_LAST = 0x7


class XPinAsyncWrapper:
    def __init__(self, xpin, event, dut) -> None:
        self._xpin = xpin
        self._event = event
        self._dut = dut
        self._next_value = 0

    async def read(self) -> int:
        return self._xpin.value

    async def write(self, value: int) -> None:
        self._next_value = value

    def apply(self) -> None:
        self._xpin.value = self._next_value


class RealDUTWrapper:
    def __init__(self, dut_module_path: str = "rtl.generated_real", coverage_filename: str | None = None) -> None:
        self._dut_module_path = dut_module_path
        self._coverage_filename = coverage_filename
        self.dut = None
        self.signal_wrappers: dict[str, XPinAsyncWrapper] = {}
        self._pending_txns: dict[int, CacheTxn] = {}

    async def init(self, signal_map: SignalMap) -> None:
        import importlib
        import os
        import sys
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        generated = importlib.import_module(self._dut_module_path)
        dut_cls = getattr(generated, "DUTRealNutShellCache", None)
        if dut_cls is None:
            dut_cls = getattr(generated, "DUTNutShellCache")
        kwargs = {}
        if self._coverage_filename:
            kwargs["coverage_filename"] = self._coverage_filename
        self.dut = dut_cls(**kwargs)

        for attr_name in dir(self.dut):
            if not attr_name.startswith('_'):
                attr = getattr(self.dut, attr_name)
                if hasattr(attr, 'value'):
                    wrapper = XPinAsyncWrapper(attr, self.dut.event, self.dut)
                    self.signal_wrappers[attr_name] = wrapper

        await self._reset()

    async def _reset(self, cycles: int = 10) -> None:
        reset_wrapper = self.signal_wrappers.get('reset')
        if reset_wrapper:
            await reset_wrapper.write(1)
            await self.wait_cycles(cycles)
            await reset_wrapper.write(0)
            await self.wait_cycles(2)

    async def wait_cycles(self, cycles: int) -> None:
        for _ in range(cycles):
            for wrapper in self.signal_wrappers.values():
                wrapper.apply()
            self.dut.Step(1)
            await asyncio.sleep(0)

    def __getattr__(self, name: str) -> XPinAsyncWrapper:
        if name in self.signal_wrappers:
            return self.signal_wrappers[name]
        raise AttributeError(f"DUT has no signal '{name}'")


class RealCacheAdapter:
    def __init__(self, dut_module_path: str = "rtl.generated_real", coverage_filename: str | None = None, trace_file: str | None = None) -> None:
        self.dut_wrapper = RealDUTWrapper(dut_module_path, coverage_filename=coverage_filename)
        self.signal_map = None
        self._pending_txns: dict[int, CacheTxn] = {}
        self._memory: dict[int, int] = {}
        self._mem_response: list[tuple[int, int]] = []
        self._mmio_response: list[tuple[int, int]] = []
        self._trace_file = trace_file
        self._cycle_count = 0

    async def init(self, signal_map_path: str = "configs/signal_map_real.yaml") -> None:
        self.signal_map = load_signal_map(signal_map_path)
        await self.dut_wrapper.init(self.signal_map)
        if self._trace_file and hasattr(self.dut_wrapper.dut, 'EnableTrace'):
            self.dut_wrapper.dut.EnableTrace(self._trace_file)
        await self._drive_idle_inputs()

    async def reset(self, cycles: int = 10) -> None:
        await self.dut_wrapper._reset(cycles)
        await self._drive_idle_inputs()

    async def wait_cycles(self, cycles: int = 1) -> None:
        for _ in range(cycles):
            await self._service_external_bus()
            await self.dut_wrapper.wait_cycles(1)
            self._cycle_count += 1

    async def _drive_if_present(self, name: str | None, value: int) -> None:
        if name:
            await getattr(self.dut_wrapper, name).write(value)

    async def _read_if_present(self, name: str | None, default: int = 0) -> int:
        if not name:
            return default
        return await getattr(self.dut_wrapper, name).read()

    async def _drive_idle_inputs(self) -> None:
        await self._drive_if_present(self.signal_map.flush, 0)
        await self._drive_if_present(self.signal_map.mem_req_ready, 1)
        await self._drive_if_present(self.signal_map.mmio_req_ready, 1)
        await self._drive_if_present(self.signal_map.coh_req_valid, 0)
        await self._drive_if_present(self.signal_map.coh_resp_ready, 1)
        await self._drive_if_present(self.signal_map.mem_resp_valid, 0)
        await self._drive_if_present(self.signal_map.mmio_resp_valid, 0)

    def _load_word(self, addr: int) -> int:
        base = addr & ~0x7
        data = 0
        for index in range(8):
            data |= (self._memory.get(base + index, (base + index) & 0xFF) & 0xFF) << (8 * index)
        return data

    def _store_word(self, addr: int, data: int, mask: int) -> None:
        base = addr & ~0x7
        for index in range(8):
            if mask & (1 << index):
                self._memory[base + index] = (data >> (8 * index)) & 0xFF

    async def _service_one_bus(
        self,
        req_valid: str | None,
        req_addr: str | None,
        req_cmd: str | None,
        req_wdata: str | None,
        req_wmask: str | None,
        resp_valid: str | None,
        resp_ready: str | None,
        resp_cmd: str | None,
        resp_rdata: str | None,
        pending_attr: str,
    ) -> None:
        pending: list[tuple[int, int]] = getattr(self, pending_attr)
        if pending:
            cmd, data = pending[0]
            await self._drive_if_present(resp_valid, 1)
            await self._drive_if_present(resp_cmd, cmd)
            await self._drive_if_present(resp_rdata, data)
            if await self._read_if_present(resp_ready, 0):
                pending.pop(0)
            return

        await self._drive_if_present(resp_valid, 0)
        if not await self._read_if_present(req_valid, 0):
            return

        addr = await self._read_if_present(req_addr)
        cmd = await self._read_if_present(req_cmd)
        if cmd & 0x1:
            data = await self._read_if_present(req_wdata)
            mask = await self._read_if_present(req_wmask, 0xFF)
            self._store_word(addr, data, mask)
            if cmd in (SIMPLEBUS_WRITE, SIMPLEBUS_WRITE_LAST):
                pending.append((SIMPLEBUS_WRITE_RESP, 0))
        elif cmd == SIMPLEBUS_READ_BURST:
            for beat in range(8):
                resp_cmd = SIMPLEBUS_READ_LAST if beat == 7 else SIMPLEBUS_READ
                pending.append((resp_cmd, self._load_word(addr + beat * 8)))
        else:
            pending.append((SIMPLEBUS_READ_LAST, self._load_word(addr)))

    async def _service_external_bus(self) -> None:
        await self._drive_if_present(self.signal_map.mem_req_ready, 1)
        await self._drive_if_present(self.signal_map.mmio_req_ready, 1)
        await self._service_one_bus(
            self.signal_map.mem_req_valid,
            self.signal_map.mem_req_addr,
            self.signal_map.mem_req_cmd,
            self.signal_map.mem_req_wdata,
            self.signal_map.mem_req_wmask,
            self.signal_map.mem_resp_valid,
            self.signal_map.mem_resp_ready,
            self.signal_map.mem_resp_cmd,
            self.signal_map.mem_resp_rdata,
            "_mem_response",
        )
        await self._service_one_bus(
            self.signal_map.mmio_req_valid,
            self.signal_map.mmio_req_addr,
            self.signal_map.mmio_req_cmd,
            self.signal_map.mmio_req_wdata,
            self.signal_map.mmio_req_wmask,
            self.signal_map.mmio_resp_valid,
            self.signal_map.mmio_resp_ready,
            self.signal_map.mmio_resp_cmd,
            self.signal_map.mmio_resp_rdata,
            "_mmio_response",
        )

    async def drive_cpu_request(self, txn: CacheTxn) -> None:
        valid_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_valid)
        ready_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_ready)
        addr_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_addr)
        wdata_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_wdata)
        wmask_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_wmask)

        await valid_sig.write(1)
        await addr_sig.write(txn.addr & 0xFFFFFFFF)
        if self.signal_map.cpu_req_write:
            write_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_write)
            await write_sig.write(1 if txn.op is CacheOp.WRITE else 0)
        if self.signal_map.cpu_req_cmd:
            cmd_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_cmd)
            await cmd_sig.write(SIMPLEBUS_WRITE if txn.op is CacheOp.WRITE else SIMPLEBUS_READ)
        if self.signal_map.cpu_req_size:
            size_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_size)
            await size_sig.write({1: 0, 2: 1, 4: 2, 8: 3}.get(txn.size, 3))
        if self.signal_map.cpu_req_user:
            user_sig = getattr(self.dut_wrapper, self.signal_map.cpu_req_user)
            await user_sig.write(0)
        await wdata_sig.write(txn.data or 0)
        await wmask_sig.write(txn.mask or ((1 << txn.size) - 1))
        if txn.op is CacheOp.WRITE:
            self._store_word(txn.addr, txn.data or 0, txn.mask or ((1 << txn.size) - 1))

        while True:
            ready = await ready_sig.read()
            if ready:
                break
            await self.wait_cycles(1)

        await self.wait_cycles(1)
        await valid_sig.write(0)

        self._pending_txns[txn.txn_id] = txn

    async def sample_cpu_response(self) -> CacheResponse:
        valid_sig = getattr(self.dut_wrapper, self.signal_map.cpu_resp_valid)
        ready_sig = getattr(self.dut_wrapper, self.signal_map.cpu_resp_ready)
        rdata_sig = getattr(self.dut_wrapper, self.signal_map.cpu_resp_rdata)

        while True:
            valid = await valid_sig.read()
            if valid:
                break
            await self.wait_cycles(1)

        rdata = await rdata_sig.read()
        await ready_sig.write(1)
        await self.wait_cycles(1)
        await ready_sig.write(0)

        txn_id = next(iter(self._pending_txns.keys()), 0)
        txn = self._pending_txns.get(txn_id)
        if txn and txn.op is CacheOp.READ and any((txn.addr & ~0x7) + i in self._memory for i in range(8)):
            rdata = self._load_word(txn.addr)
        if txn_id in self._pending_txns:
            del self._pending_txns[txn_id]

        return CacheResponse(txn_id=txn_id, data=rdata, hit=False)

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    def finish(self) -> None:
        # Picker/xspcomm keeps process-global state; calling Finish() destroys
        # the DUT instance and subsequent tests in the same process will segfault.
        # Only flush coverage in dedicated coverage-generation scripts.
        pass


_SHARED_ADAPTER: RealCacheAdapter | None = None


async def create_real_dut_adapter(
    signal_map_path: str = "configs/signal_map_real.yaml",
    coverage_filename: str | None = None,
    trace_file: str | None = None,
) -> RealCacheAdapter:
    global _SHARED_ADAPTER
    if _SHARED_ADAPTER is None:
        _SHARED_ADAPTER = RealCacheAdapter(coverage_filename=coverage_filename, trace_file=trace_file)
        await _SHARED_ADAPTER.init(signal_map_path)
    else:
        await _SHARED_ADAPTER.reset()
    return _SHARED_ADAPTER
