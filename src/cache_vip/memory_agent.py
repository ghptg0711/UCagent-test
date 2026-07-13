from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .reference_model import ByteMemory


@dataclass(frozen=True)
class MemoryRequest:
    addr: int
    size: int
    write: bool = False
    data: int = 0
    mask: int | None = None
    txn_id: int = 0


@dataclass(frozen=True)
class MemoryResponse:
    txn_id: int
    data: int = 0
    ready_cycle: int = 0


class ScriptedMemoryAgent:
    """Protocol-independent memory model for DUT adapter tests.

    The Toffee layer can translate concrete memory-side DUT signals into
    MemoryRequest objects and use this agent to model latency, writes, and
    backpressure without changing the cache reference model.
    """

    def __init__(
        self,
        memory: ByteMemory | None = None,
        *,
        default_latency: int = 1,
        backpressure_pattern: list[bool] | None = None,
    ) -> None:
        if default_latency < 0:
            raise ValueError("default_latency must be non-negative")
        self.memory = memory or ByteMemory()
        self.default_latency = default_latency
        self.backpressure_pattern = backpressure_pattern or [True]
        if not any(self.backpressure_pattern):
            raise ValueError("backpressure_pattern must allow at least one ready cycle")
        self.cycle = 0
        self._pending: deque[MemoryResponse] = deque()

    def ready(self) -> bool:
        return self.backpressure_pattern[self.cycle % len(self.backpressure_pattern)]

    def accept(self, request: MemoryRequest, *, latency: int | None = None) -> bool:
        if not self.ready():
            return False
        response_latency = self.default_latency if latency is None else latency
        if response_latency < 0:
            raise ValueError("latency must be non-negative")

        if request.write:
            self.memory.write(
                request.addr, request.size, request.data, request.mask or ((1 << request.size) - 1)
            )
            data = 0
        else:
            data = self.memory.read(request.addr, request.size)
        self._pending.append(
            MemoryResponse(request.txn_id, data=data, ready_cycle=self.cycle + response_latency)
        )
        return True

    def tick(self) -> list[MemoryResponse]:
        ready: list[MemoryResponse] = []
        while self._pending and self._pending[0].ready_cycle <= self.cycle:
            ready.append(self._pending.popleft())
        self.cycle += 1
        return ready

    def run_until_idle(self, max_cycles: int = 10_000) -> list[MemoryResponse]:
        responses: list[MemoryResponse] = []
        for _ in range(max_cycles):
            responses.extend(self.tick())
            if not self._pending:
                return responses
        raise TimeoutError("memory agent did not drain before max_cycles")


class ToffeeMemoryAgent:
    """Toffee-bound memory agent that drives/samples memory-side DUT signals.

    Translates between the protocol-independent ScriptedMemoryAgent and
    concrete DUT memory-side signals. Handles miss fill, dirty writeback,
    configurable latency, and backpressure.
    """

    def __init__(
        self,
        dut: object,
        signal_map: object,
        *,
        memory: ByteMemory | None = None,
        default_latency: int = 2,
        backpressure_pattern: list[bool] | None = None,
        line_bytes: int = 64,
    ) -> None:
        self.dut = dut
        self.signal_map = signal_map
        self.line_bytes = line_bytes
        self.inner = ScriptedMemoryAgent(
            memory,
            default_latency=default_latency,
            backpressure_pattern=backpressure_pattern,
        )
        self._writeback_log: list[tuple[int, bytes]] = []

    async def monitor_memory_request(self) -> MemoryRequest | None:
        """Monitor memory request signals from the DUT (DUT -> Memory).

        Returns a MemoryRequest if valid, or None if no request is pending.
        """
        mem_req_valid_name = getattr(self.signal_map, "mem_req_valid", None)
        if mem_req_valid_name is None:
            return None

        valid_sig = getattr(self.dut, mem_req_valid_name)
        ready_sig = getattr(self.dut, self.signal_map.mem_req_ready)
        valid = await valid_sig.read()
        if not valid:
            return None

        addr_sig = getattr(self.dut, self.signal_map.mem_req_addr)
        write_sig = getattr(self.dut, self.signal_map.mem_req_write)
        wdata_sig = getattr(self.dut, self.signal_map.mem_req_wdata)
        wmask_sig = getattr(self.dut, self.signal_map.mem_req_wmask)

        addr = await addr_sig.read()
        write = await write_sig.read()
        data = await wdata_sig.read()
        mask = await wmask_sig.read()

        await ready_sig.write(1)
        await self.dut.wait_cycles(1)

        return MemoryRequest(
            addr=addr, size=self.line_bytes, write=bool(write), data=data, mask=mask
        )

    async def drive_memory_response(self, response: MemoryResponse) -> None:
        """Drive memory response signals to the DUT (Memory -> DUT).

        Follows valid/ready handshake protocol with configurable latency.
        """
        mem_resp_valid_name = getattr(self.signal_map, "mem_resp_valid", None)
        if mem_resp_valid_name is None:
            return

        valid_sig = getattr(self.dut, mem_resp_valid_name)
        rdata_sig = getattr(self.dut, self.signal_map.mem_resp_rdata)
        ready_sig = getattr(self.dut, self.signal_map.mem_resp_ready)

        await rdata_sig.write(response.data)
        await valid_sig.write(1)

        for _ in range(self.inner.default_latency):
            await self.dut.wait_cycles(1)

        while True:
            ready = await ready_sig.read()
            if ready:
                break
            await self.dut.wait_cycles(1)

        await self.dut.wait_cycles(1)
        await valid_sig.write(0)

    async def handle_fill(self, addr: int) -> bytes:
        """Handle a read miss: return line fill data from backing memory.

        Reads a full cache line from the agent's backing memory at the
        given address and drives it as a memory response.
        """
        line_bytes = self.line_bytes
        data = self.inner.memory.read(addr, line_bytes)
        response = MemoryResponse(txn_id=0, data=data)
        await self.drive_memory_response(response)
        line_data = bytearray(line_bytes)
        for i in range(line_bytes):
            line_data[i] = (data >> (8 * i)) & 0xFF
        return bytes(line_data)

    async def handle_writeback(self, addr: int, data: bytes) -> None:
        """Handle a dirty writeback: write data back to backing memory.

        Records the writeback in the log for later verification.
        """
        for i, byte in enumerate(data):
            self.inner.memory.write_byte(addr + i, byte)
        self._writeback_log.append((addr, data))

    @property
    def writeback_log(self) -> list[tuple[int, bytes]]:
        """Return the log of all writeback operations."""
        return list(self._writeback_log)

    async def serve_one(self) -> MemoryRequest | None:
        """Serve one memory request cycle: monitor, process, respond.

        This is the main loop body for the memory agent. It checks for
        pending DUT memory requests and handles them (fill or writeback).
        """
        request = await self.monitor_memory_request()
        if request is None:
            return None

        if request.write:
            line_bytes = self.line_bytes
            line_data = bytearray(line_bytes)
            for i in range(line_bytes):
                if request.mask and request.mask & (1 << i):
                    line_data[i] = (request.data >> (8 * i)) & 0xFF
            await self.handle_writeback(request.addr, bytes(line_data))
        else:
            await self.handle_fill(request.addr)

        return request
