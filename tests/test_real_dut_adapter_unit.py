from types import SimpleNamespace

import pytest

from cache_vip.real_dut_adapter import (
    SIMPLEBUS_READ_BURST,
    SIMPLEBUS_WRITE,
    RealCacheAdapter,
    XPinAsyncWrapper,
)
from cache_vip.transactions import CacheOp, CacheTxn


class FakeSignal:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    async def read(self) -> int:
        return self.value

    async def write(self, value: int) -> None:
        self.value = value


class FakeDUT:
    def __init__(self) -> None:
        self.steps = 0
        self.finished = False

    def Step(self, cycles: int) -> None:
        self.steps += cycles

    def Finish(self) -> None:
        self.finished = True

@pytest.mark.asyncio
async def test_real_adapter_preserves_dut_read_data(monkeypatch) -> None:
    adapter = RealCacheAdapter()
    adapter.signal_map = SimpleNamespace(
        cpu_resp_valid="resp_valid",
        cpu_resp_ready="resp_ready",
        cpu_resp_rdata="resp_data",
    )
    adapter.dut_wrapper.signal_wrappers = {
        "resp_valid": FakeSignal(1),
        "resp_ready": FakeSignal(0),
        "resp_data": FakeSignal(0x0123456789ABCDEF),
    }
    txn = CacheTxn(CacheOp.READ, addr=0x1000, size=8, txn_id=7)
    adapter._pending_txns[txn.txn_id] = txn
    adapter._txn_event_start[txn.txn_id] = 0
    adapter._bus_events.append(
        {"bus": "mem", "cycle": 1, "addr": txn.addr, "cmd": 0, "data": 0, "mask": 0}
    )
    adapter._store_word(txn.addr, 0xDEADBEEFDEADBEEF, 0xFF)

    async def no_wait(_cycles: int = 1) -> None:
        return None

    monkeypatch.setattr(adapter, "wait_cycles", no_wait)

    response = await adapter.sample_cpu_response()

    assert response.txn_id == 7
    assert response.data == 0x0123456789ABCDEF
    assert response.hit is False
    assert response.evicted_dirty is False
    assert response.observed_fields == frozenset(
        {"txn_id", "data", "hit", "evicted_dirty", "writeback_addr"}
    )


@pytest.mark.asyncio
async def test_xpin_wrapper_stages_then_applies_value() -> None:
    signal = FakeSignal(3)
    wrapper = XPinAsyncWrapper(signal, event=None, dut=None)

    assert await wrapper.read() == 3
    await wrapper.write(9)
    assert signal.value == 3
    wrapper.apply()
    assert signal.value == 9


@pytest.mark.asyncio
async def test_real_adapter_reset_clears_transaction_and_memory_state(monkeypatch) -> None:
    adapter = RealCacheAdapter()
    adapter._memory[0] = 1
    adapter._pending_txns[1] = CacheTxn(CacheOp.READ, 0, 8, txn_id=1)
    adapter._mem_response.append((0, 0))
    adapter._mmio_response.append((0, 0))
    adapter._cycle_count = 99
    calls: list[str] = []

    async def fake_reset(_cycles: int) -> None:
        calls.append("reset")

    async def fake_idle() -> None:
        calls.append("idle")

    monkeypatch.setattr(adapter.dut_wrapper, "_reset", fake_reset)
    monkeypatch.setattr(adapter, "_drive_idle_inputs", fake_idle)

    await adapter.reset(clear_memory=True)

    assert calls == ["reset", "idle"]
    assert adapter._memory == {}
    assert adapter._pending_txns == {}
    assert adapter._mem_response == []
    assert adapter._mmio_response == []
    assert adapter.cycle_count == 0


def _install_bus_signals(adapter: RealCacheAdapter, *, cmd: int) -> None:
    adapter.dut_wrapper.signal_wrappers = {
        "req_valid": FakeSignal(1),
        "req_addr": FakeSignal(0x40),
        "req_cmd": FakeSignal(cmd),
        "req_data": FakeSignal(0x1122334455667788),
        "req_mask": FakeSignal(0xFF),
        "resp_valid": FakeSignal(0),
        "resp_ready": FakeSignal(1),
        "resp_cmd": FakeSignal(0),
        "resp_data": FakeSignal(0),
    }


async def _service_test_bus(adapter: RealCacheAdapter) -> None:
    await adapter._service_one_bus(
        "req_valid",
        "req_addr",
        "req_cmd",
        "req_data",
        "req_mask",
        "resp_valid",
        "resp_ready",
        "resp_cmd",
        "resp_data",
        "_mem_response",
        "mem",
    )


@pytest.mark.asyncio
async def test_real_adapter_services_write_and_response() -> None:
    adapter = RealCacheAdapter()
    _install_bus_signals(adapter, cmd=SIMPLEBUS_WRITE)

    await _service_test_bus(adapter)

    assert adapter._load_word(0x40) == 0x1122334455667788
    assert adapter._mem_response
    assert adapter.bus_events[-1]["addr"] == 0x40

    await _service_test_bus(adapter)
    assert adapter._mem_response == []
    assert adapter.dut_wrapper.signal_wrappers["resp_valid"].value == 1


@pytest.mark.asyncio
async def test_real_adapter_services_read_burst() -> None:
    adapter = RealCacheAdapter()
    _install_bus_signals(adapter, cmd=SIMPLEBUS_READ_BURST)
    for beat in range(8):
        adapter._store_word(0x40 + beat * 8, beat + 1, 0xFF)

    await _service_test_bus(adapter)

    assert len(adapter._mem_response) == 8
    assert adapter._mem_response[0][1] == 1
    assert adapter._mem_response[-1][1] == 8


@pytest.mark.asyncio
async def test_real_adapter_drives_cpu_request(monkeypatch) -> None:
    adapter = RealCacheAdapter()
    adapter.signal_map = SimpleNamespace(
        cpu_req_valid="valid",
        cpu_req_ready="ready",
        cpu_req_addr="addr",
        cpu_req_write="write",
        cpu_req_cmd="cmd",
        cpu_req_size="size",
        cpu_req_user="user",
        cpu_req_wdata="data",
        cpu_req_wmask="mask",
    )
    adapter.dut_wrapper.signal_wrappers = {
        name: FakeSignal(1 if name == "ready" else 0)
        for name in ("valid", "ready", "addr", "write", "cmd", "size", "user", "data", "mask")
    }

    async def no_wait(_cycles: int = 1) -> None:
        return None

    monkeypatch.setattr(adapter, "wait_cycles", no_wait)
    txn = CacheTxn(CacheOp.WRITE, 0x1234, 4, data=0xAABBCCDD, mask=0xF, txn_id=11)

    await adapter.drive_cpu_request(txn)

    signals = adapter.dut_wrapper.signal_wrappers
    assert signals["valid"].value == 0
    assert signals["addr"].value == 0x1234
    assert signals["write"].value == 1
    assert signals["data"].value == 0xAABBCCDD
    assert adapter._pending_txns[11] == txn


def test_real_adapter_finish_releases_shared_dut() -> None:
    adapter = RealCacheAdapter()
    dut = FakeDUT()
    adapter.dut_wrapper.dut = dut

    adapter.finish()

    assert dut.finished is True
    assert adapter.dut_wrapper.dut is None
