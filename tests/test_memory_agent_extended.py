from types import SimpleNamespace

import pytest

from cache_vip.memory_agent import (
    MemoryRequest,
    MemoryResponse,
    ScriptedMemoryAgent,
    ToffeeMemoryAgent,
)


class FakeSignal:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    async def read(self) -> int:
        return self.value

    async def write(self, value: int) -> None:
        self.value = value


class FakeDUT:
    def __init__(self) -> None:
        self.cycles = 0
        self.req_valid = FakeSignal(1)
        self.req_ready = FakeSignal(0)
        self.req_addr = FakeSignal(0x100)
        self.req_write = FakeSignal(0)
        self.req_data = FakeSignal(0xAABB)
        self.req_mask = FakeSignal(0x3)
        self.resp_valid = FakeSignal(0)
        self.resp_ready = FakeSignal(1)
        self.resp_data = FakeSignal(0)

    async def wait_cycles(self, cycles: int) -> None:
        self.cycles += cycles


def _signal_map():
    return SimpleNamespace(
        mem_req_valid="req_valid",
        mem_req_ready="req_ready",
        mem_req_addr="req_addr",
        mem_req_write="req_write",
        mem_req_wdata="req_data",
        mem_req_wmask="req_mask",
        mem_resp_valid="resp_valid",
        mem_resp_ready="resp_ready",
        mem_resp_rdata="resp_data",
    )


def test_scripted_memory_agent_rejects_invalid_configuration_and_latency() -> None:
    with pytest.raises(ValueError, match="default_latency"):
        ScriptedMemoryAgent(default_latency=-1)
    with pytest.raises(ValueError, match="ready cycle"):
        ScriptedMemoryAgent(backpressure_pattern=[False, False])

    agent = ScriptedMemoryAgent()
    with pytest.raises(ValueError, match="latency"):
        agent.accept(MemoryRequest(0, 1), latency=-1)


def test_scripted_memory_agent_timeout_and_default_write_mask() -> None:
    agent = ScriptedMemoryAgent(default_latency=100)
    assert agent.accept(MemoryRequest(0x20, 2, write=True, data=0xBEEF, txn_id=1))
    assert agent.memory.read(0x20, 2) == 0xBEEF
    with pytest.raises(TimeoutError, match="did not drain"):
        agent.run_until_idle(max_cycles=1)


@pytest.mark.asyncio
async def test_toffee_memory_agent_monitors_request_and_absence() -> None:
    dut = FakeDUT()
    agent = ToffeeMemoryAgent(dut, _signal_map(), line_bytes=8)

    request = await agent.monitor_memory_request()

    assert request == MemoryRequest(0x100, 8, write=False, data=0xAABB, mask=0x3)
    assert dut.req_ready.value == 1
    assert dut.cycles == 1

    dut.req_valid.value = 0
    assert await agent.monitor_memory_request() is None
    agent.signal_map.mem_req_valid = None
    assert await agent.monitor_memory_request() is None


@pytest.mark.asyncio
async def test_toffee_memory_agent_drives_response_and_fill() -> None:
    dut = FakeDUT()
    agent = ToffeeMemoryAgent(dut, _signal_map(), default_latency=2, line_bytes=8)
    agent.inner.memory.write(0x80, 8, 0x1122334455667788, 0xFF)

    line = await agent.handle_fill(0x80)

    assert line == bytes.fromhex("8877665544332211")
    assert dut.resp_data.value == 0x1122334455667788
    assert dut.resp_valid.value == 0
    assert dut.cycles == 3

    agent.signal_map.mem_resp_valid = None
    await agent.drive_memory_response(MemoryResponse(0, data=1))


@pytest.mark.asyncio
async def test_toffee_memory_agent_writeback_and_serve_one() -> None:
    dut = FakeDUT()
    dut.req_write.value = 1
    agent = ToffeeMemoryAgent(dut, _signal_map(), line_bytes=8)

    request = await agent.serve_one()

    assert request is not None and request.write
    assert agent.writeback_log == [(0x100, bytes.fromhex("bbaa000000000000"))]
    assert agent.inner.memory.read(0x100, 2) == 0xAABB

    dut.req_valid.value = 0
    assert await agent.serve_one() is None
